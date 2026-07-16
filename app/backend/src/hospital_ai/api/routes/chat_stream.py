"""Server-Sent Events (SSE) streaming endpoint for chat.
Endpoint API cung cấp luồng phản hồi hội thoại AI theo thời gian thực qua giao thức Server-Sent Events (SSE).

Provides token-by-token streaming responses using the LLM provider
abstraction layer, inspired by kotaemon's generator-based streaming.
Cung cấp câu trả lời theo từng token dựa trên lớp trừu tượng LLM,
lấy cảm hứng từ cơ chế streaming của kotaemon.
"""

import json
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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
    SAFE_NO_EVIDENCE_ANSWER,
    SAFE_INJECTION_DETECTED_ANSWER,
    SAFE_PHI_LEAK_BLOCKED_ANSWER,
    _select_pipeline,
    elapsed_ms,
)
from hospital_ai.services.guardrails import get_input_guardrail, get_output_guardrail
from hospital_ai.services.drug_check import DrugCheckService
from hospital_ai.services.graph_rag import extract_entities_and_relations_nlp, find_related_entities
from hospital_ai.services.metrics import MetricsService, TimingBreakdown
from hospital_ai.schemas.chat import DrugWarningSchema
from hospital_ai.services.chat_utils import (
    build_grounded_prompt,
    confidence_from_score,
    extract_citation_ids,
    is_chitchat_query,
    meets_evidence_threshold,
)
from hospital_ai.services.embeddings import EmbeddingService
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
    Trạng thái cuối cùng của luồng phản hồi SSE, được truyền cho hàm callback on_complete khi kết thúc.

    F-RAG-004 / demo-readiness fix: the route uses this payload to mirror
    the non-streaming `ChatService.answer` contract — persist the answer,
    evidence trace, audit row, and (when thread-bound) ChatMessage rows so
    that streamed answers survive a page reload.
    Route sử dụng dữ liệu này để lưu trữ câu trả lời, bằng chứng RAG, nhật ký kiểm kê
    và lịch sử tin nhắn (nếu thuộc thread), giúp dữ liệu không bị mất khi reload trang.
    """

    validation_status: str  # "passed" | "failed"
    answer: str
    cited_evidence: list[Any] = field(default_factory=list)
    citations_payload: list[dict] = field(default_factory=list)
    confidence: str = "low"
    t_gen_ms: int = 0


OnCompleteCallback = Callable[[StreamCompletion], Awaitable[None]]


async def _generate_sse_events(
    *,
    settings: Settings,
    question: str,
    evidence: list,
    conversation_history: list,
    query_id: UUID,
    pipeline_name: str,
    provider_override: str | None = None,
    drug_warnings: list | None = None,
    on_complete: OnCompleteCallback | None = None,
) -> AsyncIterator[str]:
    """Generate SSE events with token-by-token streaming.
    Tạo các sự kiện SSE để truyền tải từng token phản hồi về client.

    Event format:
        data: {"type": "token", "content": "word"}
        data: {"type": "citations", "data": [...]}
        data: {"type": "done", "query_id": "..."}
        data: {"type": "error", "message": "..."}
    """
    try:
        # Get LLM with streaming
        llm_manager = LLMManager(settings)
        llm = llm_manager.get(provider_override)

        if pipeline_name == "chitchat":
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
            full_text = ""
            t_gen_start = time.perf_counter()
            try:
                async for token in llm.stream(messages):
                    full_text += token
                    event = json.dumps({"type": "token", "content": token})
                    yield f"data: {event}\n\n"
            except Exception:
                if settings.chat_provider == "stub":
                    lower_q = question.lower()
                    if "xin chào" in lower_q or "chào" in lower_q or "hello" in lower_q or "hi" in lower_q:
                        full_text = "Xin chào! Tôi là trợ lý ảo HMS AI Copilot. Tôi có thể giúp gì cho bạn hôm nay?"
                    elif "cảm ơn" in lower_q or "cám ơn" in lower_q or "thank" in lower_q or "thanks" in lower_q:
                        full_text = "Không có gì! Nếu bạn cần thêm thông tin gì khác, cứ hỏi tôi nhé."
                    else:
                        full_text = (
                            "Tôi là HMS AI Copilot, trợ lý thông tin bệnh viện của bạn. Tôi có thể giúp gì cho bạn?"
                        )
                    event = json.dumps({"type": "token", "content": full_text})
                    yield f"data: {event}\n\n"
                else:
                    raise

            t_gen_ms = int((time.perf_counter() - t_gen_start) * 1000)
            
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
            done_event = json.dumps(
                {
                    "type": "done",
                    "query_id": str(query_id),
                    "validation": "passed",
                }
            )
            yield f"data: {done_event}\n\n"

            if on_complete is not None:
                try:
                    await on_complete(
                        StreamCompletion(
                            validation_status="passed",
                            answer=full_text,
                            cited_evidence=[],
                            citations_payload=[],
                            confidence="high",
                            t_gen_ms=t_gen_ms,
                        )
                    )
                except Exception:
                    logger.exception(
                        "Failed to persist chitchat stream query_id=%s",
                        query_id,
                    )
            return

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
        t_gen_start = time.perf_counter()
        full_text = ""
        async for token in llm.stream(messages):
            full_text += token
        t_gen_ms = int((time.perf_counter() - t_gen_start) * 1000)

        # --- Output Guardrail Check ---
        output_guard = get_output_guardrail()
        output_result = await output_guard.scan(question, full_text)

        if output_result.blocked:
            refusal_event = json.dumps({"type": "token", "content": SAFE_PHI_LEAK_BLOCKED_ANSWER})
            yield f"data: {refusal_event}\n\n"
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
            if on_complete is not None:
                try:
                    await on_complete(
                        StreamCompletion(
                            validation_status="failed",
                            answer=SAFE_PHI_LEAK_BLOCKED_ANSWER,
                            cited_evidence=[],
                            citations_payload=[],
                            confidence="low",
                            t_gen_ms=t_gen_ms,
                        )
                    )
                except Exception:
                    logger.exception("Failed to persist failed-validation stream query_id=%s", query_id)
            return

        # Restore original stream generator for valid text
        async def mock_stream():
            yield full_text
            
        async for token in mock_stream():
            full_text += token

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
            if on_complete is not None:
                try:
                    await on_complete(
                        StreamCompletion(
                            validation_status="failed",
                            answer=SAFE_NO_EVIDENCE_ANSWER,
                            cited_evidence=[],
                            citations_payload=[],
                            confidence="low",
                        )
                    )
                except Exception:
                    logger.exception(
                        "Failed to persist failed-validation stream query_id=%s",
                        query_id,
                    )
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
                "pipeline": pipeline_name,
                "model": llm.model_name(),
            }
        )
        yield f"data: {meta_event}\n\n"

        # Done
        done_event = json.dumps(
            {
                "type": "done",
                "query_id": str(query_id),
                "validation": "passed",
            }
        )
        yield f"data: {done_event}\n\n"

        # Persist after successful streaming so the answer survives a reload.
        if on_complete is not None:
            try:
                await on_complete(
                    StreamCompletion(
                        validation_status="passed",
                        answer=full_text,
                        cited_evidence=cited_evidence,
                        citations_payload=citations,
                        confidence=confidence,
                        t_gen_ms=t_gen_ms,
                    )
                )
            except Exception:
                logger.exception(
                    "Failed to persist completed stream query_id=%s",
                    query_id,
                )

    except AppError as exc:
        # Sanitized client-facing error (preserves AppError contract).
        error_event = json.dumps(
            {
                "type": "error",
                "code": exc.code,
                "message": exc.message,
            }
        )
        yield f"data: {error_event}\n\n"
    except Exception:
        # F-SEC-004: Never leak internal exception strings to the client.
        # Log the full trace server-side, return a generic message.
        logger.exception("SSE chat stream failed unexpectedly query_id=%s", query_id)
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
    patient_id: UUID | None,
    thread_id: UUID | None,
    question: str,
    evidence: list,
    retrieval_mode: str,
    trace_id: str,
    ip_address: str | None,
    started: float,
    t_embed_ms: int,
    t_retrieval_ms: int,
    pipeline_name: str,
    drug_warnings_count: int,
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

    ai_query.answer = completion.answer
    ai_query.status = "completed" if completion.validation_status == "passed" else "failed"
    ai_query.latency_ms = elapsed_ms(started)

    for index, item in enumerate(evidence, start=1):
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
            },
            trace_id=trace_id,
            created_at=datetime.now(UTC),
        )
        session.add(user_message)
        session.add(assistant_message)

        thread = await session.get(ChatThread, thread_id)
        if thread is not None:
            thread.last_message_at = assistant_message.created_at

    await AuditService(session).record(
        actor_user_id=user_id,
        action="chat.stream",
        object_type="ai_query",
        object_id=ai_query.id,
        patient_id=patient_id,
        outcome="allowed" if completion.validation_status == "passed" else "failed",
        trace_id=trace_id,
        ip_address=ip_address,
        metadata={
            "result": ai_query.status,
            "evidence_count": len(evidence),
            "validation": completion.validation_status,
            "thread_id": str(thread_id) if thread_id else None,
            "pipeline": pipeline_name,
            "drug_warnings": drug_warnings_count,
        },
    )

    if thread_id is not None and completion.validation_status == "passed":
        from hospital_ai.core.config import get_settings

        settings = get_settings()
        source_ids = [str(item.document_id) for item in evidence]
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


@router.post("/stream")
@limiter.limit("100/minute")
async def chat_stream(
    payload: ChatRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    """SSE streaming chat endpoint.
    Endpoint hỏi đáp AI phản hồi dạng luồng Server-Sent Events (SSE).

    Returns a text/event-stream response with token-by-token generation.
    Trả về response `text/event-stream` với các token được sinh và truyền liên tục theo thời gian thực.
    """
    started = time.perf_counter()
    trace_id = new_trace_id()

    effective_patient_id = payload.patient_id or (payload.context.patient_id if payload.context else None)

    from hospital_ai.db.migrations import HOSPITAL_PUBLIC_ID
    provider_override = None
    if not effective_patient_id:
        effective_patient_id = HOSPITAL_PUBLIC_ID
        provider_override = "gemini"

    # --- Input Guardrail Check ---
    input_guard = get_input_guardrail()
    input_result = await input_guard.scan(payload.question)

    if input_result.blocked:
        blocked_reason = input_result.reason
        
        # Create AI query record for denial
        ai_query = AiQuery(
            id=new_trace_id(),
            patient_id=effective_patient_id,
            user_id=current_user.id,
            question=payload.question,
            pipeline_type="unknown",
            status="denied",
            latency_ms=elapsed_ms(started),
            answer=SAFE_INJECTION_DETECTED_ANSWER,
        )
        session.add(ai_query)
        
        await AuditService(session).record(
            actor_user_id=current_user.id,
            action="chat.stream",
            object_type="ai_query",
            object_id=ai_query.id,
            patient_id=effective_patient_id,
            outcome="denied",
            trace_id=trace_id,
            ip_address=get_request_ip(request),
            metadata={"reason": "input_guardrail_blocked", "details": blocked_reason},
        )
        await session.commit()

        async def blocked_stream() -> AsyncIterator[str]:
            yield f"data: {{'type': 'token', 'content': '{SAFE_INJECTION_DETECTED_ANSWER}'}}\n\n"
            yield f"data: {{'type': 'done', 'query_id': '{str(ai_query.id)}', 'validation': 'failed', 'confidence': 'low'}}\n\n"

        return StreamingResponse(blocked_stream(), media_type="text/event-stream")

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
        ai_query.status = "denied"
        await AuditService(session).record(
            actor_user_id=current_user.id,
            action="chat.stream",
            object_type="ai_query",
            object_id=ai_query.id,
            patient_id=effective_patient_id,
            outcome="denied",
            trace_id=trace_id,
            ip_address=get_request_ip(request),
            metadata={"reason": "missing_patient_read_scope"},
        )
        await session.commit()

        async def denied_stream() -> AsyncIterator[str]:
            event = json.dumps({"type": "error", "message": "User is not authorized for this patient."})
            yield f"data: {event}\n\n"

        return StreamingResponse(denied_stream(), media_type="text/event-stream")

    # Gather conversation history
    conversation_history: list = []
    if payload.thread_id:
        from hospital_ai.services.chat import ChatService

        svc = ChatService(session, settings)
        conversation_history = await svc._get_conversation_history(
            payload.thread_id, current_user.id, effective_patient_id
        )

    drug_warnings = []
    t_embed_ms = 0
    t_retrieval_ms = 0
    retrieval_svc = None

    is_chitchat = is_chitchat_query(payload.question)
    logger.error(f"QUESTION IS: {payload.question!r}, IS_CHITCHAT: {is_chitchat}")

    if is_chitchat:
        evidence = []
        selected_pipeline = "chitchat"
        retrieval_mode = settings.retrieval_mode
    else:
        # Retrieve evidence (mirror chat.py mode dispatch).
        t_embed_start = time.perf_counter()
        query_embedding = await EmbeddingService(settings).embed(payload.question)
        t_embed_ms = int((time.perf_counter() - t_embed_start) * 1000)

        t_retrieval_start = time.perf_counter()
        retrieval_svc = RetrievalService(session)
        retrieval_mode = settings.retrieval_mode
        if retrieval_mode in ("bm25", "hybrid"):
            evidence = (
                await retrieval_svc.hybrid_search(
                    user_id=current_user.id,
                    patient_id=effective_patient_id,
                    query_embedding=query_embedding,
                    query_text=payload.question,
                    top_k=payload.top_k,
                    retrieval_mode=retrieval_mode,
                )
                if effective_patient_id
                else []
            )
        else:
            evidence = (
                await retrieval_svc.search(
                    user_id=current_user.id,
                    patient_id=effective_patient_id,
                    query_embedding=query_embedding,
                    top_k=payload.top_k,
                )
                if effective_patient_id
                else []
            )

        # Graph RAG & Drug Check
        try:
            if effective_patient_id:
                query_entities, _ = await extract_entities_and_relations_nlp(payload.question)
                if query_entities:
                    entity_names = [e.name for e in query_entities]
                    graph_ctx = await find_related_entities(
                        session, entity_names, max_hops=2, patient_id=effective_patient_id
                    )
                    if graph_ctx.related_chunk_ids:
                        existing_ids = {e.chunk_id for e in evidence}
                        graph_only_ids = graph_ctx.related_chunk_ids - existing_ids
                        if graph_only_ids:
                            graph_evidence = await retrieval_svc.get_chunks_by_ids(
                                list(graph_only_ids)[:payload.top_k],
                                user_id=current_user.id,
                                patient_id=effective_patient_id,
                            )
                            for ge in graph_evidence:
                                ge.metadata["retrieval_method"] = "graph"
                            evidence.extend(graph_evidence)
        except Exception:
            logger.warning("Graph RAG enrichment skipped", exc_info=True)

        t_retrieval_ms = int((time.perf_counter() - t_retrieval_start) * 1000)

        try:
            drug_warnings = await DrugCheckService(session).check_interactions(
                query_text=payload.question, patient_id=effective_patient_id
            )
        except Exception:
            logger.warning("Drug interaction check skipped", exc_info=True)

    if not is_chitchat and (not evidence or not meets_evidence_threshold(evidence[0], retrieval_mode, settings.evidence_threshold)):
        is_blocked = retrieval_svc.blocked_chunk_count > 0
        answer_text = PERMISSION_DENIED_CHAT_ANSWER if is_blocked else SAFE_NO_EVIDENCE_ANSWER
        result_status = "denied" if is_blocked else "no_evidence"
        outcome = "denied" if is_blocked else "allowed"

        ai_query.status = result_status
        ai_query.answer = answer_text
        ai_query.latency_ms = elapsed_ms(started)

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

        await AuditService(session).record(
            actor_user_id=current_user.id,
            action="chat.stream",
            object_type="ai_query",
            object_id=ai_query.id,
            patient_id=effective_patient_id,
            outcome=outcome,
            trace_id=trace_id,
            ip_address=get_request_ip(request),
            metadata={"result": result_status, "evidence_count": 0},
        )
        await session.commit()

        async def no_evidence_stream() -> AsyncIterator[str]:
            event = json.dumps({"type": "token", "content": answer_text})
            yield f"data: {event}\n\n"
            done = json.dumps({"type": "done", "query_id": str(ai_query.id), "confidence": "low"})
            yield f"data: {done}\n\n"

        return StreamingResponse(no_evidence_stream(), media_type="text/event-stream")

        if not is_chitchat:
            selected_pipeline = _select_pipeline(payload.pipeline, payload.question)

    # Stream response
    ai_query.status = "streaming"
    await session.commit()

    # Capture state for the post-stream persistence callback. The callback
    # uses a fresh session opened from the global factory because the
    # request-bound `session` may be closed by the time streaming finishes.
    session_factory = get_session_factory()
    captured_user_id = current_user.id
    captured_patient_id = effective_patient_id
    captured_thread_id = payload.thread_id
    captured_query_id = ai_query.id
    captured_question = payload.question
    captured_ip = get_request_ip(request)

    async def _on_complete(completion: StreamCompletion) -> None:
        await _persist_stream_completion(
            session_factory,
            ai_query_id=captured_query_id,
            user_id=captured_user_id,
            patient_id=captured_patient_id,
            thread_id=captured_thread_id,
            question=captured_question,
            evidence=evidence,
            retrieval_mode=retrieval_mode,
            trace_id=trace_id,
            ip_address=captured_ip,
            started=started,
            t_embed_ms=t_embed_ms,
            t_retrieval_ms=t_retrieval_ms,
            pipeline_name=selected_pipeline,
            drug_warnings_count=len(drug_warnings),
            completion=completion,
        )

    return StreamingResponse(
        _generate_sse_events(
            settings=settings,
            question=payload.question,
            evidence=evidence,
            conversation_history=conversation_history,
            query_id=ai_query.id,
            pipeline_name=selected_pipeline,
            provider_override=provider_override,
            drug_warnings=drug_warnings,
            on_complete=_on_complete,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
