from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_session
from hospital_ai.db.models import Document, DocumentChunk, User

router = APIRouter(tags=["Metrics"])


@router.get("/metrics")
def get_metrics() -> Response:
    """Return Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/metrics/vector")
async def get_vector_metrics(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    # 1. Count indexed documents
    # Unified contract: Document must be ready/ready_with_warnings and have an active generation or we just use status.
    # We use status and ensure we count only documents that aren't deleted.
    doc_stmt = select(func.count(Document.id)).where(
        Document.deleted_at.is_(None),
        Document.status.in_(["ready", "ready_with_warnings"]),
        Document.active_index_generation_id.is_not(None)
    )
    indexed_document_count = await session.scalar(doc_stmt) or 0

    # 2. Count active chunks matching the active generation
    chunk_stmt = select(func.count(DocumentChunk.id)).join(
        Document, Document.id == DocumentChunk.document_id
    ).where(
        DocumentChunk.deleted_at.is_(None),
        Document.deleted_at.is_(None),
        Document.status.in_(["ready", "ready_with_warnings"]),
        DocumentChunk.generation_id.is_not_distinct_from(Document.active_index_generation_id)
    )
    active_chunk_count = await session.scalar(chunk_stmt) or 0

    # 3. Sources breakdown
    sources_stmt = select(
        Document.id,
        func.count(DocumentChunk.id).label("chunk_count")
    ).join(
        DocumentChunk,
        and_(
            DocumentChunk.document_id == Document.id,
            DocumentChunk.deleted_at.is_(None),
            DocumentChunk.generation_id.is_not_distinct_from(Document.active_index_generation_id)
        ),
        isouter=True
    ).where(
        Document.deleted_at.is_(None),
        Document.status.in_(["ready", "ready_with_warnings"])
    ).group_by(Document.id)
    
    result = await session.execute(sources_stmt)
    sources = [{"document_id": str(row.id), "chunk_count": row.chunk_count} for row in result.all()]

    return {
        "indexed_document_count": indexed_document_count,
        "active_chunk_count": active_chunk_count,
        "sources": sources
    }
