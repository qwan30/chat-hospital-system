"""Server-Sent Events (SSE) streaming endpoint for chat.

Provides token-by-token streaming responses using the LLM provider
abstraction layer, inspired by kotaemon's generator-based streaming.
"""

import json
import time
from typing import AsyncIterator, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.security import PATIENT_READ_SCOPES, new_trace_id
from hospital_ai.db.models import AiQuery, User
from hospital_ai.schemas.chat import ChatRequest
from hospital_ai.services.audit import AuditService
from hospital_ai.services.chat import SAFE_NO_EVIDENCE_ANSWER, _select_pipeline, elapsed_ms
from hospital_ai.services.chat_utils import (
    build_grounded_prompt,
    confidence_from_score,
    MAX_HISTORY_MESSAGES,
)
from hospital_ai.services.embeddings import EmbeddingService
from hospital_ai.services.llm import LLMManager
from hospital_ai.services.llm.base import LLMMessage
from hospital_ai.services.permissions import PermissionService
from hospital_ai.services.retrieval import RetrievalService

router = APIRouter()


async def _generate_sse_events(
    *,
    settings: Settings,
    question: str,
    evidence: list,
    conversation_history: list,
    query_id: UUID,
    pipeline_name: str,
) -> AsyncIterator[str]:
    """Generate SSE events with token-by-token streaming.

    Event format:
        data: {"type": "token", "content": "word"}
        data: {"type": "citations", "data": [...]}
        data: {"type": "done", "query_id": "..."}
        data: {"type": "error", "message": "..."}
    """
    try:
        # Build prompt
        prompt = build_grounded_prompt(question, evidence, conversation_history)

        # Get LLM with streaming
        llm_manager = LLMManager(settings)
        llm = llm_manager.get()

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

        # Stream tokens
        full_text = ""
        async for token in llm.stream(messages):
            full_text += token
            event = json.dumps({"type": "token", "content": token})
            yield f"data: {event}\n\n"

        # Send citations
        citations = []
        for item in evidence:
            citations.append({
                "evidence_id": item.evidence_id,
                "document_id": str(item.document_id),
                "document_title": item.document_title,
                "page": item.page,
                "score": item.score,
                "content": item.content[:200],
            })
        citation_event = json.dumps({"type": "citations", "data": citations})
        yield f"data: {citation_event}\n\n"

        # Send confidence
        avg_score = sum(e.score for e in evidence) / len(evidence) if evidence else 0.0
        confidence = confidence_from_score(avg_score)
        meta_event = json.dumps({
            "type": "metadata",
            "confidence": confidence,
            "pipeline": pipeline_name,
            "model": llm.model_name(),
        })
        yield f"data: {meta_event}\n\n"

        # Done
        done_event = json.dumps({"type": "done", "query_id": str(query_id)})
        yield f"data: {done_event}\n\n"

    except Exception as exc:
        error_event = json.dumps({"type": "error", "message": str(exc)})
        yield f"data: {error_event}\n\n"


@router.post("/stream")
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

    # Create AI query record
    ai_query = AiQuery(
        user_id=current_user.id,
        patient_id=payload.patient_id,
        question=payload.question,
        status="received",
        model=settings.chat_model if settings.chat_provider == "ollama" else "stub",
    )
    session.add(ai_query)
    await session.flush()

    # Permission check
    has_scope = await PermissionService(session).has_patient_scope(
        user_id=current_user.id,
        patient_id=payload.patient_id,
        accepted_scopes=PATIENT_READ_SCOPES,
    )
    if not has_scope:
        ai_query.status = "denied"
        await AuditService(session).record(
            actor_user_id=current_user.id,
            action="chat.stream",
            object_type="ai_query",
            object_id=ai_query.id,
            patient_id=payload.patient_id,
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
        conversation_history = await svc._get_conversation_history(payload.thread_id)

    # Retrieve evidence
    query_embedding = await EmbeddingService(settings).embed(payload.question)
    evidence = await RetrievalService(session).search(
        user_id=current_user.id,
        patient_id=payload.patient_id,
        query_embedding=query_embedding,
        top_k=payload.top_k,
    )

    if not evidence or evidence[0].score < settings.evidence_threshold:
        ai_query.status = "no_evidence"
        ai_query.answer = SAFE_NO_EVIDENCE_ANSWER
        ai_query.latency_ms = elapsed_ms(started)
        await session.commit()

        async def no_evidence_stream() -> AsyncIterator[str]:
            event = json.dumps({"type": "token", "content": SAFE_NO_EVIDENCE_ANSWER})
            yield f"data: {event}\n\n"
            done = json.dumps({"type": "done", "query_id": str(ai_query.id), "confidence": "low"})
            yield f"data: {done}\n\n"

        return StreamingResponse(no_evidence_stream(), media_type="text/event-stream")

    # Stream response
    selected_pipeline = _select_pipeline(payload.pipeline, payload.question)
    ai_query.status = "streaming"
    await session.commit()

    return StreamingResponse(
        _generate_sse_events(
            settings=settings,
            question=payload.question,
            evidence=evidence,
            conversation_history=conversation_history,
            query_id=ai_query.id,
            pipeline_name=selected_pipeline,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
