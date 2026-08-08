from __future__ import annotations

import hashlib
import io
import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import Request
from sqlalchemy import select, text

from hospital_ai.db.clinical_documents import DocumentUpload, IdempotencyRecord
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import Document, User


def _request() -> Request:
    return Request(
        {"type": "http", "client": ("127.0.0.1", 8000), "method": "POST", "path": "/api/v1/documents/upload-sessions"}
    )


def _upload_request(body: bytes) -> Request:
    async def receive() -> dict:
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(
        {
            "type": "http",
            "client": ("127.0.0.1", 8000),
            "method": "PUT",
            "path": "/api/v1/documents/upload-objects",
            "headers": [(b"if-none-match", b"*"), (b"content-type", b"application/pdf")],
        },
        receive,
    )


@pytest.mark.asyncio
async def test_create_upload_session_idempotency_replay(session_and_settings, monkeypatch: pytest.MonkeyPatch) -> None:
    session, settings = session_and_settings
    from hospital_ai.api.routes import document_uploads as upload_routes
    from hospital_ai.schemas.document_uploads import UploadSessionCreate

    await session.execute(text("PRAGMA foreign_keys = ON"))

    doctor = await session.get(User, DOCTOR_ID)
    if not doctor:
        doctor = User(
            id=uuid.uuid4(), email="doc@test.com", password_hash="hash", full_name="Doc", role="doctor", is_active=True
        )
        session.add(doctor)
        await session.commit()

    payload = UploadSessionCreate(
        patient_id=PATIENT_ALICE_ID,
        filename="report.pdf",
        title="Synthetic report",
        document_type="scan",
        expected_size=1024,
        expected_sha256="b" * 64,
        claimed_mime_type="application/pdf",
    )

    res1 = await upload_routes.create_upload_session(
        payload=payload,
        request=_request(),
        idempotency_key="idemp-test-1",
        session=session,
        current_user=doctor,
    )

    res2 = await upload_routes.create_upload_session(
        payload=payload,
        request=_request(),
        idempotency_key="idemp-test-1",
        session=session,
        current_user=doctor,
    )

    assert res1.upload_id == res2.upload_id
    assert res1.object_key == res2.object_key
    document = await session.get(Document, res1.document_id)
    assert document is not None
    assert document.title == "Synthetic report"
    assert document.document_type == "scan"


@pytest.mark.asyncio
async def test_upload_service_scanner_requires_explicit_local_opt_in(
    session_and_settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    session, settings = session_and_settings
    from hospital_ai.core import config
    from hospital_ai.services.upload_sessions import (
        SyntheticCleanMalwareScanner,
        UnavailableMalwareScanner,
        UploadSessionService,
    )

    monkeypatch.setattr(config, "get_settings", lambda: settings)

    disabled = UploadSessionService.from_request(session, _request())
    assert isinstance(disabled.scanner, UnavailableMalwareScanner)

    settings.allow_synthetic_malware_scan = True
    enabled = UploadSessionService.from_request(session, _request())
    assert isinstance(enabled.scanner, SyntheticCleanMalwareScanner)

    settings.environment = "staging"
    staging = UploadSessionService.from_request(session, _request())
    assert isinstance(staging.scanner, UnavailableMalwareScanner)


@pytest.mark.asyncio
async def test_finalize_upload_session(session_and_settings, monkeypatch: pytest.MonkeyPatch) -> None:
    session, settings = session_and_settings
    settings.worker_inline = True
    from hospital_ai.api.routes import document_uploads as upload_routes
    from hospital_ai.schemas.document_uploads import UploadSessionCreate
    from hospital_ai.services.storage import StorageObjectHead

    doctor = await session.get(User, DOCTOR_ID)
    if not doctor:
        doctor = User(
            id=uuid.uuid4(),
            email="doc2@test.com",
            password_hash="hash",
            full_name="Doc2",
            role="doctor",
            is_active=True,
        )
        session.add(doctor)
        await session.commit()

    content = b"%PDF-1.4\n"
    payload = UploadSessionCreate(
        patient_id=PATIENT_ALICE_ID,
        filename="report.pdf",
        expected_size=len(content),
        expected_sha256=hashlib.sha256(content).hexdigest(),
        claimed_mime_type="application/pdf",
    )

    created = await upload_routes.create_upload_session(
        payload=payload,
        request=_request(),
        idempotency_key="idemp-test-2",
        session=session,
        current_user=doctor,
    )
    created2 = await upload_routes.create_upload_session(
        payload=payload,
        request=_request(),
        idempotency_key="idemp-test-3",
        session=session,
        current_user=doctor,
    )

    # Mock storage methods on whatever service is resolved so finalize passes validation
    from hospital_ai.services import upload_sessions as us_module

    original_from_request = us_module.UploadSessionService.from_request

    def mocked_from_request(sess, req):
        service = original_from_request(sess, req)
        service.storage = type(
            "MockStorage",
            (),
            {
                "head_object": lambda *args: StorageObjectHead(args[-1], len(content), '"etag"', "application/pdf"),
                "read_stream": lambda *args: io.BytesIO(content),
            },
        )()
        from hospital_ai.services.upload_sessions import StorageContentReader

        service.content_reader = StorageContentReader(service.storage)
        service.scanner = _CleanScanner()
        return service

    monkeypatch.setattr(us_module.UploadSessionService, "from_request", mocked_from_request)
    process_document = AsyncMock()
    monkeypatch.setattr("hospital_ai.workers.jobs.process_document", process_document)
    monkeypatch.setattr("hospital_ai.workers.queue.enqueue_document_indexing", lambda *args, **kwargs: None)

    res = await upload_routes.finalize_upload_session(
        document_id=created.document_id,
        upload_id=created.upload_id,
        request=_request(),
        idempotency_key="finalize-1",
        session=session,
        current_user=doctor,
    )
    assert res.state == "finalized"
    process_document.assert_awaited_once()

    replay = await upload_routes.finalize_upload_session(
        document_id=created.document_id,
        upload_id=created.upload_id,
        request=_request(),
        idempotency_key="finalize-1",
        session=session,
        current_user=doctor,
    )
    assert replay.id == res.id
    record = await session.scalar(select(IdempotencyRecord).where(IdempotencyRecord.scope.like("%finalize%")))
    assert record is not None
    assert record.state == "completed"

    from hospital_ai.core.errors import ConflictError

    with pytest.raises(ConflictError):
        await upload_routes.finalize_upload_session(
            document_id=created2.document_id,
            upload_id=created2.upload_id,
            request=_request(),
            idempotency_key="finalize-1",
            session=session,
            current_user=doctor,
        )


@pytest.mark.asyncio
async def test_local_upload_object_is_bound_and_immutable(session_and_settings) -> None:
    session, settings = session_and_settings
    from hospital_ai.api.routes import document_uploads as upload_routes

    doctor = await session.get(User, DOCTOR_ID)
    content = b"%PDF-1.7\nsynthetic"
    document_id = uuid.uuid4()
    upload_id = uuid.uuid4()
    object_key = f"source/{PATIENT_ALICE_ID}/{document_id}/{upload_id}/original.pdf"
    session.add(
        Document(
            id=document_id,
            patient_id=PATIENT_ALICE_ID,
            uploaded_by=DOCTOR_ID,
            title="Local upload",
            document_type="clinical_note",
            storage_uri="pending",
            mime_type="application/pdf",
            status="uploaded",
        )
    )
    session.add(
        DocumentUpload(
            id=upload_id,
            document_id=document_id,
            state="pending_upload",
            object_key=object_key,
            expected_sha256="a" * 64,
            byte_size=len(content),
            mime_type="application/pdf",
            actor_user_id=DOCTOR_ID,
        )
    )
    await session.commit()

    response = await upload_routes.put_local_upload_object(
        object_key=object_key,
        request=_upload_request(content),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    assert response.status_code == 204
    assert (settings.storage_root / object_key).read_bytes() == content

    from hospital_ai.core.errors import ConflictError

    with pytest.raises(ConflictError, match="already exists"):
        await upload_routes.put_local_upload_object(
            object_key=object_key,
            request=_upload_request(content),
            session=session,
            current_user=doctor,
            settings=settings,
        )


@pytest.mark.asyncio
async def test_finalize_upload_session_failure_releases_idempotency_key(
    session_and_settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    session, _ = session_and_settings
    import hashlib
    import io

    from hospital_ai.api.routes import document_uploads as upload_routes
    from hospital_ai.core.errors import ValidationAppError
    from hospital_ai.schemas.document_uploads import UploadSessionCreate
    from hospital_ai.services.storage import StorageObjectHead

    doctor = await session.get(User, DOCTOR_ID)
    if not doctor:
        doctor = User(
            id=uuid.uuid4(),
            email="doc3@test.com",
            password_hash="hash",
            full_name="Doc3",
            role="doctor",
            is_active=True,
        )
        session.add(doctor)
        await session.commit()

    content = b"%PDF-1.4\n"
    payload = UploadSessionCreate(
        patient_id=PATIENT_ALICE_ID,
        filename="bad.pdf",
        expected_size=len(content),
        expected_sha256="a" * 64,
        claimed_mime_type="application/pdf",
    )
    created = await upload_routes.create_upload_session(
        payload=payload, request=_request(), idempotency_key="idemp-create-fail", session=session, current_user=doctor
    )

    from hospital_ai.services import upload_sessions as us_module

    original_from_request = us_module.UploadSessionService.from_request

    def mocked_from_request(sess, req):
        service = original_from_request(sess, req)
        service.storage = type(
            "MockStorage",
            (),
            {
                "head_object": lambda *args: StorageObjectHead(args[-1], len(content), '"etag"', "application/pdf"),
                "read_stream": lambda *args: io.BytesIO(content),
            },
        )()
        from hospital_ai.services.upload_sessions import StorageContentReader

        service.content_reader = StorageContentReader(service.storage)
        service.scanner = _CleanScanner()
        return service

    monkeypatch.setattr(us_module.UploadSessionService, "from_request", mocked_from_request)
    monkeypatch.setattr("hospital_ai.workers.queue.enqueue_document_indexing", lambda *args, **kwargs: None)

    with pytest.raises(ValidationAppError):
        await upload_routes.finalize_upload_session(
            document_id=created.document_id,
            upload_id=created.upload_id,
            request=_request(),
            idempotency_key="finalize-fail-1",
            session=session,
            current_user=doctor,
        )

    records = list(
        (
            await session.execute(
                select(IdempotencyRecord).where(
                    IdempotencyRecord.key_hash == hashlib.sha256(b"finalize-fail-1").hexdigest()
                )
            )
        ).scalars()
    )
    assert len(records) == 0


def test_routes_registered_in_router() -> None:
    from hospital_ai.api.router import api_router

    paths = [route.path for route in api_router.routes]
    assert any("upload-sessions" in p for p in paths)
    assert any("finalize" in p for p in paths)


class _CleanScanner:
    async def scan(self, key: str):
        from hospital_ai.services.upload_sessions import MalwareScanResult

        return MalwareScanResult(status="clean")
