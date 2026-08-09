from __future__ import annotations

import uuid

import pytest
from fastapi import Request

from hospital_ai.db.migrations import DOCTOR_ID
from hospital_ai.db.models import User


def _request() -> Request:
    return Request(
        {"type": "http", "client": ("127.0.0.1", 8000), "method": "POST", "path": "/api/v1/documents/upload-sessions"}
    )


@pytest.mark.asyncio
async def test_create_upload_session_idempotency_replay(session_and_settings, monkeypatch: pytest.MonkeyPatch) -> None:
    session, settings = session_and_settings
    from hospital_ai.api.routes import document_uploads as upload_routes
    from hospital_ai.schemas.document_uploads import UploadSessionCreate

    doctor = await session.get(User, DOCTOR_ID)
    if not doctor:
        doctor = User(
            id=uuid.uuid4(), email="doc@test.com", password_hash="hash", full_name="Doc", role="doctor", is_active=True
        )
        session.add(doctor)
        await session.commit()

    payload = UploadSessionCreate(
        patient_id=uuid.uuid4(),
        filename="report.pdf",
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


@pytest.mark.asyncio
async def test_finalize_upload_session(session_and_settings, monkeypatch: pytest.MonkeyPatch) -> None:
    session, settings = session_and_settings
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

    payload = UploadSessionCreate(
        patient_id=uuid.uuid4(),
        filename="report.pdf",
        expected_size=10,
        expected_sha256="c" * 64,
        claimed_mime_type="application/pdf",
    )

    created = await upload_routes.create_upload_session(
        payload=payload,
        request=_request(),
        idempotency_key="idemp-test-2",
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
                "head_object": lambda *args: StorageObjectHead(args[-1], 10, '"etag"', "application/pdf"),
                "read_stream": lambda *args: None,
            },
        )()
        return service

    monkeypatch.setattr(us_module.UploadSessionService, "from_request", mocked_from_request)

    res = await upload_routes.finalize_upload_session(
        document_id=created.document_id,
        upload_id=created.upload_id,
        request=_request(),
        session=session,
        current_user=doctor,
    )
    assert res.state == "finalized"


def test_routes_registered_in_router() -> None:
    from hospital_ai.api.router import api_router

    paths = [route.path for route in api_router.routes]
    assert any("upload-sessions" in p for p in paths)
    assert any("finalize" in p for p in paths)
