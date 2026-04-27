from pathlib import Path

import pytest
from sqlalchemy import select

from hospital_ai.db.migrations import PATIENT_ALICE_ID, RECORDS_ID
from hospital_ai.db.models import Document, DocumentChunk
from hospital_ai.workers.jobs import process_document


@pytest.mark.asyncio
async def test_text_document_moves_to_indexed(session_and_settings, tmp_path: Path):
    session, settings = session_and_settings
    storage_file = tmp_path / "note.txt"
    storage_file.write_text("Patient reports dizziness. Follow up with cardiology.", encoding="utf-8")
    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Synthetic note",
        document_type="clinical_note",
        storage_uri=str(storage_file),
        mime_type="text/plain",
        status="uploaded",
    )
    session.add(document)
    await session.commit()

    await process_document(session, document.id, settings)

    refreshed = await session.get(Document, document.id)
    assert refreshed.status == "indexed"
    assert refreshed.page_count == 1
    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document.id))
    assert len(result.scalars().all()) == 1


@pytest.mark.asyncio
async def test_failed_ocr_creates_no_chunks(session_and_settings, tmp_path: Path, monkeypatch):
    session, settings = session_and_settings
    storage_file = tmp_path / "scan.pdf"
    storage_file.write_bytes(b"%PDF-1.4 synthetic")
    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Bad scan",
        document_type="scan",
        storage_uri=str(storage_file),
        mime_type="application/pdf",
        status="uploaded",
    )
    session.add(document)
    await session.commit()

    def fail_ocr(self, *, storage_uri, mime_type):
        raise RuntimeError("ocr failed")

    monkeypatch.setattr("hospital_ai.services.ocr.OcrService.extract_pages", fail_ocr)
    await process_document(session, document.id, settings)

    refreshed = await session.get(Document, document.id)
    assert refreshed.status == "ocr_failed"
    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document.id))
    assert result.scalars().all() == []
