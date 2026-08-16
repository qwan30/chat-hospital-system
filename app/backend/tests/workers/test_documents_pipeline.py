from __future__ import annotations

import pytest
from sqlalchemy import select

from hospital_ai.db.clinical_documents import DocumentUpload
from hospital_ai.db.migrations import PATIENT_ALICE_ID, RECORDS_ID
from hospital_ai.db.models import Document, DocumentProcessingEvent

# A stub to represent the pipeline entry point that we'll test
# We'll import it from the module the coder is supposed to create/update
# For TDD, if it's missing, it'll fail on import or execution.
try:
    from hospital_ai.workers.pipeline import process_document_pipeline
except ImportError:
    # Dummy mock so test can be written, but we expect the coder to implement it
    async def process_document_pipeline(session, document_id, settings):
        pass


async def _finalize_test_source(session, document: Document) -> None:
    await session.flush()
    upload = DocumentUpload(
        document_id=document.id,
        state="finalized",
        object_key=f"source/test/{document.id}/upload/original.pdf",
        expected_sha256="a" * 64,
        byte_size=1,
        mime_type="application/pdf",
        actor_user_id=document.uploaded_by,
    )
    session.add(upload)
    await session.flush()
    document.finalized_upload_id = upload.id
    document.indexed_source_sha256 = upload.expected_sha256


class _MockFinalizedStorage:
    def source_sha256(self, storage_uri: str) -> str:
        return "a" * 64


@pytest.mark.asyncio
async def test_pipeline_happy_path_states(session_and_settings, monkeypatch):
    session, settings = session_and_settings
    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Pipeline Test",
        document_type="clinical_note",
        storage_uri="mock/path",
        mime_type="application/pdf",
        status="uploaded",
    )
    session.add(document)
    await _finalize_test_source(session, document)
    await session.commit()

    monkeypatch.setattr("hospital_ai.workers.jobs.get_storage_service", lambda settings: _MockFinalizedStorage())

    # The coder should implement process_document_pipeline to iterate over stages
    await process_document_pipeline(session, document.id, settings)

    await session.refresh(document)

    # Check if the coder implemented the final state
    assert document.status in ("ready", "ready_with_warnings", "review_required")

    # Check for the expected processing events according to the spec
    result = await session.execute(
        select(DocumentProcessingEvent)
        .where(DocumentProcessingEvent.document_id == document.id)
        .order_by(DocumentProcessingEvent.sequence)
    )
    events = list(result.scalars().all())

    stages = [event.stage for event in events if event.state == "completed"]
    expected_stages = [
        "preflight_document",
        "classify_document",
        # "extract_native_pages", # or vision
        # "reconstruct_document",
        # "extract_clinical_facts",
        # "validate_and_route_review",
        # "build_fhir_draft",
        # "index_document",
        # "extract_graph",
        # "run_cdss",
        # "finalize_document"
    ]

    # We just test that the pipeline executed the new stages from CDI-001 spec.
    # The actual exact sequence depends on the document type, but we should see these basic ones.
    for stage in expected_stages:
        assert stage in stages, f"Expected pipeline stage '{stage}' not found in processing events."


@pytest.mark.asyncio
async def test_pipeline_review_required_state(session_and_settings, monkeypatch):
    session, settings = session_and_settings
    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Needs Review",
        document_type="clinical_note",
        storage_uri="mock/path",
        mime_type="application/pdf",
        status="uploaded",
    )
    session.add(document)
    await _finalize_test_source(session, document)
    await session.commit()

    monkeypatch.setattr("hospital_ai.workers.jobs.get_storage_service", lambda settings: _MockFinalizedStorage())

    # We can use monkeypatch in a real scenario to force the fact extractor
    # to emit a low confidence fact, but for now we just verify the pipeline can enter 'review_required'

    await process_document_pipeline(session, document.id, settings)

    await session.refresh(document)
    # This test will fail until the coder implements the state machine properly.
    assert document.status == "review_required"
