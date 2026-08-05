from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from hospital_ai.db.clinical_documents import (
    ClinicalTimelineEvent,
    DocumentIndexGeneration,
    DocumentPageRevision,
    DocumentRevisionSet,
)
from hospital_ai.db.clinical_graph import GraphEntity, GraphMention, GraphRelationAssertion, GraphRelationEvidence
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage, User
from hospital_ai.services.clinical_timeline import ClinicalTimelineService
from hospital_ai.services.evidence_scope import ActiveEvidenceScope
from hospital_ai.services.graph_query import GraphFilters, GraphQueryService
from hospital_ai.services.graph_rag import find_related_entities
from hospital_ai.services.retrieval import RetrievalService


@pytest.fixture
async def cross_path_data(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    document = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Cross path scope document",
        document_type="progress_note",
        storage_uri="local://test/cross-path.pdf",
        mime_type="application/pdf",
        status="ready",
    )
    session.add(document)
    await session.flush()

    page = DocumentPage(
        id=uuid.uuid4(),
        document_id=document.id,
        page_number=1,
        ocr_text="active evidence",
        ocr_confidence=1.0,
    )
    session.add(page)
    await session.flush()

    approved_page = DocumentPageRevision(
        id=uuid.uuid4(),
        document_id=document.id,
        page_number=1,
        revision_number=1,
        revision_type="machine_ocr",
        raw_text_snapshot="active evidence",
        corrected_text="active evidence",
        confidence=1.0,
        status="approved",
        created_by_user_id=DOCTOR_ID,
        content_sha256="a" * 64,
        version=1,
    )
    low_confidence_page = DocumentPageRevision(
        id=uuid.uuid4(),
        document_id=document.id,
        page_number=1,
        revision_number=2,
        revision_type="machine_ocr",
        raw_text_snapshot="low confidence evidence",
        corrected_text="low confidence evidence",
        confidence=0.2,
        status="approved",
        created_by_user_id=DOCTOR_ID,
        content_sha256="b" * 64,
        version=2,
    )
    session.add_all([approved_page, low_confidence_page])
    await session.flush()

    approved_set = DocumentRevisionSet(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_number=1,
        status="approved",
        created_by_user_id=DOCTOR_ID,
        submitted_at=datetime.now(UTC),
        approved_by_user_id=DOCTOR_ID,
        approved_at=datetime.now(UTC),
    )
    unapproved_set = DocumentRevisionSet(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_number=2,
        status="submitted",
        created_by_user_id=DOCTOR_ID,
        submitted_at=datetime.now(UTC),
    )
    session.add_all([approved_set, unapproved_set])
    await session.flush()

    active_generation = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_set_id=approved_set.id,
        state="active",
        revision_set_sha256="c" * 64,
        generation_sha256="d" * 64,
        created_at=datetime.now(UTC),
        started_at=datetime.now(UTC),
        activated_at=datetime.now(UTC),
    )
    superseded_generation = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_set_id=approved_set.id,
        state="superseded",
        revision_set_sha256="e" * 64,
        generation_sha256="f" * 64,
        created_at=datetime.now(UTC),
    )
    unapproved_generation = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_set_id=unapproved_set.id,
        state="active",
        revision_set_sha256="1" * 64,
        generation_sha256="2" * 64,
        created_at=datetime.now(UTC),
    )
    session.add_all([active_generation, superseded_generation, unapproved_generation])
    await session.flush()
    document.approved_revision_set_id = approved_set.id
    document.active_index_generation_id = active_generation.id

    active_chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=document.id,
        page_id=page.id,
        patient_id=PATIENT_ALICE_ID,
        chunk_index=0,
        content="active evidence",
        token_count=2,
        embedding=[0.1] * 1024,
        meta={"access_tags": []},
        generation_id=active_generation.id,
        revision_set_id=approved_set.id,
        page_revision_id=approved_page.id,
        approval_state="approved",
        source_text_sha256="a" * 64,
    )
    superseded_chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=document.id,
        page_id=page.id,
        patient_id=PATIENT_ALICE_ID,
        chunk_index=1,
        content="superseded evidence",
        token_count=2,
        embedding=[0.1] * 1024,
        meta={"access_tags": []},
        generation_id=superseded_generation.id,
        revision_set_id=approved_set.id,
        page_revision_id=approved_page.id,
        approval_state="approved",
    )
    wrong_patient_chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=document.id,
        page_id=page.id,
        patient_id=PATIENT_BOB_ID,
        chunk_index=2,
        content="wrong patient evidence",
        token_count=3,
        embedding=[0.1] * 1024,
        meta={"access_tags": []},
        generation_id=active_generation.id,
        revision_set_id=approved_set.id,
        page_revision_id=approved_page.id,
        approval_state="approved",
    )
    deleted_chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=document.id,
        page_id=page.id,
        patient_id=PATIENT_ALICE_ID,
        chunk_index=3,
        content="deleted evidence",
        token_count=2,
        embedding=[0.1] * 1024,
        meta={"access_tags": []},
        generation_id=active_generation.id,
        revision_set_id=approved_set.id,
        page_revision_id=approved_page.id,
        approval_state="approved",
        deleted_at=datetime.now(UTC),
    )
    unapproved_chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=document.id,
        page_id=page.id,
        patient_id=PATIENT_ALICE_ID,
        chunk_index=4,
        content="unapproved evidence",
        token_count=2,
        embedding=[0.1] * 1024,
        meta={"access_tags": []},
        generation_id=unapproved_generation.id,
        revision_set_id=unapproved_set.id,
        page_revision_id=approved_page.id,
        approval_state="approved",
    )
    session.add_all([active_chunk, superseded_chunk, wrong_patient_chunk, deleted_chunk, unapproved_chunk])
    await session.flush()

    active_entity = GraphEntity(
        id=uuid.uuid4(), patient_id=PATIENT_ALICE_ID, entity_type="medication", normalized_label="active medication"
    )
    superseded_entity = GraphEntity(
        id=uuid.uuid4(), patient_id=PATIENT_ALICE_ID, entity_type="medication", normalized_label="superseded medication"
    )
    wrong_patient_entity = GraphEntity(
        id=uuid.uuid4(),
        patient_id=PATIENT_BOB_ID,
        entity_type="medication",
        normalized_label="wrong patient medication",
    )
    session.add_all([active_entity, superseded_entity, wrong_patient_entity])
    await session.flush()

    session.add_all(
        [
            GraphMention(
                patient_id=PATIENT_ALICE_ID,
                entity_id=active_entity.id,
                generation_id=active_generation.id,
                document_id=document.id,
                revision_set_id=approved_set.id,
                page_revision_id=approved_page.id,
                chunk_id=active_chunk.id,
                independent_source_identity="active",
            ),
            GraphMention(
                patient_id=PATIENT_ALICE_ID,
                entity_id=superseded_entity.id,
                generation_id=superseded_generation.id,
                document_id=document.id,
                revision_set_id=approved_set.id,
                page_revision_id=approved_page.id,
                chunk_id=superseded_chunk.id,
                independent_source_identity="superseded",
            ),
            GraphMention(
                patient_id=PATIENT_BOB_ID,
                entity_id=wrong_patient_entity.id,
                generation_id=active_generation.id,
                document_id=document.id,
                revision_set_id=approved_set.id,
                page_revision_id=approved_page.id,
                chunk_id=wrong_patient_chunk.id,
                independent_source_identity="wrong-patient",
            ),
            GraphMention(
                patient_id=PATIENT_ALICE_ID,
                entity_id=active_entity.id,
                generation_id=unapproved_generation.id,
                document_id=document.id,
                revision_set_id=unapproved_set.id,
                page_revision_id=approved_page.id,
                chunk_id=unapproved_chunk.id,
                independent_source_identity="unapproved",
            ),
            GraphMention(
                patient_id=PATIENT_ALICE_ID,
                entity_id=active_entity.id,
                generation_id=active_generation.id,
                document_id=document.id,
                revision_set_id=approved_set.id,
                page_revision_id=approved_page.id,
                chunk_id=deleted_chunk.id,
                independent_source_identity="deleted",
            ),
        ]
    )

    active_assertion = GraphRelationAssertion(
        patient_id=PATIENT_ALICE_ID,
        subject_entity_id=active_entity.id,
        object_entity_id=active_entity.id,
        relation_type="active_relation",
        normalized_value="active",
    )
    superseded_assertion = GraphRelationAssertion(
        patient_id=PATIENT_ALICE_ID,
        subject_entity_id=superseded_entity.id,
        object_entity_id=superseded_entity.id,
        relation_type="superseded_relation",
        normalized_value="superseded",
    )
    session.add_all([active_assertion, superseded_assertion])
    await session.flush()
    session.add_all(
        [
            GraphRelationEvidence(
                patient_id=PATIENT_ALICE_ID,
                assertion_id=active_assertion.id,
                generation_id=active_generation.id,
                document_id=document.id,
                revision_set_id=approved_set.id,
                page_revision_id=approved_page.id,
                chunk_id=active_chunk.id,
                independent_source_identity="active-relation",
            ),
            GraphRelationEvidence(
                patient_id=PATIENT_ALICE_ID,
                assertion_id=superseded_assertion.id,
                generation_id=superseded_generation.id,
                document_id=document.id,
                revision_set_id=approved_set.id,
                page_revision_id=approved_page.id,
                chunk_id=superseded_chunk.id,
                independent_source_identity="superseded-relation",
            ),
        ]
    )

    event_rows = {
        "active": ClinicalTimelineEvent(
            patient_id=PATIENT_ALICE_ID,
            event_type="active_event",
            clinical_date=datetime(2026, 1, 1, tzinfo=UTC),
            recorded_date=datetime(2026, 1, 2, tzinfo=UTC),
            source_evidence={
                "document_id": str(document.id),
                "generation_id": str(active_generation.id),
                "revision_set_id": str(approved_set.id),
                "chunk_ids": [str(active_chunk.id)],
            },
            confidence=0.99,
            reviewer_state="approved",
            conflict_state="none",
        ),
        "superseded": ClinicalTimelineEvent(
            patient_id=PATIENT_ALICE_ID,
            event_type="superseded_event",
            clinical_date=datetime(2025, 1, 1, tzinfo=UTC),
            recorded_date=datetime(2025, 1, 2, tzinfo=UTC),
            source_evidence={
                "document_id": str(document.id),
                "generation_id": str(superseded_generation.id),
                "revision_set_id": str(approved_set.id),
                "chunk_ids": [str(superseded_chunk.id)],
            },
            confidence=0.99,
            reviewer_state="approved",
            conflict_state="none",
        ),
        "wrong_patient": ClinicalTimelineEvent(
            patient_id=PATIENT_ALICE_ID,
            event_type="wrong_patient_event",
            clinical_date=datetime(2026, 1, 3, tzinfo=UTC),
            recorded_date=datetime(2026, 1, 4, tzinfo=UTC),
            source_evidence={"document_id": str(document.id), "chunk_ids": [str(wrong_patient_chunk.id)]},
            confidence=0.99,
            reviewer_state="approved",
            conflict_state="none",
        ),
    }
    session.add_all(list(event_rows.values()))
    await session.commit()

    return {
        "session": session,
        "doctor": doctor,
        "document": document,
        "active_chunk": active_chunk,
        "superseded_chunk": superseded_chunk,
        "wrong_patient_chunk": wrong_patient_chunk,
        "active_entity": active_entity,
        "events": event_rows,
    }


@pytest.mark.asyncio
async def test_all_cdi_read_paths_share_active_evidence_scope(cross_path_data) -> None:
    data = cross_path_data
    session = data["session"]
    document = data["document"]
    doctor = data["doctor"]

    retrieval = await RetrievalService(session).hybrid_search(
        user_id=doctor.id,
        patient_id=PATIENT_ALICE_ID,
        query_text="evidence",
        query_embedding=[0.1] * 1024,
        top_k=20,
        retrieval_mode="hybrid",
    )
    assert {item.chunk_id for item in retrieval} == {data["active_chunk"].id}

    graph = await GraphQueryService(session).document_graph(
        document,
        doctor,
        GraphFilters(min_confidence=0.8, entity_types=("medication",)),
    )
    assert {item["normalized_label"] for item in graph.mentions} == {"active medication"}
    assert len(graph.assertions) == 1

    timeline = await ClinicalTimelineService(session).document_timeline(document, doctor, {})
    assert [event["event_type"] for event in timeline["events"]] == ["active_event"]

    graph_context = await find_related_entities(
        session,
        ["active medication"],
        max_hops=2,
        patient_id=PATIENT_ALICE_ID,
    )
    assert graph_context.related_chunk_ids == {data["active_chunk"].id}

    chat_evidence = await RetrievalService(session).get_chunks_by_ids(
        [data["active_chunk"].id, data["superseded_chunk"].id, data["wrong_patient_chunk"].id],
        user_id=doctor.id,
        patient_id=PATIENT_ALICE_ID,
    )
    assert {item.chunk_id for item in chat_evidence} == {data["active_chunk"].id}


@pytest.mark.asyncio
async def test_superseded_scope_is_explicit_and_still_patient_bound(cross_path_data) -> None:
    data = cross_path_data
    session = data["session"]
    document = data["document"]
    doctor = data["doctor"]

    audit_chunk_ids = await ActiveEvidenceScope(session).authorized_chunk_id_set(
        user_id=doctor.id,
        patient_id=PATIENT_ALICE_ID,
        document_ids=(document.id,),
        include_superseded=True,
    )
    assert audit_chunk_ids == {data["active_chunk"].id, data["superseded_chunk"].id}

    graph = await GraphQueryService(session).document_graph(
        document,
        doctor,
        GraphFilters(include_superseded=True, min_confidence=0.8),
    )
    assert {item["normalized_label"] for item in graph.mentions} == {
        "active medication",
        "superseded medication",
    }
