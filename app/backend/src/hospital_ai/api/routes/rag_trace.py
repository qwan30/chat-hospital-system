"""RAG Trace Observability API.

Allows clinicians and admins to inspect the full retrieval pipeline trace
for a given AI query — which chunks were retrieved, their scores before
and after reranking, the retrieval method, and the reranker backend used.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user
from hospital_ai.db.models import (
    AiQuery,
    RetrievedEvidence,
    User,
)
from hospital_ai.db.session import get_session
from hospital_ai.schemas.chat import RagTraceEvidence, RagTraceResponse
from hospital_ai.services.retrieval import RetrievalService

router = APIRouter()


@router.get(
    "/queries/{query_id}/trace",
    response_model=RagTraceResponse,
    summary="Get RAG trace for a query",
    description=(
        "Returns the full RAG retrieval trace including retrieved chunks, "
        "scores before and after reranking, retrieval methods, and latency."
    ),
)
async def get_rag_trace(
    query_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> RagTraceResponse:
    """Return the full RAG trace for a given AI query.

    Only the user who created the query (or an admin) can view the trace.
    """
    # Fetch the AI query
    result = await db.execute(select(AiQuery).where(AiQuery.id == query_id))
    ai_query = result.scalar_one_or_none()
    if ai_query is None:
        raise HTTPException(status_code=404, detail="Query not found.")

    # Authorization: only the query owner or admin can view
    if ai_query.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this trace.")

    # Re-authorize each persisted evidence row against the current patient
    # grant, active document/page chain, and role tags. A trace is historical
    # telemetry, not a bypass around read-time evidence authorization.
    evidence_result = await db.execute(
        select(RetrievedEvidence).where(RetrievedEvidence.ai_query_id == query_id).order_by(RetrievedEvidence.rank)
    )
    evidence_rows = evidence_result.scalars().all()
    visible_chunks = await RetrievalService(db).get_chunks_by_ids(
        [ev.chunk_id for ev in evidence_rows],
        user_id=user.id,
        patient_id=ai_query.patient_id,
    )
    visible_by_chunk_id = {chunk.chunk_id: chunk for chunk in visible_chunks}

    trace_evidence = []
    for ev in evidence_rows:
        chunk = visible_by_chunk_id.get(ev.chunk_id)
        if chunk is None:
            continue

        trace_evidence.append(
            RagTraceEvidence(
                evidence_id=f"E{ev.rank}",
                chunk_id=ev.chunk_id,
                rank=ev.rank,
                retrieval_score=float(ev.score),
                rerank_score=float(ev.rerank_score) if ev.rerank_score is not None else None,
                retrieval_method=ev.retrieval_method,
                rerank_method=ev.rerank_method,
                citation_label=ev.citation_label,
                content=chunk.content,
                document_title=chunk.document_title,
                page=chunk.page,
            )
        )

    # Determine pipeline from audit metadata (best effort)
    pipeline = None
    if ai_query.answer:
        # The pipeline field isn't stored on AiQuery directly, but we can
        # infer from metadata or default to None
        pipeline = None

    return RagTraceResponse(
        query_id=ai_query.id,
        question=ai_query.question,
        answer=ai_query.answer,
        status=ai_query.status,
        pipeline=pipeline,
        model=ai_query.model,
        latency_ms=ai_query.latency_ms,
        evidence=trace_evidence,
        created_at=ai_query.created_at.isoformat(),
    )
