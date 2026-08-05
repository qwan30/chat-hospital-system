from __future__ import annotations
import pytest
import uuid
from datetime import datetime, UTC

from sqlalchemy import select
from hospital_ai.db.models import Document, DocumentPage, DocumentChunk, User, Patient
from hospital_ai.db.clinical_documents import (
    DocumentRevisionSet,
    DocumentPageRevision,
    DocumentIndexGeneration,
)
from hospital_ai.db.migrations import PATIENT_ALICE_ID, PATIENT_BOB_ID, DOCTOR_ID
from hospital_ai.services.evidence_scope import ActiveEvidenceScope


@pytest.fixture
async def session(session_and_settings):
    session, _ = session_and_settings
    return session


@pytest.fixture
async def seeded_scope_data(session):
    doctor = await session.get(User, DOCTOR_ID)
    if not doctor:
        doctor = User(id=uuid.uuid4(), email="scope_doc@test.com", full_name="Scope Doc", role="doctor", is_active=True)
        session.add(doctor)
        await session.commit()

    doc = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id,
        title="Active Generation Doc",
        document_type="progress_note",
        storage_uri="local://test/scope.pdf",
        mime_type="application/pdf",
        status="ready",
    )
    session.add(doc)
    await session.flush()

    page = DocumentPage(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_number=1,
        ocr_text="Metformin 500mg daily.",
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
        raw_text_snapshot="Metformin 500mg daily.",
        corrected_text="Metformin 500mg daily.",
        confidence=1.0,
        status="approved",
        created_by_user_id=doctor.id,
        content_sha256="abcd" * 16,
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
        revision_set_sha256="abcd" * 16,
        generation_sha256="abcd" * 16,
        created_at=datetime.now(UTC),
        started_at=datetime.now(UTC),
        activated_at=datetime.now(UTC),
    )
    superseded_gen = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=doc.id,
        revision_set_id=rev_set.id,
        state="superseded",
        revision_set_sha256="old0" * 16,
        generation_sha256="old0" * 16,
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
        content="Metformin 500mg daily.",
        token_count=4,
        embedding=[0.1] * 1024,
        meta={},
        generation_id=active_gen.id,
        revision_set_id=rev_set.id,
        page_revision_id=page_rev.id,
        approval_state="approved",
        source_text_sha256="abcd" * 16,
    )

    superseded_chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_id=page.id,
        patient_id=PATIENT_ALICE_ID,
        chunk_index=1,
        content="Old metformin dose.",
        token_count=3,
        embedding=[0.1] * 1024,
        meta={},
        generation_id=superseded_gen.id,
        revision_set_id=rev_set.id,
        page_revision_id=page_rev.id,
        approval_state="approved",
    )

    session.add_all([active_chunk, superseded_chunk])
    await session.commit()
    return doc, active_chunk, superseded_chunk


@pytest.mark.asyncio
async def test_evidence_scope_includes_only_active_generation_chunks(session, seeded_scope_data) -> None:
    doc, active_chunk, superseded_chunk = seeded_scope_data
    scope = ActiveEvidenceScope(session)
    subq = scope.authorized_chunk_ids(user_id=DOCTOR_ID, patient_id=PATIENT_ALICE_ID)
    
    res = await session.execute(select(DocumentChunk.id).where(DocumentChunk.id.in_(subq)))
    chunk_ids = set(res.scalars().all())

    assert active_chunk.id in chunk_ids
    assert superseded_chunk.id not in chunk_ids


@pytest.mark.asyncio
async def test_evidence_scope_respects_document_id_filtering(session, seeded_scope_data) -> None:
    doc, active_chunk, _ = seeded_scope_data
    scope = ActiveEvidenceScope(session)

    # With matching doc ID
    subq1 = scope.authorized_chunk_ids(user_id=DOCTOR_ID, patient_id=PATIENT_ALICE_ID, document_ids=[doc.id])
    res1 = await session.execute(select(DocumentChunk.id).where(DocumentChunk.id.in_(subq1)))
    assert active_chunk.id in set(res1.scalars().all())

    # With non-matching doc ID
    subq2 = scope.authorized_chunk_ids(user_id=DOCTOR_ID, patient_id=PATIENT_ALICE_ID, document_ids=[uuid.uuid4()])
    res2 = await session.execute(select(DocumentChunk.id).where(DocumentChunk.id.in_(subq2)))
    assert active_chunk.id not in set(res2.scalars().all())
