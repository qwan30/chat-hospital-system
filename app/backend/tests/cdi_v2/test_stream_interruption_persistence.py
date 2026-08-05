from __future__ import annotations

import asyncio
import json
import uuid

import pytest
from sqlalchemy import select

from hospital_ai.api.routes.chat_stream import (
    StreamCompletion,
    _apply_stream_completion,
    _ensure_stream_terminal,
    _generate_sse_events,
)
from hospital_ai.core.config import Settings
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import AiQuery, AuditLog, User
from hospital_ai.services.retrieval import RetrievedChunk


async def test_interrupted_stream_persists_sequence_and_validation_mode(session_and_settings) -> None:
    session, _settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    assert doctor is not None
    query = AiQuery(
        user_id=doctor.id,
        patient_id=PATIENT_ALICE_ID,
        question="What is the patient status?",
        status="streaming",
        model="stub",
    )
    session.add(query)
    await session.flush()

    await _apply_stream_completion(
        session,
        ai_query_id=query.id,
        user_id=doctor.id,
        patient_id=PATIENT_ALICE_ID,
        thread_id=None,
        question=query.question,
        evidence=[],
        retrieval_mode="vector",
        trace_id="trace-interrupted",
        ip_address="127.0.0.1",
        started=0.0,
        completion=StreamCompletion(
            validation_status="failed",
            answer="Patient is stable ",
            failure_reason="disconnected",
            last_emitted_sequence=3,
            validation_mode="sentence_buffered",
        ),
    )
    await session.commit()

    refreshed = await session.get(AiQuery, query.id)
    assert refreshed is not None
    assert refreshed.status == "interrupted"
    assert refreshed.last_emitted_sequence == 3
    assert refreshed.validation_mode == "sentence_buffered"
    audit = (
        await session.execute(select(AuditLog).where(AuditLog.action == "chat.stream", AuditLog.object_id == query.id))
    ).scalar_one()
    assert audit.meta["reason"] == "disconnected"


async def test_terminal_guard_passes_last_sequence_to_persistence_callback() -> None:
    completions: list[StreamCompletion] = []

    async def capture(completion: StreamCompletion) -> None:
        completions.append(completion)

    state = {"finished": False, "last_emitted_sequence": 4, "validation_mode": "sentence_buffered"}
    await _ensure_stream_terminal(state, capture)

    assert completions[0].failure_reason == "disconnected"
    assert completions[0].last_emitted_sequence == 4
    assert completions[0].validation_mode == "sentence_buffered"


@pytest.mark.asyncio
async def test_cancellation_after_validated_sequence_does_not_emit_raw_fragment(monkeypatch) -> None:
    class CancellingLlm:
        async def stream(self, _messages):
            yield "Patient is stable [E1]. "
            yield "raw fragment that must stay private"
            raise asyncio.CancelledError()

        def model_name(self) -> str:
            return "cancelling-test"

    monkeypatch.setattr(
        "hospital_ai.api.routes.chat_stream.LLMManager",
        lambda _settings: type("Manager", (), {"get": lambda self: CancellingLlm()})(),
    )
    evidence = [
        RetrievedChunk(
            evidence_id="E1",
            document_id=uuid.uuid4(),
            document_title="Synthetic source",
            page=1,
            chunk_id=uuid.uuid4(),
            score=0.9,
            content="Patient is stable",
            metadata={},
        )
    ]
    state = {
        "finished": False,
        "last_emitted_sequence": 0,
        "validation_mode": "sentence_buffered",
        "answer": "",
    }
    completions: list[StreamCompletion] = []

    async def capture(completion: StreamCompletion) -> None:
        completions.append(completion)

    events: list[dict] = []
    with pytest.raises(asyncio.CancelledError):
        async for raw in _generate_sse_events(
            settings=Settings(
                database_url="sqlite+aiosqlite:///:memory:",
                chat_provider="stub",
                embedding_provider="deterministic",
                evidence_threshold=0.0,
            ),
            question="What is the status?",
            evidence=evidence,
            conversation_history=[],
            query_id=uuid.uuid4(),
            pipeline_name="simple_qa",
            on_complete=capture,
            stream_state=state,
        ):
            events.append(json.loads(raw.removeprefix("data: ").strip()))

    assert any(event["type"] == "token" for event in events)
    assert "raw fragment that must stay private" not in json.dumps(events)
    assert len(completions) == 1
    assert completions[0].failure_reason == "cancelled"
    assert completions[0].last_emitted_sequence == state["last_emitted_sequence"] > 0
