"""Regression coverage for persisted citations emitted by the SSE chat route."""

import json
import uuid

import pytest
from sqlalchemy import select

from hospital_ai.api.routes.chat_stream import (
    _apply_stream_completion,
    _generate_sse_events,
)
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import AiQuery, ChatMessage, ChatThread, DocumentChunk, User
from hospital_ai.schemas.chat_threads import ChatMessageRead
from hospital_ai.schemas.documents import EvidenceRead
from hospital_ai.services.retrieval import RetrievedChunk
from tests.conftest import create_indexed_document


class _CitationLLM:
    def model_name(self) -> str:
        return "citation-contract-test"

    async def stream(self, messages):
        yield "The patient record states a stable condition [E1]."


async def _collect_sse_events(generator) -> list[dict]:
    events = []
    async for raw in generator:
        events.append(json.loads(raw.removeprefix("data: ").strip()))
    return events


@pytest.mark.asyncio
async def test_stream_citation_persists_with_chunk_id_and_validates_as_chat_message(
    session_and_settings,
    monkeypatch,
):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    document = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Stream citation contract note",
        content="The patient record states a stable condition.",
    )
    chunk = (await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document.id))).scalar_one()
    thread = ChatThread(
        title="Stream citation contract",
        scope="patient-linked",
        visibility="private",
        status="active",
        owner_user_id=doctor.id,
        patient_id=PATIENT_ALICE_ID,
        created_trace_id="trace-stream-citation-contract",
    )
    session.add(thread)
    query = AiQuery(
        user_id=doctor.id,
        patient_id=PATIENT_ALICE_ID,
        question="What is the patient condition?",
        status="streaming",
        model="stub",
    )
    session.add(query)
    await session.flush()

    evidence = [
        RetrievedChunk(
            evidence_id="E1",
            document_id=document.id,
            document_title=document.title,
            page=1,
            chunk_id=chunk.id,
            score=0.9,
            content=chunk.content,
            metadata={"retrieval_method": "vector"},
        )
    ]
    completed = []

    async def capture_completion(completion):
        completed.append(completion)

    monkeypatch.setattr(
        "hospital_ai.api.routes.chat_stream.LLMManager",
        lambda _settings: type("Manager", (), {"get": lambda _self: _CitationLLM()})(),
    )
    events = await _collect_sse_events(
        _generate_sse_events(
            settings=settings,
            question="What is the patient condition?",
            evidence=evidence,
            conversation_history=[],
            query_id=query.id,
            pipeline_name="simple_qa",
            on_complete=capture_completion,
        )
    )

    citation_event = next(event for event in events if event["type"] == "citations")
    await _apply_stream_completion(
        session,
        ai_query_id=query.id,
        user_id=doctor.id,
        patient_id=PATIENT_ALICE_ID,
        thread_id=thread.id,
        question="What is the patient condition?",
        evidence=evidence,
        retrieval_mode="vector",
        trace_id="trace-stream-citation-contract",
        ip_address="127.0.0.1",
        started=0.0,
        completion=completed[0],
    )
    await session.commit()

    assistant = (
        await session.execute(
            select(ChatMessage).where(ChatMessage.thread_id == thread.id, ChatMessage.role == "assistant")
        )
    ).scalar_one()
    citation = EvidenceRead.parse_obj(citation_event["data"][0])
    response_message = ChatMessageRead.from_orm(assistant)

    assert citation.chunk_id == chunk.id
    assert response_message.citations[0].chunk_id == chunk.id
    assert response_message.citations[0].document_id == document.id
    assert response_message.citations[0].evidence_id == "E1"
    assert uuid.UUID(assistant.citations[0]["chunk_id"]) == chunk.id
