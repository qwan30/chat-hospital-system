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
from hospital_ai.db.clinical_graph import GraphEntity, GraphMention
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage, User
from hospital_ai.services.clinical_timeline import ClinicalTimelineService
from hospital_ai.services.graph_query import GraphFilters, GraphQueryService
from hospital_ai.services.retrieval import RetrievalService


@pytest.fixture
async def session(session_and_settings):
    session, _ = session_and_settings
    return session


@pytest.fixture
async def matrix_data(session):
    doctor = await session.get(User, DOCTOR_ID)
    if not doctor:
        doctor = User(
            id=uuid.uuid4(), email="matrix_doc@test.com", full_name="Matrix Doc", role="doctor", is_active=True
        )
        session.add(doctor)
        await session.commit()

    doc = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id,
        title="Matrix Doc",
        document_type="progress_note",
        storage_uri="local://test/matrix.pdf",
        mime_type="application/pdf",
        status="ready",
    )
    session.add(doc)
    await session.flush()

    page = DocumentPage(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_number=1,
        ocr_text="active superseded wrong_patient deleted unapproved",
        ocr_confidence=1.0,
    )
    session.add(page)
    await session.flush()

    def make_rev_set(status, rev_num):
        rs = DocumentRevisionSet(
            id=uuid.uuid4(),
            document_id=doc.id,
            revision_number=rev_num,
            status=status,
            created_by_user_id=doctor.id,
            submitted_at=datetime.now(UTC),
        )
        session.add(rs)
        return rs

    def make_gen(rs_id, state):
        gen = DocumentIndexGeneration(
            id=uuid.uuid4(),
            document_id=doc.id,
            revision_set_id=rs_id,
            state=state,
            revision_set_sha256="hash" * 16,
            generation_sha256="hash" * 16,
        )
        session.add(gen)
        return gen

    def make_page_rev(status):
        pr = DocumentPageRevision(
            id=uuid.uuid4(),
            document_id=doc.id,
            page_number=1,
            revision_number=1,
            revision_type="machine_ocr",
            raw_text_snapshot="txt",
            corrected_text="txt",
            confidence=1.0,
            status=status,
            created_by_user_id=doctor.id,
            content_sha256="hash" * 16,
            version=1,
        )
        session.add(pr)
        return pr

    active_rs = make_rev_set("approved", 1)
    unapproved_rs = make_rev_set("submitted", 2)

    active_gen = make_gen(active_rs.id, "active")
    superseded_gen = make_gen(active_rs.id, "superseded")

    doc.approved_revision_set_id = active_rs.id
    doc.active_index_generation_id = active_gen.id

    approved_pr = make_page_rev("approved")
    unapproved_pr = make_page_rev("submitted")
    await session.flush()

    def make_chunk(patient_id, gen_id, rs_id, pr_id, idx, is_deleted=False, content="content"):
        chunk = DocumentChunk(
            id=uuid.uuid4(),
            document_id=doc.id,
            page_id=page.id,
            patient_id=patient_id,
            chunk_index=idx,
            content=content,
            embedding=[0.1] * 1024,
            generation_id=gen_id,
            revision_set_id=rs_id,
            page_revision_id=pr_id,
            approval_state="approved",
            deleted_at=datetime.now(UTC) if is_deleted else None,
        )
        session.add(chunk)
        return chunk

    c_active = make_chunk(
        PATIENT_ALICE_ID, active_gen.id, active_rs.id, approved_pr.id, 0, content="active chunk matches"
    )
    c_superseded = make_chunk(
        PATIENT_ALICE_ID, superseded_gen.id, active_rs.id, approved_pr.id, 1, content="superseded chunk matches"
    )
    c_wrong_pat = make_chunk(
        PATIENT_BOB_ID, active_gen.id, active_rs.id, approved_pr.id, 2, content="wrong patient chunk matches"
    )
    c_deleted = make_chunk(
        PATIENT_ALICE_ID,
        active_gen.id,
        active_rs.id,
        approved_pr.id,
        3,
        is_deleted=True,
        content="deleted chunk matches",
    )
    c_unapproved = make_chunk(
        PATIENT_ALICE_ID, active_gen.id, unapproved_rs.id, unapproved_pr.id, 4, content="unapproved chunk matches"
    )
    await session.flush()

    # Graph Mentions
    entity = GraphEntity(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        entity_type="Disease",
        normalized_label="matrix disease",
        lifecycle_status="active",
    )
    session.add(entity)
    await session.flush()

    def make_mention(chunk, pat_id):
        m = GraphMention(
            id=uuid.uuid4(),
            patient_id=pat_id,
            document_id=chunk.document_id,
            chunk_id=chunk.id,
            entity_id=entity.id,
            generation_id=chunk.generation_id,
            revision_set_id=chunk.revision_set_id,
            page_revision_id=chunk.page_revision_id,
            independent_source_identity=f"mention-{chunk.id}",
        )
        session.add(m)
        return m

    make_mention(c_active, PATIENT_ALICE_ID)
    make_mention(c_superseded, PATIENT_ALICE_ID)
    make_mention(c_wrong_pat, PATIENT_BOB_ID)
    make_mention(c_deleted, PATIENT_ALICE_ID)
    make_mention(c_unapproved, PATIENT_ALICE_ID)

    # Timeline Events
    def make_event(chunk, pat_id):
        evt = ClinicalTimelineEvent(
            id=uuid.uuid4(),
            patient_id=pat_id,
            event_type="test",
            clinical_date=datetime.now(UTC),
            recorded_date=datetime.now(UTC),
            source_evidence={
                "document_id": str(chunk.document_id),
                "chunk_id": str(chunk.id),
                "generation_id": str(chunk.generation_id),
                "revision_set_id": str(chunk.revision_set_id),
            },
        )
        session.add(evt)
        return evt

    make_event(c_active, PATIENT_ALICE_ID)
    make_event(c_superseded, PATIENT_ALICE_ID)
    make_event(c_wrong_pat, PATIENT_BOB_ID)
    make_event(c_deleted, PATIENT_ALICE_ID)
    make_event(c_unapproved, PATIENT_ALICE_ID)

    await session.commit()
    return doc, c_active


@pytest.mark.asyncio
async def test_cross_path_matrix_shared_scope(session, matrix_data, session_and_settings) -> None:
    doc, c_active = matrix_data
    doctor = await session.get(User, DOCTOR_ID)

    # 1. Lexical BM25
    bm25_res = await RetrievalService(session).hybrid_search(
        user_id=doctor.id,
        patient_id=PATIENT_ALICE_ID,
        query="matches",
        query_embedding=[0.1] * 1024,
        top_k=10,
        mode="bm25",
    )
    assert [c.chunk_id for c in bm25_res] == [c_active.id]

    # 2. Vector
    vec_res = await RetrievalService(session).hybrid_search(
        user_id=doctor.id,
        patient_id=PATIENT_ALICE_ID,
        query="matches",
        query_embedding=[0.1] * 1024,
        top_k=10,
        mode="vector",
    )
    assert [c.chunk_id for c in vec_res] == [c_active.id]

    # 3. Graph
    graph_res = await GraphQueryService(session).document_graph(doc, doctor, GraphFilters())
    assert len(graph_res.mentions) == 1
    # Check that we didn't pick up the wrong-patient entity/mention or superseded

    # 4. Timeline
    timeline_res = await ClinicalTimelineService(session).document_timeline(doc, doctor, {})
    assert len(timeline_res["events"]) == 1
    assert timeline_res["events"][0]["evidence_ids"] == [str(c_active.id)]

    # 5. Chat
    from hospital_ai.services.chat import ChatService
    from hospital_ai.services.reasoning import ReasoningResult

    settings = session_and_settings[1]
    chat_svc = ChatService(session, settings)

    evidence_passed = []

    async def mock_run_pipeline(pipeline_name, question, evidence, conversation_history, evaluation_observer=None):
        evidence_passed.extend(evidence)
        cite = evidence[0].evidence_id if evidence else "N/A"
        return ReasoningResult(
            answer=f"Fake answer [{cite}]", citations=[], confidence="high", disclaimer="", pipeline="mock"
        )

    chat_svc._run_pipeline = mock_run_pipeline

    await chat_svc.answer(
        user=doctor,
        patient_id=PATIENT_ALICE_ID,
        question="matches",
        top_k=10,
        trace_id="test",
        ip_address="127.0.0.1",
    )

    assert [c.chunk_id for c in evidence_passed] == [c_active.id]
