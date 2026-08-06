from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_session
from hospital_ai.core.errors import NotFoundError
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.models import Document, User
from hospital_ai.schemas.document_graph import DocumentGraphRead
from hospital_ai.services.audit import AuditService
from hospital_ai.services.capabilities import CapabilityService
from hospital_ai.services.clinical_timeline import ClinicalTimelineService
from hospital_ai.services.graph_query import GraphFilters, GraphQueryService
from hospital_ai.services.permissions import PermissionService

router = APIRouter()


async def require_document_read(
    document_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    *,
    enforce_patient_scope: bool = True,
) -> Document:
    document = await session.get(Document, document_id)
    if not document or document.deleted_at is not None:
        if current_user:
            await AuditService(session).record(
                actor_user_id=current_user.id,
                action="document.graph.timeline.read",
                object_type="document",
                object_id=document_id,
                patient_id=None,
                outcome="denied",
                trace_id=new_trace_id(),
                metadata={"reason": "document_not_found"},
            )
            await session.commit()
        raise NotFoundError("Document not found.")
    if enforce_patient_scope:
        await PermissionService(session).require_read(
            user=current_user,
            patient_id=document.patient_id,
            action="document.graph.timeline.read",
            trace_id=new_trace_id(),
            object_type="document",
            object_id=document.id,
        )
    return document


@router.get("/{document_id}/graph", response_model=DocumentGraphRead)
async def get_document_graph(
    document_id: UUID,
    filters: GraphFilters = Depends(),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentGraphRead:
    document = await require_document_read(
        document_id,
        session,
        current_user,
        enforce_patient_scope=not filters.include_superseded,
    )
    if filters.include_superseded:
        # Require superseded evidence capability
        await CapabilityService(session).require(
            user=current_user,
            patient_id=document.patient_id,
            capability="superseded_evidence.read",
            action="document.graph.superseded.read",
            trace_id=new_trace_id(),
            object_id=document.id,
        )
        await PermissionService(session).require_read(
            user=current_user,
            patient_id=document.patient_id,
            action="document.graph.superseded.read",
            trace_id=new_trace_id(),
            object_type="document",
            object_id=document.id,
        )
    return await GraphQueryService(session).document_graph(document, current_user, filters)


@router.get("/{document_id}/timeline")
async def get_document_timeline(
    document_id: UUID, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)
):
    document = await require_document_read(document_id, session, current_user)
    return await ClinicalTimelineService(session).document_timeline(document, current_user, {})
