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
from hospital_ai.services.permissions import PermissionService
from hospital_ai.services.retrieval import RetrievalService

logger = logging.getLogger(__name__)

router = APIRouter()


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


async def _generate_sse_events(
    *,
    settings: Settings,
    question: str,
    evidence: list,
    conversation_history: list,
    query_id: UUID,
    pipeline_name: str,
    on_complete: Optional[OnCompleteCallback] = None,
) -> AsyncIterator[str]:
    """Generate SSE events with token-by-token streaming.

    Event format:
        data: {"type": "token", "content": "word"}
        data: {"type": "citations", "data": [...]}
        data: {"type": "done", "query_id": "..."}
        data: {"type": "error", "message": "..."}
    """
    completion_callback_active = False
    # This transport currently executes one grounded generation path.  Do not
    # claim a requested reasoning pipeline that was not actually run.
    actual_pipeline = "chitchat" if pipeline_name == "chitchat" else "simple_qa"

    async def complete_terminal(completion: StreamCompletion) -> None:
        nonlocal completion_callback_active
        completion_callback_active = True
        await _complete_stream(on_complete, completion)
        completion_callback_active = False

    try:
        retrieval_status = json.dumps({"type": "status", "stage": "retrieving"})
        yield f"data: {retrieval_status}\n\n"

        # Get LLM with streaming
        llm_manager = LLMManager(settings)
        llm = llm_manager.get()

        if pipeline_name == "chitchat":
            preparing_status = json.dumps({"type": "status", "stage": "preparing_answer"})
            yield f"data: {preparing_status}\n\n"
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

            validation_status = json.dumps({"type": "status", "stage": "validating_citations"})
            yield f"data: {validation_status}\n\n"
            output_result = await get_output_guardrail().scan(question, full_text)
            if output_result.blocked:
                refusal_event = json.dumps({"type": "token", "content": SAFE_PHI_LEAK_BLOCKED_ANSWER})
                yield f"data: {refusal_event}\n\n"
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

            event = json.dumps({"type": "token", "content": full_text})
            yield f"data: {event}\n\n"

            # Emit metadata, done, and run on_complete
            meta_event = json.dumps(
                {
                    "type": "metadata",
                    "confidence": "high",
                    "pipeline": "chitchat",
                    "model": llm.model_name(),
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

        preparing_status = json.dumps({"type": "status", "stage": "preparing_answer"})
        yield f"data: {preparing_status}\n\n"

        # Build prompt
        prompt = build_grounded_prompt(question, evidence, conversation_history)

        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are a hospital knowledge assistant. Answer only from the evidence. "
                    "Cite every factual claim using evidence IDs like [E1]."
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

        validation_status = json.dumps({"type": "status", "stage": "validating_citations"})
        yield f"data: {validation_status}\n\n"
        output_result = await get_output_guardrail().scan(question, full_text)
        if output_result.blocked:
            logger.warning(
                "Streaming answer blocked by output guardrail query_id=%s reason=%s",
                query_id,
                output_result.reason,
            )
            refusal_event = json.dumps({"type": "token", "content": SAFE_PHI_LEAK_BLOCKED_ANSWER})
            yield f"data: {refusal_event}\n\n"
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
            refusal_event = json.dumps({"type": "token", "content": SAFE_NO_EVIDENCE_ANSWER})
            yield f"data: {refusal_event}\n\n"
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

        # Validated — emit the full answer as token events so existing
        # frontend parsers continue to accumulate the text.  Yield in
        # whitespace-preserving chunks to keep the streaming contract.
        for piece in full_text.splitlines(keepends=True):
            if piece:
                event = json.dumps({"type": "token", "content": piece})
                yield f"data: {event}\n\n"

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

    effective_patient_id = payload.patient_id or (payload.context.patient_id if payload.context else None)

    # Create AI query record
    ai_query = AiQuery(
        user_id=current_user.id,
        patient_id=effective_patient_id,
        question=payload.question,
        status="received",
        model=settings.chat_model if settings.chat_provider == "ollama" else "stub",
    )
    session.add(ai_query)
    await session.flush()

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

        async def input_refusal_stream() -> AsyncIterator[str]:
            token = json.dumps({"type": "token", "content": SAFE_INJECTION_DETECTED_ANSWER})
            yield f"data: {token}\n\n"
            done = json.dumps(
                {
                    "type": "done",
                    "query_id": str(ai_query.id),
                    "confidence": "low",
                }
            )
            yield f"data: {done}\n\n"

        return StreamingResponse(input_refusal_stream(), media_type="text/event-stream")

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
        if retrieval_mode in ("bm25", "hybrid"):
            evidence = await retrieval_svc.hybrid_search(
                user_id=current_user.id,
                patient_id=effective_patient_id,
                query_embedding=query_embedding,
                query_text=payload.question,
                top_k=payload.top_k,
                retrieval_mode=retrieval_mode,
            )
        else:
            evidence = await retrieval_svc.search(
                user_id=current_user.id,
                patient_id=effective_patient_id,
                query_embedding=query_embedding,
                top_k=payload.top_k,
            )

        # ── Graph RAG Enrichment ─────────────────────────────────────────────
        try:
            if effective_patient_id:
                from hospital_ai.services.chat import extract_entities_and_relations_nlp, find_related_entities

                query_entities, _ = await extract_entities_and_relations_nlp(payload.question)
                entity_names = [entity.name for entity in query_entities]

                if entity_names:
                    graph_ctx = await find_related_entities(
                        session, entity_names, max_hops=2, patient_id=effective_patient_id
                    )
                    if graph_ctx.related_chunk_ids:
                        existing_ids = {e.chunk_id for e in evidence}
                        graph_only_ids = graph_ctx.related_chunk_ids - existing_ids
                        if graph_only_ids:
                            graph_evidence = await retrieval_svc.get_chunks_by_ids(
                                list(graph_only_ids)[: payload.top_k],
                                user_id=current_user.id,
                                patient_id=effective_patient_id,
                            )
                            for ge in graph_evidence:
                                ge.metadata["retrieval_method"] = "graph"
                            evidence.extend(graph_evidence)
                            evidence = evidence[: payload.top_k]
        except Exception:
            logger.warning("Graph RAG enrichment skipped", exc_info=True)

        # A chat attachment is an explicit evidence scope, not merely a UI
        # hint.  Permission filtering still happens inside retrieval; this
        # additional allow-list ensures only the requested document can reach
        # prompt construction or the streamed citation payload.
        requested_document_ids = set(payload.context.document_ids or []) if payload.context else set()
        if requested_document_ids:
            evidence = [item for item in evidence if item.document_id in requested_document_ids]

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

            async def no_evidence_stream() -> AsyncIterator[str]:
                event = json.dumps({"type": "token", "content": answer_text})
                yield f"data: {event}\n\n"
                done = json.dumps({"type": "done", "query_id": str(ai_query.id), "confidence": "low"})
                yield f"data: {done}\n\n"

            return StreamingResponse(no_evidence_stream(), media_type="text/event-stream")

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
