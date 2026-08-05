from __future__ import annotations

import hashlib
import io
import uuid

import pytest
from fastapi import Request, UploadFile
from starlette.datastructures import Headers
from starlette.responses import Response

from hospital_ai.api.routes import documents as document_routes
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import Document, User


class _FakeR2Storage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.upload_called = False

    async def save_upload(self, *, patient_id: uuid.UUID, document_id: uuid.UUID, file: UploadFile) -> str:
        self.upload_called = True
        payload = await file.read()
        uri = f"r2://patients/{patient_id}/documents/{document_id}/upload.txt"
        self.objects[uri] = payload
        return uri

    def read_bytes(self, storage_uri: str) -> bytes:
        return self.objects[storage_uri]

    def source_sha256(self, storage_uri: str) -> str:
        return hashlib.sha256(self.read_bytes(storage_uri)).hexdigest()

    def save_page_image(self, patient_id: str, document_id: str, page_number: int, image_bytes: bytes) -> str:
        uri = f"r2://patients/{patient_id}/documents/{document_id}/pages/{page_number}.png"
        self.objects[uri] = image_bytes
        return uri

    def read_page_image(self, patient_id: str, document_id: str, page_number: int) -> bytes:
        return self.objects[f"r2://patients/{patient_id}/documents/{document_id}/pages/{page_number}.png"]

    def create_presigned_put(self, *, key: str, content_type: str, expires_seconds: int) -> Any:
        from hospital_ai.services.storage import PresignedPut

        return PresignedPut(
            url=f"https://fake.r2/{key}", required_headers={"Content-Type": content_type, "If-None-Match": "*"}
        )

    def head_object(self, key: str) -> Any:
        from hospital_ai.services.storage import StorageObjectHead

        if key not in self.objects:
            raise FileNotFoundError()
        return StorageObjectHead(key, len(self.objects[key]), '"etag"', "application/pdf")

    def read_stream(self, key: str) -> io.BytesIO:
        return io.BytesIO(self.objects[key])

    def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)


def _request() -> Request:
    return Request({"type": "http", "client": ("127.0.0.1", 8000)})


@pytest.mark.asyncio
async def test_upload_document_selects_storage_factory(session_and_settings, monkeypatch: pytest.MonkeyPatch) -> None:
    session, settings = session_and_settings
    settings.worker_inline = False
    storage = _FakeR2Storage()
    monkeypatch.setattr(document_routes, "get_storage_service", lambda _settings: storage, raising=False)
    monkeypatch.setattr(document_routes, "enqueue_document_indexing", lambda *_args: "queued")
    doctor = await session.get(User, DOCTOR_ID)

    document = await document_routes.upload_document(
        request=_request(),
        patient_id=PATIENT_ALICE_ID,
        title="R2 note",
        document_type="chat_attachment",
        file=UploadFile(
            filename="upload.txt",
            file=io.BytesIO(b"R2 source"),
            headers=Headers({"content-type": "text/plain"}),
        ),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    assert storage.upload_called is True
    assert document.storage_uri.startswith("r2://")


@pytest.mark.asyncio
async def test_document_content_is_served_from_storage_bytes(
    session_and_settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    session, settings = session_and_settings
    storage = _FakeR2Storage()
    uri = "r2://patients/patient-1/documents/document-1/upload.txt"
    payload = b"R2 content bytes"
    storage.objects[uri] = payload
    monkeypatch.setattr(document_routes, "get_storage_service", lambda _settings: storage, raising=False)
    doctor = await session.get(User, DOCTOR_ID)
    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="R2 content",
        document_type="chat_attachment",
        storage_uri=uri,
        mime_type="text/plain",
        status="ready",
    )
    session.add(document)
    await session.commit()

    response = await document_routes.get_document_content(
        document_id=document.id,
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    assert isinstance(response, Response)
    assert response.media_type == "text/plain"
    assert response.body == payload


@pytest.mark.asyncio
async def test_document_page_image_is_served_from_storage_bytes(
    session_and_settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    session, settings = session_and_settings
    storage = _FakeR2Storage()
    page_uri = "r2://patients/patient-1/documents/document-1/pages/1.png"
    page_png = b"\x89PNG\r\n\x1a\npage"
    storage.objects[page_uri] = page_png
    monkeypatch.setattr(document_routes, "get_storage_service", lambda _settings: storage, raising=False)
    doctor = await session.get(User, DOCTOR_ID)
    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="R2 image",
        document_type="chat_attachment",
        storage_uri="r2://patients/patient-1/documents/document-1/source.pdf",
        mime_type="application/pdf",
        status="ready",
    )
    session.add(document)
    await session.commit()
    storage.objects[f"r2://patients/{PATIENT_ALICE_ID}/documents/{document.id}/pages/1.png"] = page_png

    response = await document_routes.get_document_page_image(
        document_id=document.id,
        page_number=1,
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    assert isinstance(response, Response)
    assert response.media_type == "image/png"
    assert response.body == page_png


@pytest.mark.asyncio
async def test_upload_session_storage_integration(session_and_settings, monkeypatch: pytest.MonkeyPatch) -> None:
    session, settings = session_and_settings
    storage = _FakeR2Storage()
    monkeypatch.setattr("hospital_ai.services.storage.get_storage_service", lambda _settings: storage)

    from hospital_ai.services.upload_sessions import UploadSessionService

    service = UploadSessionService.from_request(session, _request())

    res = await service.create(
        patient_id=uuid.uuid4(),
        filename="test.pdf",
        expected_size=10,
        expected_sha256="d" * 64,
        claimed_mime_type="application/pdf",
    )
    assert res.presigned_url and res.presigned_url.startswith("https://fake.r2/")
    assert res.required_headers == {"Content-Type": "application/pdf", "If-None-Match": "*"}
