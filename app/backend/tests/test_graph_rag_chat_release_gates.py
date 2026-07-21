"""Synthetic release-gate contracts for Graph RAG and chat transports."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker
from starlette.requests import Request

from hospital_ai.api.routes.chat_stream import chat_stream
from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID
from hospital_ai.db.models import (
    AiQuery,
    AuditLog,
    DocumentChunk,
    DocumentPage,
    PatientPermission,
    RetrievedEvidence,
    User,
)
from hospital_ai.schemas.chat import ChatRequest
from hospital_ai.services.chat import SAFE_NO_EVIDENCE_ANSWER, SAFE_PHI_LEAK_BLOCKED_ANSWER, ChatService
from hospital_ai.services.graph_rag import (
    ExtractedEntity,
    ExtractedRelation,
    GraphContext,
    GraphEntity,
    GraphRelation,
    find_related_entities,
    index_chunk_entities,
)
from hospital_ai.services.guardrails import GuardrailResult
from hospital_ai.services.reasoning import DISCLAIMER, ReasoningResult
from hospital_ai.services.retrieval import RetrievalService, RetrievedChunk
from tests.conftest import create_indexed_document


async def _chunk(session, document_id: uuid.UUID) -> DocumentChunk:
    return (await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id))).scalar_one()


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/chat/stream",
            "headers": [],
            "client": ("10.10.10.10", 50000),
        }
    )


async def _events(response) -> list[dict]:
    body = ""
    async for item in response.body_iterator:
        body += item.decode("utf-8") if isinstance(item, bytes) else item
    return [json.loads(part.strip()[6:]) for part in body.split("\n\n") if part.strip().startswith("data: ")]


@pytest.mark.asyncio
async def test_graph_relation_scope_returns_exact_patient_chunk_set(session_and_settings):
    session, _ = session_and_settings
    alice_doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice metformin",
        content="Metformin treats diabetes.",
    )
    bob_doc = await create_indexed_document(
        session,
        patient_id=PATIENT_BOB_ID,
        uploaded_by=DOCTOR_ID,
        title="Bob metformin",
        content="Metformin treats diabetes.",
    )
    alice_chunk, bob_chunk = await _chunk(session, alice_doc.id), await _chunk(session, bob_doc.id)
    await index_chunk_entities(session, alice_chunk.id, alice_doc.id, alice_chunk.content)
    await index_chunk_entities(session, bob_chunk.id, bob_doc.id, bob_chunk.content)
    await session.commit()
    alice = await find_related_entities(session, ["metformin"], patient_id=PATIENT_ALICE_ID)
    bob = await find_related_entities(session, ["metformin"], patient_id=PATIENT_BOB_ID)
    assert alice.related_chunk_ids == {alice_chunk.id}
    assert bob.related_chunk_ids == {bob_chunk.id}


@pytest.mark.asyncio
async def test_graph_traversal_excludes_soft_deleted_page_sources(session_and_settings):
    session, _ = session_and_settings
    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Deleted graph",
        content="Metformin treats diabetes.",
    )
    chunk = await _chunk(session, doc.id)
    await index_chunk_entities(session, chunk.id, doc.id, chunk.content)
    page = await session.get(DocumentPage, chunk.page_id)
    assert page is not None
    page.deleted_at = func.now()
    await session.commit()
    assert (await find_related_entities(session, ["metformin"], patient_id=PATIENT_ALICE_ID)).related_chunk_ids == set()


@pytest.mark.asyncio
async def test_graph_reindex_replaces_prior_rows_for_the_chunk(session_and_settings):
    session, _ = session_and_settings
    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Reindex graph",
        content="Metformin treats diabetes.",
    )
    chunk = await _chunk(session, doc.id)
    await index_chunk_entities(session, chunk.id, doc.id, chunk.content)
    await index_chunk_entities(session, chunk.id, doc.id, chunk.content)
    await session.commit()
    entities = await session.scalar(
        select(func.count()).select_from(GraphEntity).where(GraphEntity.source_chunk_id == chunk.id)
    )
    relations = await session.scalar(
        select(func.count()).select_from(GraphRelation).where(GraphRelation.source_chunk_id == chunk.id)
    )
    assert entities == 2
    assert relations == 1


@pytest.mark.asyncio
async def test_graph_evidence_fetch_excludes_soft_deleted_page(session_and_settings):
    session, _ = session_and_settings
    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Deleted page",
        content="Metformin treats diabetes.",
    )
    chunk = await _chunk(session, doc.id)
    page = await session.get(DocumentPage, chunk.page_id)
    assert page is not None
    page.deleted_at = func.now()
    await session.commit()
    evidence = await RetrievalService(session).get_chunks_by_ids(
        [chunk.id], user_id=DOCTOR_ID, patient_id=PATIENT_ALICE_ID
    )
    assert evidence == []


@pytest.mark.asyncio
async def test_graph_evidence_excludes_mismatched_document_patient(session_and_settings):
    session, _ = session_and_settings
    alice_doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice chunk",
        content="Alice evidence must retain its document ownership.",
    )
    bob_doc = await create_indexed_document(
        session,
        patient_id=PATIENT_BOB_ID,
        uploaded_by=DOCTOR_ID,
        title="Bob document",
        content="Bob evidence must remain isolated.",
    )
    chunk = await _chunk(session, alice_doc.id)
    await session.execute(
        update(DocumentChunk).where(DocumentChunk.id == chunk.id).values(document_id=bob_doc.id, chunk_index=1)
    )
    await session.commit()

    evidence = await RetrievalService(session).get_chunks_by_ids(
        [chunk.id], user_id=DOCTOR_ID, patient_id=PATIENT_ALICE_ID
    )

    assert evidence == []


@pytest.mark.asyncio
async def test_graph_evidence_excludes_mismatched_page_document(session_and_settings):
    session, _ = session_and_settings
    source_doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice source",
        content="Alice evidence must retain its page ownership.",
    )
    other_doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice other document",
        content="A different Alice document still cannot supply the page.",
    )
    chunk = await _chunk(session, source_doc.id)
    other_page = (
        await session.execute(select(DocumentPage).where(DocumentPage.document_id == other_doc.id))
    ).scalar_one()
    await session.execute(update(DocumentChunk).where(DocumentChunk.id == chunk.id).values(page_id=other_page.id))
    await session.commit()

    evidence = await RetrievalService(session).get_chunks_by_ids(
        [chunk.id], user_id=DOCTOR_ID, patient_id=PATIENT_ALICE_ID
    )

    assert evidence == []


@pytest.mark.asyncio
@pytest.mark.parametrize("deleted_layer", ["chunk", "document", "page"])
async def test_graph_evidence_excludes_soft_deleted_join_layer(session_and_settings, deleted_layer):
    session, _ = session_and_settings
    document = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title=f"Deleted {deleted_layer}",
        content=f"Evidence from a deleted {deleted_layer} must be excluded.",
    )
    chunk = await _chunk(session, document.id)
    page = await session.get(DocumentPage, chunk.page_id)
    assert page is not None
    deleted_rows = {"chunk": chunk, "document": document, "page": page}
    deleted_rows[deleted_layer].deleted_at = func.now()
    await session.commit()

    evidence = await RetrievalService(session).get_chunks_by_ids(
        [chunk.id], user_id=DOCTOR_ID, patient_id=PATIENT_ALICE_ID
    )

    assert evidence == []


@pytest.mark.asyncio
@pytest.mark.parametrize("permission_state", ["revoked", "expired"])
async def test_graph_evidence_excludes_inactive_permission(session_and_settings, permission_state):
    session, _ = session_and_settings
    document = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title=f"{permission_state.title()} permission",
        content="Evidence requires an active accepted permission.",
    )
    chunk = await _chunk(session, document.id)
    inactive_value = (
        {"deleted_at": datetime.now(UTC)}
        if permission_state == "revoked"
        else {"expires_at": datetime.now(UTC) - timedelta(minutes=1)}
    )
    await session.execute(
        update(PatientPermission)
        .where(
            PatientPermission.user_id == DOCTOR_ID,
            PatientPermission.patient_id == PATIENT_ALICE_ID,
        )
        .values(**inactive_value)
    )
    await session.commit()

    evidence = await RetrievalService(session).get_chunks_by_ids(
        [chunk.id], user_id=DOCTOR_ID, patient_id=PATIENT_ALICE_ID
    )

    assert evidence == []


@pytest.mark.asyncio
async def test_chat_service_rejects_answer_without_citation(session_and_settings, monkeypatch):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Citation note",
        content="Metformin treats diabetes.",
    )

    async def uncited(self, _pipeline, _question, _evidence, _history):
        return ReasoningResult(
            answer="Metformin treats diabetes.",
            citations=[],
            confidence="high",
            disclaimer=DISCLAIMER,
            pipeline="simple_qa",
        )

    monkeypatch.setattr(ChatService, "_run_pipeline", uncited)
    with pytest.raises(ExternalServiceError):
        await ChatService(session, settings).answer(
            user=doctor,
            patient_id=PATIENT_ALICE_ID,
            question="What does metformin treat?",
            top_k=1,
            trace_id="uncited",
            ip_address="127.0.0.1",
        )


@pytest.mark.asyncio
async def test_graph_enrichment_respects_top_k(session_and_settings, monkeypatch):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    semantic_doc = await create_indexed_document(
        session, patient_id=PATIENT_ALICE_ID, uploaded_by=DOCTOR_ID, title="Semantic", content="Metformin is listed."
    )
    graph_doc = await create_indexed_document(
        session, patient_id=PATIENT_ALICE_ID, uploaded_by=DOCTOR_ID, title="Graph", content="Metformin treats diabetes."
    )
    semantic, graph = await _chunk(session, semantic_doc.id), await _chunk(session, graph_doc.id)

    async def semantic_hit(self, **_kwargs):
        return [
            RetrievedChunk(
                "E1",
                semantic_doc.id,
                semantic_doc.title,
                1,
                semantic.id,
                0.9,
                semantic.content,
                {"retrieval_method": "vector"},
            )
        ]

    async def entities(_question):
        return [ExtractedEntity("metformin", "drug")], []

    async def graph_context(*_args, **_kwargs):
        return GraphContext([ExtractedEntity("metformin", "drug")], [], {graph.id}, "graph evidence")

    async def answer(self, _pipeline, _question, _evidence, _history):
        return ReasoningResult("Metformin is listed [E1].", [], "high", DISCLAIMER, "simple_qa")

    monkeypatch.setattr(RetrievalService, "search", semantic_hit)
    monkeypatch.setattr("hospital_ai.services.chat.extract_entities_and_relations_nlp", entities)
    monkeypatch.setattr("hospital_ai.services.chat.find_related_entities", graph_context)
    monkeypatch.setattr(ChatService, "_run_pipeline", answer)
    response = await ChatService(session, settings).answer(
        user=doctor,
        patient_id=PATIENT_ALICE_ID,
        question="What does metformin treat?",
        top_k=1,
        trace_id="top-k",
        ip_address="127.0.0.1",
    )
    rows = (
        (await session.execute(select(RetrievedEvidence).where(RetrievedEvidence.ai_query_id == response.query_id)))
        .scalars()
        .all()
    )
    assert len(rows) <= 1


@pytest.mark.asyncio
async def test_stream_and_nonstream_share_graph_only_evidence_contract(session_and_settings, monkeypatch):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Graph only",
        content="Metformin treats diabetes.",
    )
    chunk = await _chunk(session, doc.id)

    async def no_semantic(self, **_kwargs):
        return []

    async def entities(_question):
        return [ExtractedEntity("metformin", "drug")], []

    async def graph_context(*_args, **_kwargs):
        return GraphContext(
            [ExtractedEntity("metformin", "drug")],
            [ExtractedRelation("metformin", "diabetes", "treats")],
            {chunk.id},
            "graph evidence",
        )

    async def answer(self, _pipeline, _question, _evidence, _history):
        return ReasoningResult("Metformin treats diabetes [G1].", [], "high", DISCLAIMER, "simple_qa")

    monkeypatch.setattr(RetrievalService, "search", no_semantic)
    monkeypatch.setattr("hospital_ai.services.chat.extract_entities_and_relations_nlp", entities)
    monkeypatch.setattr("hospital_ai.services.chat.find_related_entities", graph_context)
    monkeypatch.setattr(ChatService, "_run_pipeline", answer)
    nonstream = await ChatService(session, settings).answer(
        user=doctor,
        patient_id=PATIENT_ALICE_ID,
        question="What does metformin treat?",
        top_k=1,
        trace_id="graph-only",
        ip_address="127.0.0.1",
    )
    trace = (
        (await session.execute(select(RetrievedEvidence).where(RetrievedEvidence.ai_query_id == nonstream.query_id)))
        .scalars()
        .all()
    )
    assert [row.retrieval_method for row in trace] == ["graph"]

    class GraphOnlyLlm:
        async def stream(self, _messages):
            yield "Metformin treats diabetes [G1]."

        def model_name(self):
            return "graph-test"

    monkeypatch.setattr(
        "hospital_ai.api.routes.chat_stream.LLMManager",
        lambda _settings: type("Manager", (), {"get": lambda self: GraphOnlyLlm()})(),
    )
    stream = await chat_stream(
        payload=ChatRequest(patient_id=PATIENT_ALICE_ID, question="What does metformin treat?", top_k=1),
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )
    events = await _events(stream)
    token_text = "".join(event.get("content", "") for event in events if event.get("type") == "token")
    assert SAFE_NO_EVIDENCE_ANSWER not in token_text
    citation_events = [event for event in events if event.get("type") == "citations"]
    assert [citation["evidence_id"] for citation in citation_events[0]["data"]] == ["G1"]
    done_events = [event for event in events if event.get("type") == "done"]
    assert done_events[-1]["validation"] == "passed"
    assert not [event for event in events if event.get("type") == "error"]


@pytest.mark.asyncio
async def test_stream_output_guardrail_persists_refusal_terminal_state(session_and_settings, monkeypatch):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Guardrail source",
        content="Authorized clinical evidence.",
    )

    class UnsafeLlm:
        async def stream(self, _messages):
            yield "Secret generated PHI [E1]."

        def model_name(self):
            return "unsafe-test"

    class BlockingGuardrail:
        async def scan(self, _prompt, _output):
            return GuardrailResult(blocked=True, reason="detected PHI")

    monkeypatch.setattr(
        "hospital_ai.api.routes.chat_stream.LLMManager",
        lambda _settings: type("Manager", (), {"get": lambda self: UnsafeLlm()})(),
    )
    monkeypatch.setattr(
        "hospital_ai.api.routes.chat_stream.get_output_guardrail",
        lambda: BlockingGuardrail(),
    )
    monkeypatch.setattr(
        "hospital_ai.api.routes.chat_stream.get_session_factory",
        lambda: async_sessionmaker(session.bind, expire_on_commit=False),
    )

    response = await chat_stream(
        payload=ChatRequest(patient_id=PATIENT_ALICE_ID, question="What is in the record?", top_k=1),
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )
    events = await _events(response)

    assert [event["type"] for event in events] == ["token", "done"]
    assert events[0]["content"] == SAFE_PHI_LEAK_BLOCKED_ANSWER
    assert "Secret generated PHI" not in json.dumps(events)

    query = (await session.execute(select(AiQuery).order_by(AiQuery.created_at.desc()))).scalars().first()
    assert query is not None
    await session.refresh(query)
    assert query.status == "refused"
    assert query.answer == SAFE_PHI_LEAK_BLOCKED_ANSWER
    audit = (
        await session.execute(select(AuditLog).where(AuditLog.action == "chat.stream", AuditLog.object_id == query.id))
    ).scalar_one()
    assert audit.outcome == "denied"
    assert audit.meta["reason"] == "output_guardrail_blocked"
