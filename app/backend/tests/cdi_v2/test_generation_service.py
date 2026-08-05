from __future__ import annotations

import uuid
import pytest
from datetime import datetime, UTC

from hospital_ai.db.models import Document, User
from hospital_ai.db.clinical_documents import DocumentIndexGeneration, DocumentRevisionSet, GenerationStageResult
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID


@pytest.fixture
async def gens_fixture(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    if not doctor:
        doctor = User(id=uuid.uuid4(), email="doc@test.com", full_name="Doc", role="doctor", is_active=True)
        session.add(doctor)
        await session.commit()
        
    admin = User(id=uuid.uuid4(), email="admin_gen@test.com", full_name="Admin Gen", role="admin", is_active=True)
    session.add(admin)
    
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id,
        title="Gen Test Doc",
        document_type="progress_note",
        storage_uri="local://test/gen.pdf",
        mime_type="application/pdf",
        status="ready",
    )
    session.add(doc)
    
    rev_set_a = DocumentRevisionSet(
        document_id=doc.id,
        revision_number=1,
        created_by_user_id=doctor.id,
        status="approved",
        submitted_at=datetime.now(UTC),
        approved_by_user_id=doctor.id,
        approved_at=datetime.now(UTC),
    )
    rev_set_b = DocumentRevisionSet(
        document_id=doc.id,
        revision_number=2,
        created_by_user_id=doctor.id,
        status="approved",
        submitted_at=datetime.now(UTC),
        approved_by_user_id=doctor.id,
        approved_at=datetime.now(UTC),
    )
    session.add_all([rev_set_a, rev_set_b])
    await session.flush()
    
    gen_a = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=doc.id,
        revision_set_id=rev_set_a.id,
        state="active",
        revision_set_sha256="r1" * 32,
        generation_sha256="g1" * 32,
        activated_at=datetime.now(UTC),
    )
    gen_b = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=doc.id,
        revision_set_id=rev_set_b.id,
        state="building",
        revision_set_sha256="r2" * 32,
        generation_sha256="g2" * 32,
    )
    session.add_all([gen_a, gen_b])
    await session.flush()
    
    for g in [gen_a, gen_b]:
        for stg in ("ocr_normalization", "facts", "chunks", "embeddings", "lexical_index", "graph", "timeline"):
            session.add(GenerationStageResult(generation_id=g.id, stage=stg, status="completed"))
            
    await session.commit()
    doc.active_index_generation_id = gen_a.id
    doc.approved_revision_set_id = rev_set_a.id
    session.add(doc)
    await session.commit()
    return session, gen_a, gen_b, admin.id


@pytest.mark.asyncio
async def test_failed_generation_b_keeps_generation_a_active(gens_fixture) -> None:
    session, generation_a, generation_b, _ = gens_fixture
    from hospital_ai.services.generations import GenerationService

    document = await session.get(Document, generation_a.document_id)
    document.active_index_generation_id = generation_a.id
    await GenerationService(session).fail(generation_b.id, "EMBEDDING_COUNT_MISMATCH")
    await session.refresh(document)
    assert document.active_index_generation_id == generation_a.id
    assert generation_a.state == "active"
    assert generation_b.state == "failed"


@pytest.mark.asyncio
async def test_rollback_swaps_both_authority_pointers_atomically(gens_fixture) -> None:
    session, generation_a, generation_b, admin_id = gens_fixture
    from hospital_ai.services.generations import GenerationService

    document = await session.get(Document, generation_b.document_id)
    document.active_index_generation_id = generation_b.id
    document.approved_revision_set_id = generation_b.revision_set_id
    generation_b.state = "active"
    generation_a.state = "superseded"
    session.add_all([document, generation_b, generation_a])
    await session.commit()

    result = await GenerationService(session).rollback(
        document_id=generation_b.document_id,
        target_generation_id=generation_a.id,
        actor_id=admin_id,
        expected_active_generation_id=generation_b.id,
    )
    assert result.active_generation_id == generation_a.id
    assert result.approved_revision_set_id == generation_a.revision_set_id
    assert generation_b.state == "superseded"
    assert generation_a.state == "active"
