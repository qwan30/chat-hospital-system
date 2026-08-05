"""Regression tests for codebase-audit-2026-05 fixes.

Covers:
- F-RAG-002: hybrid-mode evidence threshold uses underlying retriever scores.
- F-RAG-001: SSE streaming rejects answers with hallucinated citations.
- F-SEC-004: SSE error events do not leak raw exception strings to the client.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Optional

import pytest

from hospital_ai.api.routes.chat_stream import StreamCompletion, _ensure_stream_terminal, _generate_sse_events
from hospital_ai.core.config import Settings
from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.services.chat import SAFE_PHI_LEAK_BLOCKED_ANSWER
from hospital_ai.services.chat_utils import meets_evidence_threshold
from hospital_ai.services.guardrails import GuardrailResult
from hospital_ai.services.llm.base import BaseLLM, LLMMessage, LLMResponse
from hospital_ai.services.retrieval import RetrievedChunk


@pytest.mark.asyncio
async def test_stream_background_finalizes_disconnect_before_first_token():
    completions: list[StreamCompletion] = []

    async def capture(completion: StreamCompletion) -> None:
        completions.append(completion)

    state = {"finished": False}
    await _ensure_stream_terminal(state, capture)

    assert len(completions) == 1
    assert completions[0].validation_status == "failed"
    assert completions[0].failure_reason == "disconnected"


@pytest.mark.asyncio
async def test_stream_background_does_not_finalize_completed_stream_twice():
    completions: list[StreamCompletion] = []

    async def capture(completion: StreamCompletion) -> None:
        completions.append(completion)

    await _ensure_stream_terminal({"finished": True}, capture)

    assert completions == []


# ── F-SEC-001: dev bearer tokens guarded by environment ─────────────────


def test_token_user_map_returns_default_in_local_environment(monkeypatch):
    monkeypatch.delenv("HOSPITAL_AI_DEV_BEARER_TOKENS", raising=False)
    settings = Settings(environment="local", _env_file=None)
    mapping = settings.token_user_map
    assert mapping.get("dev-doctor") == "doctor@example.test"
    assert mapping.get("dev-admin") == "admin@example.test"


def test_token_user_map_refuses_default_in_production(monkeypatch):
    """The committed default tokens must not be honored in non-local
    environments unless an operator explicitly opts in by setting the
    HOSPITAL_AI_DEV_BEARER_TOKENS env-var."""
    monkeypatch.delenv("HOSPITAL_AI_DEV_BEARER_TOKENS", raising=False)
    settings = Settings(environment="production", _env_file=None)
    assert settings.token_user_map == {}


def test_token_user_map_accepts_explicit_override_in_production(monkeypatch):
    """An explicit override (even if it equals the default text) is treated
    as an operator-authored value and is honored in any environment."""
    monkeypatch.delenv("HOSPITAL_AI_DEV_BEARER_TOKENS", raising=False)
    settings = Settings(
        environment="production",
        dev_bearer_tokens="ops-token:ops@example.test",
        _env_file=None,
    )
    assert settings.token_user_map == {"ops-token": "ops@example.test"}


# ── F-RAG-002: threshold helper unit tests ───────────────────────────────


def _chunk(score: float, **metadata) -> RetrievedChunk:
    return RetrievedChunk(
        evidence_id="E1",
        document_id=uuid.uuid4(),
        document_title="Doc",
        page=1,
        chunk_id=uuid.uuid4(),
        score=score,
        content="content",
        metadata=metadata,
    )


def test_threshold_vector_mode_uses_direct_score():
    assert meets_evidence_threshold(_chunk(0.5), "vector", 0.2) is True
    assert meets_evidence_threshold(_chunk(0.1), "vector", 0.2) is False


def test_threshold_bm25_mode_uses_direct_score():
    assert meets_evidence_threshold(_chunk(0.5), "bm25", 0.2) is True
    assert meets_evidence_threshold(_chunk(0.05), "bm25", 0.2) is False


def test_threshold_hybrid_mode_uses_underlying_scores_not_rrf():
    """RRF scores are tiny by construction; we must not compare them to the
    vector-scale threshold. The helper must look at score_list_* metadata
    preserved by reciprocal_rank_fusion()."""
    rrf_score = 0.033
    hybrid_chunk = _chunk(
        rrf_score,
        score_list_0=0.85,  # vector retriever original score
        score_list_1=0.40,  # bm25 retriever original score
        retrieval_method="hybrid_rrf",
    )
    assert meets_evidence_threshold(hybrid_chunk, "hybrid", 0.2) is True


def test_threshold_hybrid_mode_rejects_when_all_underlying_below_threshold():
    hybrid_chunk = _chunk(
        0.033,
        score_list_0=0.10,
        score_list_1=0.05,
        retrieval_method="hybrid_rrf",
    )
    assert meets_evidence_threshold(hybrid_chunk, "hybrid", 0.2) is False


def test_threshold_hybrid_mode_without_score_list_metadata_uses_nonzero_fallback():
    chunk = _chunk(0.001)
    assert meets_evidence_threshold(chunk, "hybrid", 0.2) is True
    chunk_zero = _chunk(0.0)
    assert meets_evidence_threshold(chunk_zero, "hybrid", 0.2) is False


# ── F-RAG-001 + F-SEC-004: streaming SSE behavior ────────────────────────


class _FakeLLM(BaseLLM):
    """Test double LLM returning a scripted answer via stream()."""

    def __init__(self, answer: str, model: str = "fake") -> None:
        self._answer = answer
        self._model = model

    def provider_name(self) -> str:
        return "fake"

    def model_name(self) -> str:
        return self._model

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        return LLMResponse(text=self._answer, model=self._model, finish_reason="stop")

    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        for word in self._answer.split(" "):
            yield word + " "


class _RaisingLLM(_FakeLLM):
    """Test double whose stream() raises an internal error mid-way."""

    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        # Yield nothing; the internal error must be sanitized before reaching client.
        if False:  # pragma: no cover - generator type stub
            yield ""
        raise RuntimeError("internal_traceback_with_secret_path /var/secret/path/private.txt")


def _settings() -> Settings:
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        chat_provider="stub",
        embedding_provider="deterministic",
        evidence_threshold=0.0,
    )


def _make_evidence(ids: list[str]) -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            evidence_id=eid,
            document_id=uuid.uuid4(),
            document_title=f"Doc {eid}",
            page=1,
            chunk_id=uuid.uuid4(),
            score=0.9,
            content=f"Content for {eid}. The dose is per protocol. Grounded answer.",
            metadata={},
        )
        for eid in ids
    ]


async def _collect(generator) -> list[dict]:
    events: list[dict] = []
    async for raw in generator:
        # Each SSE event line is "data: {json}\n\n"
        prefix = "data: "
        assert raw.startswith(prefix), raw
        body = raw[len(prefix) :].strip()
        events.append(json.loads(body))
    return events


@pytest.mark.asyncio
async def test_streaming_rejects_answer_with_hallucinated_citation(monkeypatch):
    """F-RAG-001: an answer that cites [E99] must never reach the client.

    Allowed evidence is E1, E2. The fake LLM emits a citation [E99]. The
    generator must emit a safe-refusal token and a done event with
    validation=failed, and MUST NOT emit any token containing E99 or the
    fabricated answer text."""
    fake = _FakeLLM(answer="Hallucinated claim [E99].")
    monkeypatch.setattr(
        "hospital_ai.api.routes.chat_stream.LLMManager",
        lambda settings: type("M", (), {"get": lambda self: fake})(),
    )

    events = await _collect(
        _generate_sse_events(
            settings=_settings(),
            question="What is the dose?",
            evidence=_make_evidence(["E1", "E2"]),
            conversation_history=[],
            query_id=uuid.uuid4(),
            pipeline_name="simple_qa",
        )
    )

    assert len(events) == 2, events
    refusal, done = events
    assert refusal["type"] == "token"
    assert "could not find authorized evidence" in refusal["content"].lower()
    # Fabricated content must not appear in the refusal.
    assert "Hallucinated" not in refusal["content"]
    assert "E99" not in refusal["content"]
    assert done["type"] == "done"
    assert done["validation"] == "failed"
    assert done["reason"] == "invalid_citation"


@pytest.mark.asyncio
async def test_streaming_emits_only_cited_evidence_when_validated(monkeypatch):
    """F-RAG-001: when citations validate, the citations event must list
    only the chunks the LLM cited, not all retrieved evidence."""
    fake = _FakeLLM(answer="The dose is per protocol [E1].")
    monkeypatch.setattr(
        "hospital_ai.api.routes.chat_stream.LLMManager",
        lambda settings: type("M", (), {"get": lambda self: fake})(),
    )

    events = await _collect(
        _generate_sse_events(
            settings=_settings(),
            question="What is the dose?",
            evidence=_make_evidence(["E1", "E2", "E3"]),
            conversation_history=[],
            query_id=uuid.uuid4(),
            pipeline_name="simple_qa",
        )
    )

    citation_events = [e for e in events if e["type"] == "citations"]
    assert len(citation_events) == 1
    cited_ids = [c["evidence_id"] for c in citation_events[0]["data"]]
    assert cited_ids == ["E1"], cited_ids

    done_events = [e for e in events if e["type"] == "done"]
    assert done_events and done_events[-1]["validation"] == "passed"


@pytest.mark.asyncio
async def test_streaming_output_guardrail_replaces_unsafe_buffer_before_emission(monkeypatch):
    unsafe_answer = "Secret patient detail must not leave the server [E1]."
    fake = _FakeLLM(answer=unsafe_answer)
    completed = []

    class BlockingOutputGuardrail:
        async def scan(self, prompt, output):
            assert prompt == "What is the dose?"
            assert output == unsafe_answer + " "
            return GuardrailResult(blocked=True, reason="detected PHI")

    monkeypatch.setattr(
        "hospital_ai.api.routes.chat_stream.LLMManager",
        lambda settings: type("M", (), {"get": lambda self: fake})(),
    )
    monkeypatch.setattr(
        "hospital_ai.api.routes.chat_stream.get_output_guardrail",
        lambda: BlockingOutputGuardrail(),
    )

    async def capture_completion(completion):
        completed.append(completion)

    events = await _collect(
        _generate_sse_events(
            settings=_settings(),
            question="What is the dose?",
            evidence=_make_evidence(["E1"]),
            conversation_history=[],
            query_id=uuid.uuid4(),
            pipeline_name="simple_qa",
            on_complete=capture_completion,
        )
    )

    assert [event["type"] for event in events] == ["token", "done"]
    assert events[0]["content"] == SAFE_PHI_LEAK_BLOCKED_ANSWER
    assert unsafe_answer not in json.dumps(events)
    assert events[1]["validation"] == "failed"
    assert events[1]["reason"] == "output_guardrail_blocked"
    assert len(completed) == 1
    assert completed[0].answer == SAFE_PHI_LEAK_BLOCKED_ANSWER
    assert completed[0].failure_reason == "output_guardrail_blocked"


@pytest.mark.asyncio
async def test_streaming_output_guardrail_also_blocks_chitchat_before_emission(monkeypatch):
    unsafe_answer = "Secret patient detail from casual chat."
    fake = _FakeLLM(answer=unsafe_answer)

    class BlockingOutputGuardrail:
        async def scan(self, _prompt, output):
            assert unsafe_answer in output
            return GuardrailResult(blocked=True, reason="detected PHI")

    monkeypatch.setattr(
        "hospital_ai.api.routes.chat_stream.LLMManager",
        lambda settings: type("M", (), {"get": lambda self: fake})(),
    )
    monkeypatch.setattr(
        "hospital_ai.api.routes.chat_stream.get_output_guardrail",
        lambda: BlockingOutputGuardrail(),
    )

    events = await _collect(
        _generate_sse_events(
            settings=_settings().copy(update={"chat_provider": "ollama"}),
            question="Hello",
            evidence=[],
            conversation_history=[],
            query_id=uuid.uuid4(),
            pipeline_name="chitchat",
        )
    )

    assert [event["type"] for event in events] == ["token", "done"]
    assert events[0]["content"] == SAFE_PHI_LEAK_BLOCKED_ANSWER
    assert unsafe_answer not in json.dumps(events)


# ── F-RAG-004 / demo-readiness: stream completion persists thread state ─


@pytest.mark.asyncio
async def test_apply_stream_completion_persists_thread_messages_on_success(session_and_settings):
    """A successful streaming answer must persist `ChatMessage` user +
    assistant rows so the conversation survives a page reload."""
    from sqlalchemy import select

    from hospital_ai.api.routes.chat_stream import (
        StreamCompletion,
        _apply_stream_completion,
    )
    from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
    from hospital_ai.db.models import (
        AiQuery,
        AuditLog,
        ChatMessage,
        ChatThread,
        DocumentChunk,
        RetrievedEvidence,
        User,
    )
    from tests.conftest import create_indexed_document

    session, _ = session_and_settings

    doctor = await session.get(User, DOCTOR_ID)
    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Stream-persist Test Doc",
        content="The protocol is to monitor vitals every 4 hours.",
    )
    uncited_doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Uncited Stream-persist Test Doc",
        content="This retrieved chunk is not cited by the answer.",
    )
    chunk = (await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))).scalar_one()
    uncited_chunk = (
        await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == uncited_doc.id))
    ).scalar_one()

    thread = ChatThread(
        title="Stream-persist test thread",
        scope="patient-linked",
        visibility="private",
        status="active",
        owner_user_id=doctor.id,
        patient_id=PATIENT_ALICE_ID,
        created_trace_id="trace-test-stream-persist",
    )
    session.add(thread)
    await session.flush()

    ai_query = AiQuery(
        user_id=doctor.id,
        patient_id=PATIENT_ALICE_ID,
        question="What is the monitoring protocol?",
        status="streaming",
        model="stub",
    )
    session.add(ai_query)
    await session.flush()

    evidence = [
        RetrievedChunk(
            evidence_id="E1",
            document_id=doc.id,
            document_title=doc.title,
            page=1,
            chunk_id=chunk.id,
            score=0.9,
            content=chunk.content,
            metadata={"retrieval_method": "vector"},
        ),
        RetrievedChunk(
            evidence_id="E2",
            document_id=uncited_doc.id,
            document_title=uncited_doc.title,
            page=1,
            chunk_id=uncited_chunk.id,
            score=0.8,
            content=uncited_chunk.content,
            metadata={"retrieval_method": "vector"},
        ),
    ]

    await _apply_stream_completion(
        session,
        ai_query_id=ai_query.id,
        user_id=doctor.id,
        patient_id=PATIENT_ALICE_ID,
        thread_id=thread.id,
        question="What is the monitoring protocol?",
        evidence=evidence,
        retrieval_mode="vector",
        trace_id="trace-test-stream-persist",
        ip_address="127.0.0.1",
        started=0.0,
        completion=StreamCompletion(
            validation_status="passed",
            answer="Monitor vitals every 4 hours [E1].",
            cited_evidence=[evidence[0]],
            citations_payload=[
                {
                    "evidence_id": "E1",
                    "document_id": str(doc.id),
                    "document_title": doc.title,
                    "page": 1,
                    "score": 0.9,
                    "content": chunk.content[:200],
                }
            ],
            confidence="high",
        ),
    )
    await session.commit()

    # AiQuery updated.
    refreshed = await session.get(AiQuery, ai_query.id)
    assert refreshed.status == "completed"
    assert "Monitor vitals" in refreshed.answer

    # RetrievedEvidence row persisted for rag_trace.
    rev_rows = (
        (await session.execute(select(RetrievedEvidence).where(RetrievedEvidence.ai_query_id == ai_query.id)))
        .scalars()
        .all()
    )
    assert [row.citation_label for row in rev_rows] == ["E1"]
    assert rev_rows[0].retrieval_method == "vector"

    # ChatMessage user + assistant rows present so reload preserves the thread.
    msgs = (
        (
            await session.execute(
                select(ChatMessage).where(ChatMessage.thread_id == thread.id).order_by(ChatMessage.created_at)
            )
        )
        .scalars()
        .all()
    )
    assert [m.role for m in msgs] == ["user", "assistant"]
    assert msgs[0].content == "What is the monitoring protocol?"
    assert "Monitor vitals" in msgs[1].content
    assert msgs[1].citations and msgs[1].citations[0]["evidence_id"] == "E1"
    assert msgs[1].meta.get("streaming") is True
    assert msgs[1].meta.get("validation") == "passed"

    # Thread last_message_at advanced.
    refreshed_thread = await session.get(ChatThread, thread.id)
    assert refreshed_thread.last_message_at is not None

    # chat.stream audit recorded.
    audit_rows = (
        (
            await session.execute(
                select(AuditLog).where(
                    AuditLog.action == "chat.stream",
                    AuditLog.object_id == ai_query.id,
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(audit_rows) == 1
    assert audit_rows[0].outcome == "allowed"


@pytest.mark.asyncio
async def test_apply_stream_completion_records_failure_for_invalid_citation(session_and_settings):
    """A validation-failed completion must be persisted with status=failed
    and a safe-refusal answer, so audit and rag_trace stay consistent."""
    from sqlalchemy import select

    from hospital_ai.api.routes.chat_stream import (
        StreamCompletion,
        _apply_stream_completion,
    )
    from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
    from hospital_ai.db.models import AiQuery, AuditLog, User

    session, _ = session_and_settings

    doctor = await session.get(User, DOCTOR_ID)
    ai_query = AiQuery(
        user_id=doctor.id,
        patient_id=PATIENT_ALICE_ID,
        question="Q?",
        status="streaming",
        model="stub",
    )
    session.add(ai_query)
    await session.flush()

    await _apply_stream_completion(
        session,
        ai_query_id=ai_query.id,
        user_id=doctor.id,
        patient_id=PATIENT_ALICE_ID,
        thread_id=None,
        question="Q?",
        evidence=[],
        retrieval_mode="vector",
        trace_id="trace-fail",
        ip_address="127.0.0.1",
        started=0.0,
        completion=StreamCompletion(
            validation_status="failed",
            answer="I could not find authorized evidence.",
            cited_evidence=[],
            citations_payload=[],
            confidence="low",
        ),
    )
    await session.commit()

    refreshed = await session.get(AiQuery, ai_query.id)
    assert refreshed.status == "failed"

    audit_row = (
        await session.execute(
            select(AuditLog).where(
                AuditLog.action == "chat.stream",
                AuditLog.object_id == ai_query.id,
            )
        )
    ).scalar_one()
    assert audit_row.outcome == "failed"
    assert audit_row.meta["validation"] == "failed"


@pytest.mark.asyncio
async def test_streaming_error_event_does_not_leak_exception_string(monkeypatch):
    """F-SEC-004: an internal exception during streaming must produce a
    sanitized error event with a generic message, not the raw str(exc)."""
    raising = _RaisingLLM(answer="")
    monkeypatch.setattr(
        "hospital_ai.api.routes.chat_stream.LLMManager",
        lambda settings: type("M", (), {"get": lambda self: raising})(),
    )

    events = await _collect(
        _generate_sse_events(
            settings=_settings(),
            question="Q?",
            evidence=_make_evidence(["E1"]),
            conversation_history=[],
            query_id=uuid.uuid4(),
            pipeline_name="simple_qa",
        )
    )

    assert len(events) == 1
    err = events[0]
    assert err["type"] == "error"
    assert err["code"] == "INTERNAL_ERROR"
    assert "secret_path" not in json.dumps(err)
    assert "private.txt" not in json.dumps(err)
    assert err["message"] == "Stream failed due to an internal error."


@pytest.mark.asyncio
async def test_streaming_external_service_error_uses_fixed_safe_message(monkeypatch):
    class ExternalFailureLlm(_FakeLLM):
        async def stream(self, messages, *, temperature=0.0, max_tokens=None):
            if False:
                yield ""
            raise ExternalServiceError("secret provider detail")

    monkeypatch.setattr(
        "hospital_ai.api.routes.chat_stream.LLMManager",
        lambda settings: type("M", (), {"get": lambda self: ExternalFailureLlm(answer="")})(),
    )

    events = await _collect(
        _generate_sse_events(
            settings=_settings(),
            question="Q?",
            evidence=_make_evidence(["E1"]),
            conversation_history=[],
            query_id=uuid.uuid4(),
            pipeline_name="simple_qa",
        )
    )

    assert events == [
        {
            "type": "error",
            "code": "EXTERNAL_SERVICE_ERROR",
            "message": "Stream failed because an external service was unavailable.",
        }
    ]
    assert "secret provider detail" not in json.dumps(events)


@pytest.mark.asyncio
async def test_streaming_reports_simple_pipeline_when_it_does_not_execute_requested_pipeline(monkeypatch):
    fake = _FakeLLM(answer="Grounded answer [E1].")
    monkeypatch.setattr(
        "hospital_ai.api.routes.chat_stream.LLMManager",
        lambda settings: type("M", (), {"get": lambda self: fake})(),
    )
    events = await _collect(
        _generate_sse_events(
            settings=_settings(),
            question="Q?",
            evidence=_make_evidence(["E1"]),
            conversation_history=[],
            query_id=uuid.uuid4(),
            pipeline_name="decompose",
        )
    )
    assert next(event for event in events if event["type"] == "metadata")["pipeline"] == "simple_qa"


@pytest.mark.asyncio
async def test_streaming_completion_failure_emits_error_without_done(monkeypatch):
    fake = _FakeLLM(answer="Grounded answer [E1].")

    async def failing_completion(_completion):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        "hospital_ai.api.routes.chat_stream.LLMManager",
        lambda settings: type("M", (), {"get": lambda self: fake})(),
    )

    events = await _collect(
        _generate_sse_events(
            settings=_settings(),
            question="Q?",
            evidence=_make_evidence(["E1"]),
            conversation_history=[],
            query_id=uuid.uuid4(),
            pipeline_name="simple_qa",
            on_complete=failing_completion,
        )
    )

    assert not [event for event in events if event["type"] == "done"]
    assert events[-1] == {
        "type": "error",
        "code": "INTERNAL_ERROR",
        "message": "Stream failed due to an internal error.",
    }


# ── F-RAG-003: graph-RAG patient isolation ───────────────────────────────


@pytest.mark.asyncio
async def test_find_related_entities_isolates_results_by_patient(session_and_settings):
    """`find_related_entities` must not surface entities, relations, or
    chunk ids sourced from a different patient's documents when called
    with `patient_id=...`.  Cross-patient drug names like 'metformin' or
    'aspirin' must stay scoped to their owner."""
    from sqlalchemy import select

    from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID
    from hospital_ai.db.models import DocumentChunk
    from hospital_ai.services.graph_rag import find_related_entities, index_chunk_entities
    from tests.conftest import create_indexed_document

    session, _ = session_and_settings

    alice_doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice chart",
        content="The patient takes metformin for diabetes management.",
    )
    bob_doc = await create_indexed_document(
        session,
        patient_id=PATIENT_BOB_ID,
        uploaded_by=DOCTOR_ID,
        title="Bob chart",
        content="The patient takes metformin and aspirin for hypertension.",
    )

    alice_chunk = (
        await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == alice_doc.id))
    ).scalar_one()
    bob_chunk = (
        await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == bob_doc.id))
    ).scalar_one()

    await index_chunk_entities(
        session,
        chunk_id=alice_chunk.id,
        document_id=alice_doc.id,
        content=alice_chunk.content,
    )
    await index_chunk_entities(
        session,
        chunk_id=bob_chunk.id,
        document_id=bob_doc.id,
        content=bob_chunk.content,
    )
    await session.commit()

    # Alice-scoped query returns only Alice's chunks.
    alice_ctx = await find_related_entities(session, ["metformin"], patient_id=PATIENT_ALICE_ID)
    assert alice_chunk.id in alice_ctx.related_chunk_ids
    assert bob_chunk.id not in alice_ctx.related_chunk_ids
    # Bob's "aspirin" must not show up in Alice's entity list.
    alice_entity_names = {e.name for e in alice_ctx.entities}
    assert "aspirin" not in alice_entity_names

    # Bob-scoped query returns Bob's chunks (which include aspirin) and
    # NOT Alice's chunk.
    bob_ctx = await find_related_entities(session, ["metformin"], patient_id=PATIENT_BOB_ID)
    assert bob_chunk.id in bob_ctx.related_chunk_ids
    assert alice_chunk.id not in bob_ctx.related_chunk_ids
    bob_entity_names = {e.name for e in bob_ctx.entities}
    assert "aspirin" in bob_entity_names


# ── F-RAG-005: service-boundary citation defense ─────────────────────────


@pytest.mark.asyncio
async def test_chat_service_rejects_invalid_citations_at_service_boundary(session_and_settings, monkeypatch):
    """Even if a hypothetical pipeline forgot to validate, the
    ChatService.answer service boundary must reject answers whose
    citations are not in the retrieved evidence set."""
    from hospital_ai.core.errors import ExternalServiceError
    from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
    from hospital_ai.db.models import User
    from hospital_ai.services.chat import ChatService
    from hospital_ai.services.reasoning import DISCLAIMER, ReasoningResult
    from tests.conftest import create_indexed_document

    session, settings = session_and_settings

    doctor = await session.get(User, DOCTOR_ID)
    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice protocol",
        content="The standard antibiotic course completed successfully.",
    )

    # Force `_run_pipeline` to return an answer that cites a chunk id that
    # does not exist in the retrieved evidence.  This simulates a future
    # pipeline that skips internal citation validation.
    async def _fake_pipeline(self, _name, _question, _evidence, _history):
        return ReasoningResult(
            answer="Forbidden claim from outside the evidence [E99].",
            citations=[],
            confidence="low",
            disclaimer=DISCLAIMER,
            pipeline="simple_qa",
        )

    monkeypatch.setattr(ChatService, "_run_pipeline", _fake_pipeline)

    with pytest.raises(ExternalServiceError):
        await ChatService(session, settings).answer(
            user=doctor,
            patient_id=PATIENT_ALICE_ID,
            question="What is the protocol?",
            top_k=3,
            trace_id="trace-defense",
            ip_address="127.0.0.1",
        )
