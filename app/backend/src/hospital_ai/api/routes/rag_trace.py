"""RAG Trace Observability API.
Các endpoint API giúp giám sát, kiểm định và truy xuất chi tiết luồng bằng chứng RAG của từng câu hỏi AI.

Allows clinicians and admins to inspect the full retrieval pipeline trace
for a given AI query — which chunks were retrieved, their scores before
and after reranking, the retrieval method, and the reranker backend used.
Cho phép bác sĩ và quản trị viên kiểm tra quá trình truy xuất (retrieval pipeline):
các đoạn văn bản được trích xuất, điểm số trước và sau khi rerank, phương pháp truy xuất
và mô hình xếp hạng lại (reranker) được sử dụng.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user
from hospital_ai.db.models import (
    AiQuery,
    Document,
    DocumentChunk,
    DocumentPage,
    RetrievedEvidence,
    User,
)
from hospital_ai.db.session import get_session
from hospital_ai.schemas.chat import RagTraceEvidence, RagTraceResponse

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
    Trả về toàn bộ chi tiết luồng truy xuất RAG (RAG trace) của một câu hỏi AI cụ thể.

    Only the user who created the query (or an admin) can view the trace.
    Chỉ người dùng tạo ra câu hỏi đó (hoặc quản trị viên hệ thống) mới có quyền truy cập thông tin trace này.
    """
    # Fetch the AI query
    result = await db.execute(select(AiQuery).where(AiQuery.id == query_id))
    ai_query = result.scalar_one_or_none()
    if ai_query is None:
        raise HTTPException(status_code=404, detail="Query not found.")

    # Authorization: only the query owner or admin can view
    if ai_query.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this trace.")

    # Fetch all retrieved evidence with chunk details
    evidence_result = await db.execute(
        select(RetrievedEvidence).where(RetrievedEvidence.ai_query_id == query_id).order_by(RetrievedEvidence.rank)
    )
    evidence_rows = evidence_result.scalars().all()

    # Gather chunk details for content and document info
    trace_evidence = []
    for ev in evidence_rows:
        # Fetch chunk and its document
        chunk_result = await db.execute(
            select(DocumentChunk, Document, DocumentPage)
            .join(Document, Document.id == DocumentChunk.document_id)
            .join(
                DocumentPage,
                DocumentPage.id == DocumentChunk.page_id,
            )
            .where(DocumentChunk.id == ev.chunk_id)
        )
        row = chunk_result.first()

        content = None
        doc_title = None
        page_num = None
        if row:
            chunk_obj, doc_obj, page_obj = row
            content = chunk_obj.content
            doc_title = doc_obj.title
            page_num = page_obj.page_number

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
                content=content,
                document_title=doc_title,
                page=page_num,
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
