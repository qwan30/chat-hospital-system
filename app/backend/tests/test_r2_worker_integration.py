from __future__ import annotations

import hashlib

import fitz
import pytest

from hospital_ai.db.migrations import PATIENT_ALICE_ID, RECORDS_ID
from hospital_ai.db.models import Document
from hospital_ai.workers import jobs


class _FakeR2WorkerStorage:
    def __init__(self, source_bytes: bytes) -> None:
        self.source_bytes = source_bytes
        self.read_uris: list[str] = []
        self.page_images: dict[str, bytes] = {}

    def read_bytes(self, storage_uri: str) -> bytes:
        self.read_uris.append(storage_uri)
        return self.source_bytes

    def source_sha256(self, storage_uri: str) -> str:
        return hashlib.sha256(self.read_bytes(storage_uri)).hexdigest()

    def save_page_image(self, patient_id: str, document_id: str, page_number: int, image_bytes: bytes) -> str:
        uri = f"r2://patients/{patient_id}/documents/{document_id}/pages/{page_number}.png"
        self.page_images[uri] = image_bytes
        return uri

    def read_page_image(self, patient_id: str, document_id: str, page_number: int) -> bytes:
        return self.page_images[f"r2://patients/{patient_id}/documents/{document_id}/pages/{page_number}.png"]


def _pdf_bytes() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "R2 worker source text")
    payload = document.tobytes()
    document.close()
    return payload


@pytest.mark.asyncio
async def test_worker_processes_r2_uri_and_fingerprints_source(
    session_and_settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    session, settings = session_and_settings
    source = _pdf_bytes()
    storage = _FakeR2WorkerStorage(source)
    monkeypatch.setattr(jobs, "get_storage_service", lambda _settings: storage, raising=False)
    monkeypatch.setattr(
        "hospital_ai.workers.queue.enqueue_cdss_analysis",
        lambda *_args, **_kwargs: "queued",
    )

    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="R2 worker document",
        document_type="clinical_note",
        storage_uri="r2://patients/r2-patient/documents/r2-document/source.pdf",
        mime_type="application/pdf",
        status="uploaded",
    )
    session.add(document)
    await session.commit()

    await jobs.process_document(session, document.id, settings)
    await session.refresh(document)

    assert document.status == "ready"
    assert document.indexed_source_sha256 == hashlib.sha256(source).hexdigest()
    assert storage.read_uris
    assert all(uri.startswith("r2://") for uri in storage.read_uris)
    assert len(storage.page_images) == 1
    assert next(iter(storage.page_images.values())).startswith(b"\x89PNG")
