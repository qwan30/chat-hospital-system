import pytest
import uuid
from datetime import datetime, UTC

from hospital_ai.db.models import Document, DocumentPage, DocumentChunk, User
from hospital_ai.db.clinical_documents import (
    DocumentRevisionSet,
    DocumentPageRevision,
    DocumentIndexGeneration,
)
from hospital_ai.db.migrations import PATIENT_ALICE_ID, PATIENT_BOB_ID, DOCTOR_ID
from hospital_ai.services.retrieval import RetrievalService


@pytest.fixture
async def session(session_and_settings):
    session, _ = session_and_settings
    return session


@pytest.fixture
async def seeded_generations(session):
    doctor = await session.get(User, DOCTOR_ID)
    if not doctor:
        doctor = User(id=uuid.uuid4(), email="rev_doc@test.com", full_name="Rev Doc", role="doctor", is_active=True)
        session.add(doctor)
        await session.commit()

    doc = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id,
        title="Revision Aware Retrieval Doc",
        document_type="progress_note",
        storage_uri="local://test/rev_retrieval.pdf",
        mime_type="application/pdf",
        status="ready",
    )
    session.add(doc)
    await session.flush()

    page = DocumentPage(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_number=1,
        ocr_text="metformin dose 500mg daily",
        ocr_confidence=1.0,
    )
    session.add(page)
    await session.flush()

    page_rev = DocumentPageRevision(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_number=1,
        revision_number=1,
        revision_type="machine_ocr",
        raw_text_snapshot="metformin dose 500mg daily",
        corrected_text="metformin dose 500mg daily",
        confidence=1.0,
        status="approved",
        created_by_user_id=doctor.id,
        content_sha256="efgh" * 16,
        version=1,
    )
    session.add(page_rev)
    await session.flush()

    rev_set = DocumentRevisionSet(
        id=uuid.uuid4(),
        document_id=doc.id,
        revision_number=1,
        status="approved",
        created_by_user_id=doctor.id,
        submitted_at=datetime.now(UTC),
        approved_by_user_id=doctor.id,
        approved_at=datetime.now(UTC),
    )
    session.add(rev_set)
    await session.flush()

    active_gen = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=doc.id,
        revision_set_id=rev_set.id,
        state="active",
        revision_set_sha256="efgh" * 16,
        generation_sha256="efgh" * 16,
        created_at=datetime.now(UTC),
        started_at=datetime.now(UTC),
        activated_at=datetime.now(UTC),
    )
    superseded_gen = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=doc.id,
        revision_set_id=rev_set.id,
        state="superseded",
        revision_set_sha256="old1" * 16,
        generation_sha256="old1" * 16,
        created_at=datetime.now(UTC),
    )
    session.add_all([active_gen, superseded_gen])
    await session.flush()

    doc.approved_revision_set_id = rev_set.id
    doc.active_index_generation_id = active_gen.id

    active_chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_id=page.id,
        patient_id=PATIENT_ALICE_ID,
        chunk_index=0,
        content="metformin dose 500mg daily",
        token_count=4,
        embedding=[0.1] * 1024,
        meta={"access_tags": []},
        generation_id=active_gen.id,
        revision_set_id=rev_set.id,
        page_revision_id=page_rev.id,
        approval_state="approved",
        source_text_sha256="efgh" * 16,
        text_start_offset=0,
        text_end_offset=26,
    )

    superseded_chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_id=page.id,
        patient_id=PATIENT_ALICE_ID,
        chunk_index=1,
        content="metformin dose 250mg daily (old)",
        token_count=5,
        embedding=[0.1] * 1024,
        meta={"access_tags": []},
        generation_id=superseded_gen.id,
        revision_set_id=rev_set.id,
        page_revision_id=page_rev.id,
        approval_state="approved",
    )

    wrong_patient_chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_id=page.id,
        patient_id=PATIENT_BOB_ID,
        chunk_index=2,
        content="metformin dose 1000mg for Bob",
        token_count=5,
        embedding=[0.1] * 1024,
        meta={"access_tags": []},
        generation_id=active_gen.id,
        revision_set_id=rev_set.id,
        page_revision_id=page_rev.id,
        approval_state="approved",
    )

    session.add_all([active_chunk, superseded_chunk, wrong_patient_chunk])
    await session.commit()
    return doc, active_chunk


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["vector", "bm25", "hybrid"])
async def test_retrieval_excludes_wrong_patient_and_superseded_generation(
    session, seeded_generations, mode
) -> None:
    results = await RetrievalService(session).hybrid_search(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        query="metformin dose",
        query_embedding=[0.1] * 1024,
        top_k=20,
        mode=mode,
    )
    assert results
    assert all(row.patient_id == PATIENT_ALICE_ID for row in results)
    assert all(row.generation_id == row.active_index_generation_id for row in results)
    assert all(row.approval_state == "approved" for row in results)
