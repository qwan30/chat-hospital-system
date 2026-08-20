"""Server-Sent Events (SSE) streaming endpoint for chat.

Provides token-by-token streaming responses using the LLM provider
abstraction layer, inspired by kotaemon's generator-based streaming.
"""

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.background import BackgroundTask

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.api.limiter import limiter
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.errors import AppError
from hospital_ai.core.security import PATIENT_READ_SCOPES, new_trace_id
from hospital_ai.db.models import AiQuery, ChatMessage, ChatThread, RetrievedEvidence, User
from hospital_ai.db.session import get_session_factory
from hospital_ai.schemas.chat import ChatRequest
from hospital_ai.services.audit import AuditService
from hospital_ai.services.chat import (
    PERMISSION_DENIED_CHAT_ANSWER,
    SAFE_INJECTION_DETECTED_ANSWER,
    SAFE_NO_EVIDENCE_ANSWER,
    SAFE_PHI_LEAK_BLOCKED_ANSWER,
    _select_pipeline,
    elapsed_ms,
)
from hospital_ai.services.chat_utils import (
    build_grounded_prompt,
    confidence_from_score,
    extract_citation_ids,
    is_chitchat_query,
    meets_evidence_threshold,
)
from hospital_ai.services.embeddings import EmbeddingService
from hospital_ai.services.guardrails import get_input_guardrail, get_output_guardrail
from hospital_ai.services.llm import LLMManager
from hospital_ai.services.llm.base import LLMMessage
from hospital_ai.services.memory import MemoryService
from hospital_ai.services.patient_resolver import PatientResolver
from hospital_ai.services.permissions import PermissionService
from hospital_ai.services.retrieval import RetrievalService, RetrievedChunk
from hospital_ai.services.validated_stream import ValidatedSentenceStreamer

logger = logging.getLogger(__name__)

router = APIRouter()


def _resolve_model_name(settings: Settings) -> str:
    if settings.chat_provider == "openai":
        return settings.openai_chat_model or "deepseek-chat"
    elif settings.chat_provider == "gemini":
        return settings.gemini_chat_model or "gemini-2.0-flash"
    elif settings.chat_provider == "ollama":
        return settings.chat_model or "medllama2"
    return "stub"


@dataclass
class StreamCompletion:
    """Final state of an SSE stream, handed to the on_complete callback.

    F-RAG-004 / demo-readiness fix: the route uses this payload to mirror
    the non-streaming `ChatService.answer` contract — persist the answer,
    evidence trace, audit row, and (when thread-bound) ChatMessage rows so
    that streamed answers survive a page reload.
    """

    validation_status: str  # "passed" | "failed"
    answer: str
    cited_evidence: list[Any] = field(default_factory=list)
    citations_payload: list[dict] = field(default_factory=list)
    confidence: str = "low"
    failure_reason: Optional[str] = None


OnCompleteCallback = Callable[[StreamCompletion], Awaitable[None]]
SAFE_EXTERNAL_SERVICE_ERROR_MESSAGE = "Stream failed because an external service was unavailable."


class _StreamPersistenceError(Exception):
    """Raised when a terminal stream outcome cannot be persisted."""


_REFUSAL_REASONS = {
    "input_guardrail_blocked",
    "output_guardrail_blocked",
    "missing_patient_read_scope",
    "permission_denied",
    "no_evidence",
}
_DENIED_REASONS = {
    "input_guardrail_blocked",
    "output_guardrail_blocked",
    "missing_patient_read_scope",
    "permission_denied",
}


def _stream_terminal_status(completion: StreamCompletion) -> str:
    if completion.failure_reason in _REFUSAL_REASONS:
        return "refused"
    if completion.validation_status == "passed":
        return "completed"
    return "failed"


def _stream_audit_outcome(completion: StreamCompletion) -> str:
    if completion.failure_reason in _DENIED_REASONS:
        return "denied"
    if _stream_terminal_status(completion) == "failed":
        return "failed"
    return "allowed"


async def _finalize_stream_outcome(
    session: AsyncSession,
    *,
    ai_query: AiQuery,
    completion: StreamCompletion,
    user_id: UUID,
    patient_id: Optional[UUID],
    trace_id: str,
    ip_address: Optional[str],
    started: float,
    evidence_count: int,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """Persist the terminal query and matching audit outcome exactly once."""
    ai_query.answer = completion.answer
    ai_query.status = _stream_terminal_status(completion)
    ai_query.latency_ms = elapsed_ms(started)
    audit_metadata = {
        "result": ai_query.status,
        "evidence_count": evidence_count,
        "validation": completion.validation_status,
        "reason": completion.failure_reason,
    }
    audit_metadata.update(metadata or {})
    await AuditService(session).record(
        actor_user_id=user_id,
        action="chat.stream",
        object_type="ai_query",
        object_id=ai_query.id,
        patient_id=patient_id,
        outcome=_stream_audit_outcome(completion),
        trace_id=trace_id,
        ip_address=ip_address,
        metadata=audit_metadata,
    )


async def _complete_stream(
    on_complete: Optional[OnCompleteCallback],
    completion: StreamCompletion,
) -> None:
    if on_complete is None:
        return
    try:
        await on_complete(completion)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        raise _StreamPersistenceError from exc


async def _best_effort_failed_completion(
    on_complete: Optional[OnCompleteCallback],
    *,
    failure_reason: str,
) -> None:
    if on_complete is None:
        return
    try:
        await on_complete(
            StreamCompletion(
                validation_status="failed",
                answer="",
                cited_evidence=[],
                citations_payload=[],
                confidence="low",
                failure_reason=failure_reason,
            )
        )
    except BaseException:
        logger.exception("Failed to persist terminal stream state reason=%s", failure_reason)


async def _safe_refusal_stream(
    *,
    answer: str,
    query_id: UUID,
    reason: str,
    model: str,
) -> AsyncIterator[str]:
    """Emit a safe refusal using the validated SSE contract."""
    events = (
        {"type": "status", "stage": "retrieving"},
        {
            "type": "metadata",
            "confidence": "low",
            "pipeline": "simple_qa",
            "model": model,
            "validation_mode": "sentence_buffered",
        },
        {
            "type": "token",
            "content": answer,
            "sequence": 1,
            "validation_mode": "sentence_buffered",
        },
        {"type": "citations", "data": []},
        {
            "type": "done",
            "query_id": str(query_id),
            "validation": "failed",
            "reason": reason,
            "confidence": "low",
        },
    )
    for event in events:
        yield f"data: {json.dumps(event)}\n\n"


async def _generate_validated_sse_events(
    *,
    settings: Settings,
    question: str,
    evidence: list,
    conversation_history: list,
    query_id: UUID,
    on_complete: Optional[OnCompleteCallback],
    stream_state: dict[str, Any],
) -> AsyncIterator[str]:
    """Stream only sentence-validated output from the provider.

    The provider iterator is consumed by ``ValidatedSentenceStreamer``. Raw
    fragments never enter the SSE serializer; a complete sentence is either
    emitted after deterministic validation or replaced by a safe refusal.
    """
    completion_callback_active = False
    refused = False
    preamble: list[dict[str, Any]] = []
    preamble_emitted = False
    cited_evidence: list[Any] = []
    citations_payload: list[dict[str, Any]] = []

    stream_state.setdefault("last_emitted_sequence", 0)
    stream_state.setdefault("validation_mode", "sentence_buffered")
    stream_state.setdefault("answer", "")
    stream_state.setdefault("guardrail_blocked", False)

    async def complete_terminal(completion: StreamCompletion) -> None:
        nonlocal completion_callback_active
        completion_callback_active = True
        await _complete_stream(on_complete, completion)
        completion_callback_active = False

    def serialize(event: dict[str, Any]) -> str:
        return f"data: {json.dumps(event)}\n\n"

    async def sentence_guardrail(sentence: str) -> Optional[str]:
        result = await get_output_guardrail().scan(question, f"{sentence} ")
        if result.blocked:
            stream_state["guardrail_blocked"] = True
            return SAFE_PHI_LEAK_BLOCKED_ANSWER
        return None

    try:
        llm = LLMManager(settings).get()
        prompt = build_grounded_prompt(question, evidence, conversation_history)
        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are a clinical knowledge assistant. Answer accurately and concisely "
                    "based on the authorized evidence. Cite each factual claim with [E1] or [E2]."
                ),
            ),
            LLMMessage(role="user", content=prompt),
        ]
        evidence_by_id = {item.evidence_id: item.content for item in evidence}
        provisional_confidence = confidence_from_score(evidence[0].score) if evidence else "low"
        streamer = ValidatedSentenceStreamer()

        async for event in streamer.events(
            llm.stream(messages),
            evidence_by_id,
            None,
            sentence_guardrail=sentence_guardrail,
        ):
            if event.type == "status":
                preamble.append({"type": "status", "stage": event.content or "retrieving"})
                continue
            if event.type == "metadata":
                preamble.append(
                    {
                        "type": "metadata",
                        "confidence": provisional_confidence,
                        "pipeline": "simple_qa",
                        "model": llm.model_name(),
                        "validation_mode": "sentence_buffered",
                    }
                )
                continue
            if event.type == "token":
                validation_passed = event.validation_passed is not False
                if not validation_passed:
                    refused = True
                content = event.content or ""
                if not validation_passed:
                    content = (
                        SAFE_PHI_LEAK_BLOCKED_ANSWER if stream_state["guardrail_blocked"] else SAFE_NO_EVIDENCE_ANSWER
                    )
                stream_state["answer"] += content
                stream_state["last_emitted_sequence"] = event.sequence or stream_state["last_emitted_sequence"]
                stream_state["validation_mode"] = event.validation_mode or "sentence_buffered"
                if not preamble_emitted and validation_passed:
                    for item in preamble:
                        yield serialize(item)
                    preamble_emitted = True
                yield serialize(
                    {
                        "type": "token",
                        "content": content,
                        "sequence": event.sequence,
                        "validation_mode": event.validation_mode or "sentence_buffered",
                    }
                )
                continue
            if event.type == "citations":
                citation_ids = extract_citation_ids(stream_state["answer"])
                allowed_ids = set(evidence_by_id)
                if citation_ids and citation_ids.issubset(allowed_ids) and not refused:
                    cited_evidence = [item for item in evidence if item.evidence_id in citation_ids]
                    citations_payload = [
                        {
                            "evidence_id": item.evidence_id,
                            "document_id": str(item.document_id),
                            "document_title": item.document_title,
                            "page": item.page,
                            "chunk_id": str(item.chunk_id),
                            "score": item.score,
                            "content": item.content[:200],
                        }
                        for item in cited_evidence
                    ]
                    yield serialize({"type": "citations", "data": citations_payload})
                else:
                    refused = True
                continue
            if event.type == "graph_explanation":
                if not refused:
                    yield serialize({"type": "graph_explanation", "data": event.data or ""})
                continue
            if event.type == "done":
                if stream_state["guardrail_blocked"]:
                    completion = StreamCompletion(
                        validation_status="failed",
                        answer=SAFE_PHI_LEAK_BLOCKED_ANSWER,
                        cited_evidence=[],
                        citations_payload=[],
                        confidence="low",
                        failure_reason="output_guardrail_blocked",
                        validation_mode=stream_state["validation_mode"],
                        last_emitted_sequence=stream_state["last_emitted_sequence"],
                    )
                    validation = "failed"
                    reason = "output_guardrail_blocked"
                elif refused or not cited_evidence:
                    completion = StreamCompletion(
                        validation_status="failed",
                        answer=SAFE_NO_EVIDENCE_ANSWER,
                        cited_evidence=[],
                        citations_payload=[],
                        confidence="low",
                        failure_reason="invalid_citation",
                        validation_mode=stream_state["validation_mode"],
                        last_emitted_sequence=stream_state["last_emitted_sequence"],
                    )
                    validation = "failed"
                    reason = "invalid_citation"
                else:
                    avg_score = sum(item.score for item in cited_evidence) / len(cited_evidence)
                    confidence = confidence_from_score(avg_score)
                    completion = StreamCompletion(
                        validation_status="passed",
                        answer=stream_state["answer"],
                        cited_evidence=cited_evidence,
                        citations_payload=citations_payload,
                        confidence=confidence,
                        validation_mode=stream_state["validation_mode"],
                        last_emitted_sequence=stream_state["last_emitted_sequence"],
                    )
                    validation = "passed"
                    reason = None
                await complete_terminal(completion)
                done_event = {"type": "done", "query_id": str(query_id), "validation": validation}
                if reason is not None:
                    done_event["reason"] = reason
                yield serialize(done_event)
    except _StreamPersistenceError:
        logger.exception("SSE chat completion persistence failed query_id=%s", query_id)
        yield serialize(
            {
                "type": "error",
                "code": "INTERNAL_ERROR",
                "message": "Stream failed due to an internal error.",
            }
        )
    except asyncio.CancelledError:
        if not completion_callback_active:
            await _best_effort_failed_completion(
                on_complete,
                failure_reason="cancelled",
                answer=stream_state["answer"],
                last_emitted_sequence=stream_state["last_emitted_sequence"],
                validation_mode=stream_state["validation_mode"],
            )
        raise
    except AppError as exc:
        await _best_effort_failed_completion(
            on_complete,
            failure_reason="app_error",
            answer=stream_state["answer"],
            last_emitted_sequence=stream_state["last_emitted_sequence"],
            validation_mode=stream_state["validation_mode"],
        )
        yield serialize(
            {
                "type": "error",
                "code": exc.code,
                "message": SAFE_EXTERNAL_SERVICE_ERROR_MESSAGE,
            }
        )
    except Exception:
        logger.exception("SSE chat stream failed unexpectedly query_id=%s", query_id)
        await _best_effort_failed_completion(
            on_complete,
            failure_reason="internal_error",
            answer=stream_state["answer"],
            last_emitted_sequence=stream_state["last_emitted_sequence"],
            validation_mode=stream_state["validation_mode"],
        )
        yield serialize(
            {
                "type": "error",
                "code": "INTERNAL_ERROR",
                "message": "Stream failed due to an internal error.",
            }
        )


async def _generate_sse_events(
    *,
    settings: Settings,
    question: str,
    evidence: list,
    conversation_history: list,
    query_id: UUID,
    pipeline_name: str,
    resolved_patient: Optional[Any] = None,
    on_complete: Optional[OnCompleteCallback] = None,
) -> AsyncIterator[str]:
    """Generate SSE events with token-by-token streaming.

    Event format:
        data: {"type": "token", "content": "word", "sequence": 1,
               "validation_mode": "sentence_buffered"}
        data: {"type": "citations", "data": [...]}
        data: {"type": "done", "query_id": "..."}
        data: {"type": "error", "message": "..."}
    """
    completion_callback_active = False
    # This transport currently executes one grounded generation path.  Do not
    # claim a requested reasoning pipeline that was not actually run.
    actual_pipeline = "chitchat" if pipeline_name == "chitchat" else "simple_qa"

    if resolved_patient is not None:
        res_event = json.dumps(
            {
                "type": "context_resolved",
                "patient_id": str(resolved_patient.id),
                "mrn": resolved_patient.mrn,
                "full_name": resolved_patient.full_name,
            }
        )
        yield f"data: {res_event}\n\n"

    async def complete_terminal(completion: StreamCompletion) -> None:
        nonlocal completion_callback_active
        completion_callback_active = True
        await _complete_stream(on_complete, completion)
        completion_callback_active = False

    def serialize_token(content: str, sequence: int) -> str:
        event = json.dumps(
            {
                "type": "token",
                "content": content,
                "sequence": sequence,
                "validation_mode": "sentence_buffered",
            }
        )
        return f"data: {event}\n\n"

    async def emit_validated_statuses() -> AsyncIterator[str]:
        """Expose activity only after the answer has passed safety checks."""
        for stage in ("retrieving", "preparing_answer", "validating_citations"):
            event = json.dumps({"type": "status", "stage": stage})
            yield f"data: {event}\n\n"

    try:
        # Get LLM with streaming
        llm_manager = LLMManager(settings)
        llm = llm_manager.get()

        if pipeline_name == "chitchat":
            full_text = ""
            messages = [
                LLMMessage(
                    role="system",
                    content=(
                        "You are a friendly hospital knowledge assistant. "
                        "Since this is a greeting or general conversational query, "
                        "respond naturally and politely."
                    ),
                ),
                LLMMessage(role="user", content=question),
            ]
            if settings.chat_provider == "stub":
                lower_q = question.lower()
                if "xin chào" in lower_q or "chào" in lower_q or "hello" in lower_q or "hi" in lower_q:
                    full_text = "Xin chào! Tôi là trợ lý ảo HMS AI Copilot. Tôi có thể giúp gì cho bạn hôm nay?"
                elif "cảm ơn" in lower_q or "cám ơn" in lower_q or "thank" in lower_q or "thanks" in lower_q:
                    full_text = "Không có gì! Nếu bạn cần thêm thông tin gì khác, cứ hỏi tôi nhé."
                else:
                    full_text = "Tôi là HMS AI Copilot, trợ lý thông tin bệnh viện của bạn. Tôi có thể giúp gì cho bạn?"
            else:
                async for token in llm.stream(messages):
                    full_text += token

            output_result = await get_output_guardrail().scan(question, full_text)
            if output_result.blocked:
                yield serialize_token(SAFE_PHI_LEAK_BLOCKED_ANSWER, sequence=1)
                await complete_terminal(
                    StreamCompletion(
                        validation_status="failed",
                        answer=SAFE_PHI_LEAK_BLOCKED_ANSWER,
                        failure_reason="output_guardrail_blocked",
                    ),
                )
                done_event = json.dumps(
                    {
                        "type": "done",
                        "query_id": str(query_id),
                        "validation": "failed",
                        "reason": "output_guardrail_blocked",
                        "confidence": "low",
                    }
                )
                yield f"data: {done_event}\n\n"
                return

            async for status_event in emit_validated_statuses():
                yield status_event

            yield serialize_token(full_text, sequence=1)

            # Emit metadata, done, and run on_complete
            meta_event = json.dumps(
                {
                    "type": "metadata",
                    "confidence": "high",
                    "pipeline": "chitchat",
                    "model": llm.model_name(),
                    "validation_mode": "sentence_buffered",
                }
            )
            yield f"data: {meta_event}\n\n"
            await complete_terminal(
                StreamCompletion(
                    validation_status="passed",
                    answer=full_text,
                    cited_evidence=[],
                    citations_payload=[],
                    confidence="high",
                ),
            )
            complete_status = json.dumps({"type": "status", "stage": "complete"})
            yield f"data: {complete_status}\n\n"
            done_event = json.dumps(
                {
                    "type": "done",
                    "query_id": str(query_id),
                    "validation": "passed",
                }
            )
            yield f"data: {done_event}\n\n"
            return

        # Build prompt
        prompt = build_grounded_prompt(question, evidence, conversation_history)

        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are a clinical knowledge assistant. Answer accurately and concisely "
                    "based on the authorized evidence. Cite each factual claim with [E1] or [E2]."
                ),
            ),
            LLMMessage(role="user", content=prompt),
        ]

        # F-RAG-001: Buffer the LLM stream so we can validate citations
        # against the authorized evidence set BEFORE any token leaves the
        # server.  This trades token-level streaming UX for safety —
        # invalid citations must never reach the wire.
        full_text = ""
        async for token in llm.stream(messages):
            full_text += token

        output_result = await get_output_guardrail().scan(question, full_text)
        if output_result.blocked:
            logger.warning(
                "Streaming answer blocked by output guardrail query_id=%s reason=%s",
                query_id,
                output_result.reason,
            )
            yield serialize_token(SAFE_PHI_LEAK_BLOCKED_ANSWER, sequence=1)
            await complete_terminal(
                StreamCompletion(
                    validation_status="failed",
                    answer=SAFE_PHI_LEAK_BLOCKED_ANSWER,
                    cited_evidence=[],
                    citations_payload=[],
                    confidence="low",
                    failure_reason="output_guardrail_blocked",
                ),
            )
            done_event = json.dumps(
                {
                    "type": "done",
                    "query_id": str(query_id),
                    "validation": "failed",
                    "reason": "output_guardrail_blocked",
                    "confidence": "low",
                }
            )
            yield f"data: {done_event}\n\n"
            return

        citation_ids = extract_citation_ids(full_text)
        allowed_ids = {item.evidence_id for item in evidence}

        # Reject hallucinated citations: must have at least one citation,
        # and every cited id must correspond to a retrieved chunk.
        if not citation_ids or not citation_ids.issubset(allowed_ids):
            logger.warning(
                "Streaming answer rejected: citation_validation_failed query_id=%s citation_ids=%s allowed_ids=%s",
                query_id,
                sorted(citation_ids),
                sorted(allowed_ids),
            )
            yield serialize_token(SAFE_NO_EVIDENCE_ANSWER, sequence=1)
            await complete_terminal(
                StreamCompletion(
                    validation_status="failed",
                    answer=SAFE_NO_EVIDENCE_ANSWER,
                    cited_evidence=[],
                    citations_payload=[],
                    confidence="low",
                    failure_reason="invalid_citation",
                ),
            )
            done_event = json.dumps(
                {
                    "type": "done",
                    "query_id": str(query_id),
                    "validation": "failed",
                    "reason": "invalid_citation",
                    "confidence": "low",
                }
            )
            yield f"data: {done_event}\n\n"
            return

        async for status_event in emit_validated_statuses():
            yield status_event

        # Validated — emit the full answer as token events so existing
        # frontend parsers continue to accumulate the text.  Yield in
        # whitespace-preserving chunks to keep the streaming contract.
        for sequence, piece in enumerate(full_text.splitlines(keepends=True), start=1):
            if piece:
                yield serialize_token(piece, sequence=sequence)

        # Emit only evidence that was actually cited.
        cited_evidence = [item for item in evidence if item.evidence_id in citation_ids]
        citations = []
        for item in cited_evidence:
            citations.append(
                {
                    "evidence_id": item.evidence_id,
                    "document_id": str(item.document_id),
                    "document_title": item.document_title,
                    "page": item.page,
                    "chunk_id": str(item.chunk_id),
                    "score": item.score,
                    "content": item.content[:200],
                }
            )
        citation_event = json.dumps({"type": "citations", "data": citations})
        yield f"data: {citation_event}\n\n"

        # Confidence based on cited evidence (fall back to all evidence if
        # the LLM cited none — but we required citations above, so cited
        # is non-empty here).
        scoring_pool = cited_evidence or evidence
        avg_score = sum(e.score for e in scoring_pool) / len(scoring_pool) if scoring_pool else 0.0
        confidence = confidence_from_score(avg_score)
        meta_event = json.dumps(
            {
                "type": "metadata",
                "confidence": confidence,
                "pipeline": actual_pipeline,
                "model": llm.model_name(),
                "validation_mode": "sentence_buffered",
            }
        )
        yield f"data: {meta_event}\n\n"

        await complete_terminal(
            StreamCompletion(
                validation_status="passed",
                answer=full_text,
                cited_evidence=cited_evidence,
                citations_payload=citations,
                confidence=confidence,
            ),
        )
        complete_status = json.dumps({"type": "status", "stage": "complete"})
        yield f"data: {complete_status}\n\n"
        done_event = json.dumps(
            {
                "type": "done",
                "query_id": str(query_id),
                "validation": "passed",
            }
        )
        yield f"data: {done_event}\n\n"

    except _StreamPersistenceError:
        logger.exception("SSE chat completion persistence failed query_id=%s", query_id)
        error_event = json.dumps(
            {
                "type": "error",
                "code": "INTERNAL_ERROR",
                "message": "Stream failed due to an internal error.",
            }
        )
        yield f"data: {error_event}\n\n"
    except asyncio.CancelledError:
        if not completion_callback_active:
            await _best_effort_failed_completion(on_complete, failure_reason="cancelled")
        raise
    except AppError as exc:
        await _best_effort_failed_completion(on_complete, failure_reason="app_error")
        error_event = json.dumps(
            {
                "type": "error",
                "code": exc.code,
                "message": SAFE_EXTERNAL_SERVICE_ERROR_MESSAGE,
            }
        )
        yield f"data: {error_event}\n\n"
    except Exception:
        # F-SEC-004: Never leak internal exception strings to the client.
        # Log the full trace server-side, return a generic message.
        logger.exception("SSE chat stream failed unexpectedly query_id=%s", query_id)
        await _best_effort_failed_completion(on_complete, failure_reason="internal_error")
        error_event = json.dumps(
            {
                "type": "error",
                "code": "INTERNAL_ERROR",
                "message": "Stream failed due to an internal error.",
            }
        )
        yield f"data: {error_event}\n\n"


async def _apply_stream_completion(
    session: AsyncSession,
    *,
    ai_query_id: UUID,
    user_id: UUID,
    patient_id: Optional[UUID],
    thread_id: Optional[UUID],
    question: str,
    evidence: list,
    retrieval_mode: str,
    trace_id: str,
    ip_address: Optional[str],
    started: float,
    completion: StreamCompletion,
) -> None:
    """Apply stream-completion persistence to an open session.

    Mirrors `ChatService.answer` parity for the streaming path. Writes:
      - `AiQuery.answer` + status + latency
      - `RetrievedEvidence` rows for the rag-trace endpoint
      - `ChatMessage` user + assistant rows when `thread_id` is set so
        streamed conversations survive a page reload
      - A `chat.stream` audit entry mirroring the non-streaming `chat.ask`

    The caller is responsible for the surrounding session lifecycle and
    commit so this function is unit-testable with the project's in-memory
    test session.
    """
    ai_query = await session.get(AiQuery, ai_query_id)
    if ai_query is None:
        logger.warning("AiQuery missing during stream persistence id=%s", ai_query_id)
        return

    await _finalize_stream_outcome(
        session,
        ai_query=ai_query,
        completion=completion,
        user_id=user_id,
        patient_id=patient_id,
        trace_id=trace_id,
        ip_address=ip_address,
        started=started,
        evidence_count=len(completion.cited_evidence),
        metadata={"thread_id": str(thread_id) if thread_id else None},
    )

    for index, item in enumerate(completion.cited_evidence, start=1):
        method = (item.metadata or {}).get("retrieval_method", retrieval_mode)
        session.add(
            RetrievedEvidence(
                ai_query_id=ai_query.id,
                chunk_id=item.chunk_id,
                rank=index,
                score=item.score,
                citation_label=item.evidence_id,
                retrieval_method=method,
            )
        )

    if thread_id is not None:
        scope = "patient-linked" if patient_id is not None else "general"
        permission_state = "allowed" if patient_id is not None else "not-required"
        now = datetime.now(UTC)
        user_message = ChatMessage(
            thread_id=thread_id,
            sender_user_id=user_id,
            patient_id=patient_id,
            role="user",
            scope=scope,
            content=question,
            patient_permission_state=permission_state,
            citations=[],
            meta={"streaming": True},
            trace_id=trace_id,
            created_at=now,
        )
        assistant_message = ChatMessage(
            thread_id=thread_id,
            ai_query_id=ai_query.id,
            patient_id=patient_id,
            role="assistant",
            scope=scope,
            content=completion.answer,
            patient_permission_state=permission_state,
            citations=list(completion.citations_payload),
            meta={
                "streaming": True,
                "confidence": completion.confidence,
                "validation": completion.validation_status,
                "activity": (
                    [
                        {"stage": "retrieving"},
                        {"stage": "preparing_answer"},
                        {"stage": "validating_citations"},
                        {"stage": "complete"},
                    ]
                    if completion.validation_status == "passed"
                    else []
                ),
            },
            trace_id=trace_id,
            created_at=datetime.now(UTC),
        )
        session.add(user_message)
        session.add(assistant_message)

        thread = await session.get(ChatThread, thread_id)
        if thread is not None:
            thread.last_message_at = assistant_message.created_at

    if thread_id is not None and completion.validation_status == "passed":
        from hospital_ai.core.config import get_settings

        settings = get_settings()
        source_ids = [str(item.document_id) for item in completion.cited_evidence]
        await MemoryService(session, settings).update_session_memory(
            thread_id=thread_id,
            patient_id=patient_id,
            new_question=question,
            new_answer=completion.answer,
            source_ids=source_ids,
        )


async def _persist_stream_completion(
    session_factory: async_sessionmaker[AsyncSession],
    **kwargs,
) -> None:
    """Open a fresh session and persist stream completion.

    Used by the route's on_complete callback. The request-bound session
    may be closed by the time streaming finishes, so we open a new one.
    """
    async with session_factory() as session:
        await _apply_stream_completion(session, **kwargs)
        await session.commit()


async def _ensure_stream_terminal(
    completion_state: dict[str, bool],
    on_complete: OnCompleteCallback,
) -> None:
    """Finalize a stream whose body never reached its completion callback."""
    if completion_state["finished"]:
        return
    try:
        await on_complete(
            StreamCompletion(
                validation_status="failed",
                answer="",
                cited_evidence=[],
                citations_payload=[],
                confidence="low",
                failure_reason="disconnected",
            )
        )
    except BaseException:
        logger.exception("Unable to finalize an interrupted chat stream")


def _log_telemetry(
    settings: Settings,
    patient_id: Optional[UUID],
    evidence: Optional[list] = None,
    blocked_count: int = 0,
    failure_reason: Optional[str] = None,
) -> None:
    import hashlib

    pseudo_patient_id = hashlib.sha256(str(patient_id).encode()).hexdigest() if patient_id else None

    ev_list = evidence or []
    telemetry = {
        "pseudonymized_patient_id": pseudo_patient_id,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": settings.embedding_model,
        "candidates_before_role_filter": len(ev_list) + blocked_count,
        "blocked_by_role_filter": blocked_count,
        "candidates_after_role_filter": len(ev_list),
        "top_scores": [e.score for e in ev_list],
        "threshold": settings.evidence_threshold,
        "citation_failure_reason": failure_reason,
    }
    logger.info("Telemetry: %s", json.dumps(telemetry))


@router.post("/stream")
@limiter.limit("5/minute")
async def chat_stream(
    payload: ChatRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    """SSE streaming chat endpoint.

    Returns a text/event-stream response with token-by-token generation.
    """
    started = time.perf_counter()
    trace_id = new_trace_id()

    resolved_patient = None
    effective_patient_id = payload.patient_id or (payload.context.patient_id if payload.context else None)

    # Create AI query record early
    ai_query = AiQuery(
        user_id=current_user.id,
        patient_id=effective_patient_id,
        question=payload.question,
        status="received",
        model=_resolve_model_name(settings),
    )
    session.add(ai_query)
    await session.flush()

    if effective_patient_id is None:
        patient_res = await PatientResolver(session).resolve(payload.question, user=current_user)
        if patient_res.status == "single_match" and patient_res.patients:
            resolved_patient = patient_res.patients[0]
            effective_patient_id = resolved_patient.id
            ai_query.patient_id = effective_patient_id
            await session.flush()
        elif patient_res.status == "multiple_matches" and patient_res.patients:
            ai_query.status = "disambiguation_required"
            await session.flush()
            disam_event = {
                "type": "disambiguation_required",
                "matched_term": patient_res.matched_term,
                "candidates": [
                    {
                        "patient_id": str(p.id),
                        "patient_name": p.full_name,
                        "mrn": p.mrn,
                        "dob": p.dob,
                        "department": p.department,
                    }
                    for p in patient_res.patients
                ],
            }
            candidates = disam_event.get("candidates", [])
            lines = [
                f"{i + 1}. **{c['patient_name']}** (MRN: `{c['mrn']}`, Khoa: {c.get('department') or 'N/A'})"
                for i, c in enumerate(candidates)
            ]
            disam_msg = (
                f"Hệ thống tìm thấy **{len(candidates)} bệnh nhân** có tên tương tự trong hệ thống:\n\n"
                + "\n".join(lines)
                + "\n\nVui lòng chỉ định rõ mã MRN hoặc chọn hồ sơ bệnh nhân cụ thể."
            )

            async def disambiguation_stream() -> AsyncIterator[str]:
                yield f"data: {json.dumps(disam_event)}\n\n"
                token_event = {
                    "type": "token",
                    "content": disam_msg,
                    "sequence": 1,
                    "validation_mode": "sentence_buffered",
                }
                yield f"data: {json.dumps(token_event)}\n\n"
                meta_event = json.dumps(
                    {
                        "type": "metadata",
                        "confidence": "high",
                        "pipeline": "simple_qa",
                        "model": _resolve_model_name(settings),
                        "validation_mode": "sentence_buffered",
                    }
                )
                yield f"data: {meta_event}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'query_id': str(ai_query.id)})}\n\n"

            return StreamingResponse(disambiguation_stream(), media_type="text/event-stream")

    # Permission check
    if effective_patient_id:
        has_scope = await PermissionService(session).has_patient_scope(
            user_id=current_user.id,
            patient_id=effective_patient_id,
            accepted_scopes=PATIENT_READ_SCOPES,
        )
    else:
        has_scope = True

    if not has_scope:
        await _finalize_stream_outcome(
            session,
            ai_query=ai_query,
            completion=StreamCompletion(
                validation_status="failed",
                answer=PERMISSION_DENIED_CHAT_ANSWER,
                failure_reason="missing_patient_read_scope",
            ),
            user_id=current_user.id,
            patient_id=effective_patient_id,
            trace_id=trace_id,
            ip_address=get_request_ip(request),
            started=started,
            evidence_count=0,
        )
        await session.commit()

        _log_telemetry(settings=settings, patient_id=effective_patient_id, failure_reason="permission_denied")

        async def denied_stream() -> AsyncIterator[str]:
            event = json.dumps({"type": "error", "message": "User is not authorized for this patient."})
            yield f"data: {event}\n\n"

        return StreamingResponse(denied_stream(), media_type="text/event-stream")

    input_result = await get_input_guardrail().scan(payload.question)
    if input_result.blocked:
        await _finalize_stream_outcome(
            session,
            ai_query=ai_query,
            completion=StreamCompletion(
                validation_status="failed",
                answer=SAFE_INJECTION_DETECTED_ANSWER,
                failure_reason="input_guardrail_blocked",
            ),
            user_id=current_user.id,
            patient_id=effective_patient_id,
            trace_id=trace_id,
            ip_address=get_request_ip(request),
            started=started,
            evidence_count=0,
            metadata={"details": input_result.reason},
        )
        await session.commit()

        return StreamingResponse(
            _safe_refusal_stream(
                answer=SAFE_INJECTION_DETECTED_ANSWER,
                query_id=ai_query.id,
                reason="input_guardrail_blocked",
                model=settings.chat_model if settings.chat_provider == "ollama" else "stub",
            ),
            media_type="text/event-stream",
        )

    # Gather conversation history
    conversation_history: list = []
    if payload.thread_id:
        from hospital_ai.services.chat import ChatService

        svc = ChatService(session, settings)
        conversation_history = await svc._get_conversation_history(
            payload.thread_id, current_user.id, effective_patient_id
        )

    is_chitchat = is_chitchat_query(payload.question)

    blocked_chunk_count = 0
    if is_chitchat:
        evidence = []
        selected_pipeline = "chitchat"
        retrieval_mode = settings.retrieval_mode
    else:
        # Retrieve evidence (mirror chat.py mode dispatch).
        query_embedding = await EmbeddingService(settings).embed(payload.question)
        retrieval_svc = RetrievalService(session)
        retrieval_mode = settings.retrieval_mode
        hospital_wide = effective_patient_id is None
        if retrieval_mode in ("bm25", "hybrid"):
            evidence = await retrieval_svc.hybrid_search(
                user_id=current_user.id,
                patient_id=effective_patient_id,
                hospital_wide=hospital_wide,
                query_embedding=query_embedding,
                query_text=payload.question,
                top_k=payload.top_k,
                retrieval_mode=retrieval_mode,
            )
        else:
            evidence = await retrieval_svc.search(
                user_id=current_user.id,
                patient_id=effective_patient_id,
                hospital_wide=hospital_wide,
                query_embedding=query_embedding,
                top_k=payload.top_k,
            )

        # ── Graph RAG Enrichment ─────────────────────────────────────────────
        try:
            if effective_patient_id:
                from hospital_ai.services.bm25 import reciprocal_rank_fusion
                from hospital_ai.services.chat import extract_entities_and_relations_nlp, find_related_entities

                query_entities, _ = await extract_entities_and_relations_nlp(payload.question)
                if query_entities:
                    entity_names = [e.normalized_label for e in query_entities]
                    graph_ctx = await find_related_entities(
                        session, entity_names, max_hops=2, patient_id=effective_patient_id
                    )
                    if graph_ctx.related_chunk_ids:
                        graph_chunks = await retrieval_svc.get_chunks_by_ids(
                            list(graph_ctx.related_chunk_ids),
                            user_id=current_user.id,
                            patient_id=effective_patient_id,
                            hospital_wide=hospital_wide,
                        )
                        graph_evidence = [
                            RetrievedChunk(
                                evidence_id=ge.evidence_id,
                                document_id=ge.document_id,
                                document_title=ge.document_title,
                                page=ge.page,
                                chunk_id=ge.chunk_id,
                                score=ge.score,
                                content=ge.content,
                                metadata={**ge.metadata, "retrieval_method": "graph"},
                                patient_id=ge.patient_id,
                                generation_id=ge.generation_id,
                                revision_set_id=ge.revision_set_id,
                                page_revision_id=ge.page_revision_id,
                                active_index_generation_id=ge.active_index_generation_id,
                                approval_state=ge.approval_state,
                                retrieval_method="graph",
                                source_hash=ge.source_hash,
                                start_offset=ge.start_offset,
                                end_offset=ge.end_offset,
                                bounding_boxes=ge.bounding_boxes,
                            )
                            for ge in graph_chunks
                        ]
                        if evidence and graph_evidence:
                            evidence = reciprocal_rank_fusion(evidence, graph_evidence, top_k=payload.top_k)
                        elif graph_evidence:
                            evidence = graph_evidence[: payload.top_k]
        except Exception:
            logger.warning("Graph RAG enrichment skipped", exc_info=True)

        # A chat attachment is an explicit evidence scope, not merely a UI
        # hint.  Permission filtering still happens inside retrieval; this
        # additional allow-list ensures only the requested document can reach
        # prompt construction or the streamed citation payload.
        requested_document_ids = set(payload.context.document_ids or []) if payload.context else set()
        if requested_document_ids:
            evidence = [item for item in evidence if item.document_id in requested_document_ids]

        if hospital_wide and not evidence:
            from hospital_ai.services.general_knowledge import rank_general_knowledge

            gk_evidence = rank_general_knowledge(payload.question, payload.top_k)
            if gk_evidence:
                evidence = gk_evidence
        elif resolved_patient and not evidence:
            evidence = [
                RetrievedChunk(
                    evidence_id="E1",
                    document_id=resolved_patient.id,
                    document_title=f"Patient Profile: {resolved_patient.full_name}",
                    page=1,
                    chunk_id=resolved_patient.id,
                    score=0.95,
                    content=(
                        f"Patient Name: {resolved_patient.full_name}\n"
                        f"MRN: {resolved_patient.mrn}\n"
                        f"DOB: {resolved_patient.dob or 'N/A'}\n"
                        f"Department: {resolved_patient.department or 'N/A'}\n"
                        f"Status: {resolved_patient.status}"
                    ),
                    metadata={
                        "source_scope": "patient-profile",
                        "patient_id": str(resolved_patient.id),
                    },
                )
            ]

        blocked_chunk_count = retrieval_svc.blocked_chunk_count

        if not evidence or not meets_evidence_threshold(evidence[0], retrieval_mode, settings.evidence_threshold):
            is_blocked = blocked_chunk_count > 0
            answer_text = PERMISSION_DENIED_CHAT_ANSWER if is_blocked else SAFE_NO_EVIDENCE_ANSWER
            failure_reason = "permission_denied" if is_blocked else "no_evidence"
            completion = StreamCompletion(
                validation_status="failed",
                answer=answer_text,
                failure_reason=failure_reason,
            )
            await _finalize_stream_outcome(
                session,
                ai_query=ai_query,
                completion=completion,
                user_id=current_user.id,
                patient_id=effective_patient_id,
                trace_id=trace_id,
                ip_address=get_request_ip(request),
                started=started,
                evidence_count=0,
            )
            result_status = ai_query.status

            # Persist a thread message pair for the no-evidence outcome too,
            # otherwise the user sees an answer in the UI that vanishes on
            # reload.  Mirrors the parity contract above.
            if payload.thread_id is not None:
                scope = "patient-linked" if effective_patient_id is not None else "general"
                permission_state = "allowed" if effective_patient_id is not None else "not-required"
                now = datetime.now(UTC)
                session.add(
                    ChatMessage(
                        thread_id=payload.thread_id,
                        sender_user_id=current_user.id,
                        patient_id=effective_patient_id,
                        role="user",
                        scope=scope,
                        content=payload.question,
                        patient_permission_state=permission_state,
                        citations=[],
                        meta={"streaming": True},
                        trace_id=trace_id,
                        created_at=now,
                    )
                )
                session.add(
                    ChatMessage(
                        thread_id=payload.thread_id,
                        ai_query_id=ai_query.id,
                        patient_id=effective_patient_id,
                        role="assistant",
                        scope=scope,
                        content=answer_text,
                        patient_permission_state=permission_state if not is_blocked else "denied",
                        citations=[],
                        meta={"streaming": True, "result": result_status, "confidence": "low"},
                        trace_id=trace_id,
                        created_at=datetime.now(UTC),
                    )
                )
                thread = await session.get(ChatThread, payload.thread_id)
                if thread is not None:
                    thread.last_message_at = datetime.now(UTC)

            await session.commit()

            _log_telemetry(
                settings=settings,
                patient_id=effective_patient_id,
                evidence=evidence,
                blocked_count=blocked_chunk_count,
                failure_reason="denied" if is_blocked else "no_evidence",
            )

            return StreamingResponse(
                _safe_refusal_stream(
                    answer=answer_text,
                    query_id=ai_query.id,
                    reason=failure_reason,
                    model=settings.chat_model if settings.chat_provider == "ollama" else "stub",
                ),
                media_type="text/event-stream",
            )

        selected_pipeline = _select_pipeline(payload.pipeline, payload.question)

    # Stream response
    ai_query.status = "streaming"
    await session.commit()

    # Capture state for the post-stream persistence callback. The callback
    # uses a fresh session bound to the same engine because the request-bound
    # `session` may be closed by the time streaming finishes.
    session_factory = (
        async_sessionmaker(session.bind, expire_on_commit=False) if session.bind is not None else get_session_factory()
    )
    captured_user_id = current_user.id
    captured_patient_id = effective_patient_id
    captured_thread_id = payload.thread_id
    captured_query_id = ai_query.id
    captured_question = payload.question
    captured_ip = get_request_ip(request)
    completion_state = {"finished": False}

    async def _on_complete(completion: StreamCompletion) -> None:
        persistence_kwargs = {
            "ai_query_id": captured_query_id,
            "user_id": captured_user_id,
            "patient_id": captured_patient_id,
            "thread_id": captured_thread_id,
            "question": captured_question,
            "evidence": evidence,
            "retrieval_mode": retrieval_mode,
            "trace_id": trace_id,
            "ip_address": captured_ip,
            "started": started,
            "completion": completion,
        }
        try:
            await _persist_stream_completion(session_factory, **persistence_kwargs)
        except BaseException as exc:
            fallback_completion = StreamCompletion(
                validation_status="failed",
                answer="",
                cited_evidence=[],
                citations_payload=[],
                confidence="low",
                failure_reason="cancelled" if isinstance(exc, asyncio.CancelledError) else "persistence_error",
            )
            await _apply_stream_completion(
                session,
                **{
                    **persistence_kwargs,
                    "completion": fallback_completion,
                },
            )
            await session.commit()
            raise

        _log_telemetry(
            settings=settings,
            patient_id=captured_patient_id,
            evidence=evidence,
            blocked_count=blocked_chunk_count,
            failure_reason=completion.failure_reason,
        )
        completion_state["finished"] = True

    return StreamingResponse(
        _generate_sse_events(
            settings=settings,
            question=payload.question,
            evidence=evidence,
            conversation_history=conversation_history,
            query_id=ai_query.id,
            pipeline_name=selected_pipeline,
            resolved_patient=resolved_patient,
            on_complete=_on_complete,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
        background=BackgroundTask(_ensure_stream_terminal, completion_state, _on_complete),
    )
