from __future__ import annotations

import uuid
from datetime import datetime, UTC
import pytest
from sqlalchemy import select

from hospital_ai.db.models import Document, DocumentChunk, User
from hospital_ai.db.clinical_documents import DocumentPageRevision, DocumentDraftHead, DocumentExtractionRun
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.workers.extraction_jobs import extract_document
from hospital_ai.workers.ocr_models import OcrModelManager, OcrResourceError

@pytest.fixture
async def finalized_document(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    if not doctor:
        doctor = User(id=uuid.uuid4(), email="doc@test.com", full_name="Doc", role="doctor", is_active=True)
        session.add(doctor)
        await session.commit()

    doc = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id,
        title="Extraction Test Doc",
        document_type="progress_note",
        storage_uri="local://test/extraction_doc.pdf",
        mime_type="application/pdf",
        status="uploaded",
        indexed_source_sha256="b" * 64,
    )
    session.add(doc)
    await session.commit()
    return doc

@pytest.mark.asyncio
async def test_extraction_creates_machine_revisions_but_no_chunks(session_and_settings, finalized_document, monkeypatch: pytest.MonkeyPatch) -> None:
    session, settings = session_and_settings

    # Mock file retrieval and OCR pipeline so unit test runs quickly without R2/actual models
    from hospital_ai.services.ocr_routing import OcrPageResult, OcrSpanResult
    async def mock_extract(*args, **kwargs):
        span = OcrSpanResult(
            text="Extracted text",
            start_offset=0,
            end_offset=14,
            polygon=((0.0, 0.0), (10.0, 0.0), (10.0, 5.0), (0.0, 5.0)),
            confidence=0.95,
            reading_order=1,
            engine_family="paddle_printed",
            engine_model="v4",
            engine_revision="r1",
        )
        return [
            OcrPageResult(
                page_number=1,
                raw_text="Extracted text",
                confidence=0.95,
                route="paddle_printed",
                spans=(span,),
                latency_ms=100,
                peak_rss_mb=200,
            )
        ]
    
    monkeypatch.setattr("hospital_ai.workers.extraction_jobs.ocr_pipeline_extract", mock_extract, raising=False)
    
    await extract_document(session, finalized_document.id, settings)
    revisions = list(await session.scalars(select(DocumentPageRevision).where(DocumentPageRevision.document_id == finalized_document.id)))
    chunks = list(await session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == finalized_document.id)))
    assert revisions and all(row.revision_type == "machine_ocr" for row in revisions)
    assert chunks == []
    assert (await session.get(Document, finalized_document.id)).status == "review_required"

@pytest.mark.asyncio
async def test_acquire_model_and_resource_limits() -> None:
    manager = OcrModelManager()
    with pytest.raises(OcrResourceError):
        # Using a simulated OOM or unsupported artifact
        async with manager.acquire_model("force_oom"):
            pass
