from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from hospital_ai.db.clinical_graph import GraphEntity, GraphMention, GraphRelationAssertion
from hospital_ai.services.graph_index import GraphIndexService
from hospital_ai.services.graph_rag import ExtractedEntity, GraphExtraction


@pytest.mark.asyncio
async def test_one_canonical_entity_keeps_independent_source_mentions(session_and_settings) -> None:
    session, _ = session_and_settings
    patient_id = uuid.uuid4()
    from hospital_ai.db.clinical_documents import DocumentIndexGeneration, DocumentRevisionSet
    from hospital_ai.db.models import Document, DocumentChunk, DocumentPage, Patient

    session.add(Patient(id=patient_id, full_name="Test Patient", mrn="TEST-MRN"))
    await session.flush()

    from hospital_ai.db.migrations import DOCTOR_ID

    # Setup 2 sources
    doc1 = Document(
        patient_id=patient_id,
        title="Doc 1",
        uploaded_by=DOCTOR_ID,
        mime_type="text/plain",
        storage_uri="mem",
        status="ready",
        document_type="clinical_note",
    )
    doc2 = Document(
        patient_id=patient_id,
        title="Doc 2",
        uploaded_by=DOCTOR_ID,
        mime_type="text/plain",
        storage_uri="mem",
        status="ready",
        document_type="clinical_note",
    )
    session.add_all([doc1, doc2])
    await session.flush()

    page1 = DocumentPage(document_id=doc1.id, page_number=1, ocr_text="text")
    page2 = DocumentPage(document_id=doc2.id, page_number=1, ocr_text="text")
    session.add_all([page1, page2])
    await session.flush()

    from sqlalchemy import func

    rev_set1 = DocumentRevisionSet(
        document_id=doc1.id,
        revision_number=1,
        created_by_user_id=DOCTOR_ID,
        status="approved",
        submitted_at=func.now(),
        approved_at=func.now(),
        approved_by_user_id=DOCTOR_ID,
    )
    rev_set2 = DocumentRevisionSet(
        document_id=doc2.id,
        revision_number=1,
        created_by_user_id=DOCTOR_ID,
        status="approved",
        submitted_at=func.now(),
        approved_at=func.now(),
        approved_by_user_id=DOCTOR_ID,
    )
    session.add_all([rev_set1, rev_set2])
    await session.flush()

    from hospital_ai.db.clinical_documents import DocumentPageRevision

    page_rev1 = DocumentPageRevision(
        document_id=doc1.id,
        page_number=1,
        revision_number=1,
        revision_type="initial",
        raw_text_snapshot="text",
        corrected_text="text",
        status="approved",
        created_by_user_id=DOCTOR_ID,
        content_sha256="abc",
    )
    page_rev2 = DocumentPageRevision(
        document_id=doc2.id,
        page_number=1,
        revision_number=1,
        revision_type="initial",
        raw_text_snapshot="text",
        corrected_text="text",
        status="approved",
        created_by_user_id=DOCTOR_ID,
        content_sha256="abc",
    )
    session.add_all([page_rev1, page_rev2])
    await session.flush()

    gen1 = DocumentIndexGeneration(
        document_id=doc1.id,
        revision_set_id=rev_set1.id,
        state="active",
        revision_set_sha256="abc",
        generation_sha256="abc",
    )
    gen2 = DocumentIndexGeneration(
        document_id=doc2.id,
        revision_set_id=rev_set2.id,
        state="active",
        revision_set_sha256="def",
        generation_sha256="def",
    )
    session.add_all([gen1, gen2])
    await session.flush()

    chunk1 = DocumentChunk(
        document_id=doc1.id,
        page_id=page1.id,
        patient_id=patient_id,
        chunk_index=0,
        content="text",
        generation_id=gen1.id,
        revision_set_id=rev_set1.id,
        page_revision_id=page_rev1.id,
    )
    chunk2 = DocumentChunk(
        document_id=doc2.id,
        page_id=page2.id,
        patient_id=patient_id,
        chunk_index=0,
        content="text",
        generation_id=gen2.id,
        revision_set_id=rev_set2.id,
        page_revision_id=page_rev2.id,
    )
    session.add_all([chunk1, chunk2])
    await session.flush()

    def metformin_extraction():
        return GraphExtraction(
            entities=[ExtractedEntity(entity_type="medication", normalized_label="metformin")], relations=[]
        )

    service = GraphIndexService(session)
    await service.index_chunk(gen1.id, chunk1, metformin_extraction())
    await service.index_chunk(gen2.id, chunk2, metformin_extraction())

    entities = list(await session.scalars(select(GraphEntity)))
    mentions = list(await session.scalars(select(GraphMention).where(GraphMention.entity_id == entities[0].id)))

    assert len(entities) == 1
    assert {row.document_id for row in mentions} == {doc1.id, doc2.id}
    assert len({row.independent_source_identity for row in mentions}) == 2


@pytest.mark.asyncio
async def test_cross_patient_relation_is_rejected(session_and_settings) -> None:
    session, _ = session_and_settings
    from sqlalchemy import text

    await session.execute(text("PRAGMA foreign_keys=ON"))
    from hospital_ai.db.models import Patient

    patient_alice_id = uuid.uuid4()
    patient_bob_id = uuid.uuid4()
    session.add_all(
        [
            Patient(id=patient_alice_id, full_name="Alice", mrn="MRN-1"),
            Patient(id=patient_bob_id, full_name="Bob", mrn="MRN-2"),
        ]
    )
    await session.flush()
    entity_a = GraphEntity(patient_id=patient_alice_id, entity_type="person", normalized_label="alice")
    entity_b = GraphEntity(patient_id=patient_bob_id, entity_type="person", normalized_label="bob")
    session.add_all([entity_a, entity_b])
    from sqlalchemy.exc import IntegrityError, OperationalError

    with pytest.raises((IntegrityError, OperationalError)):
        assertion = GraphRelationAssertion(
            patient_id=patient_alice_id,
            subject_entity_id=entity_a.id,
            object_entity_id=entity_b.id,
            relation_type="treated_by",
            normalized_value="treated_by",
        )
        session.add(assertion)
        await session.flush()
