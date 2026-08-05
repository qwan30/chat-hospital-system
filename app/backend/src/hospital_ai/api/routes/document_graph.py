from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_session
from hospital_ai.db.models import Document, User
from hospital_ai.schemas.document_graph import DocumentGraphRead
from hospital_ai.services.capabilities import CapabilityService
from hospital_ai.services.graph_query import GraphFilters, GraphQueryService

router = APIRouter()


async def require_document_read(
    document_id: UUID, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)
) -> Document:
    document = await session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/{document_id}/graph", response_model=DocumentGraphRead)
async def get_document_graph(
    document_id: UUID,
    filters: GraphFilters = Depends(),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentGraphRead:
    document = await require_document_read(document_id, session, current_user)
    if filters.include_superseded:
        # Require superseded evidence capability
        await CapabilityService(session).require(
            user=current_user,
            patient_id=document.patient_id,
            capability="superseded_evidence.read",
            action="document.graph.superseded.read",
            trace_id="test_trace",  # Normally from new_trace_id()
            object_id=document.id,
        )
    return await GraphQueryService(session).document_graph(document, current_user, filters)


@router.get("/{document_id}/timeline")
async def get_document_timeline(
    document_id: UUID, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)
):
    document = await require_document_read(document_id, session, current_user)
    # Placeholder for timeline response
    return {"events": []}
