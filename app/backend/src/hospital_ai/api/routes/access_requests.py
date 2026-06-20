import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.api.limiter import limiter
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.models import AccessRequest, PatientPermission, User
from hospital_ai.services.audit import AuditService
from hospital_ai.services.hms_connector import HmsApiClient

logger = logging.getLogger(__name__)

router = APIRouter()


class AccessRequestCreate(BaseModel):
    patient_id: UUID
    justification: str = Field(..., min_length=15)


class AccessRequestResponse(BaseModel):
    id: UUID
    message: str
    patient_id: UUID
    status: str


class AccessRequestListItem(BaseModel):
    id: UUID
    patient_id: UUID
    patient_name: str
    patient_mrn: str
    requester_id: UUID
    requester_name: str
    requester_role: str
    status: str
    justification: str
    created_at: datetime


class AccessRequestDetail(AccessRequestListItem):
    reviewed_by_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None


class AccessRequestReview(BaseModel):
    status: str = Field(..., description="approved, denied, or pending_info")
    notes: str = Field(default="")


@router.post("", response_model=AccessRequestResponse)
@limiter.limit("3/minute")
async def create_access_request(
    payload: AccessRequestCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> AccessRequestResponse:
    trace_id = new_trace_id()

    # P1-2: When HMS sync is enabled, route the access request through
    # the HMS for audit and approval BEFORE granting local permission.
    if settings.hms_sync_enabled:
        hms_client = HmsApiClient(settings)
        try:
            await hms_client.request_patient_access(
                str(payload.patient_id),
                str(current_user.id),
                payload.justification,
            )
        except ExternalServiceError as exc:
            logger.warning(
                "HMS access request denied for user=%s patient=%s: %s",
                current_user.id,
                payload.patient_id,
                exc.message,
            )
            raise HTTPException(
                status_code=502,
                detail="HMS access request could not be processed. Try again later.",
            ) from exc

    req = AccessRequest(
        user_id=current_user.id,
        patient_id=payload.patient_id,
        justification=payload.justification,
        status="pending",
    )
    session.add(req)
    await session.flush()

    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="access_request.create",
        object_type="access_request",
        object_id=req.id,
        patient_id=payload.patient_id,
        outcome="allowed",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
        metadata={"justification": payload.justification},
    )
    await session.commit()

    return AccessRequestResponse(
        id=req.id,
        message="Access request submitted for review.",
        patient_id=payload.patient_id,
        status="pending",
    )


@router.get("", response_model=list[AccessRequestListItem])
async def list_access_requests(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[AccessRequestListItem]:
    if current_user.role not in ("admin", "security"):
        raise HTTPException(status_code=403, detail="Not authorized to list requests")

    stmt = (
        select(AccessRequest)
        .options(joinedload(AccessRequest.patient), joinedload(AccessRequest.user))
        .order_by(desc(AccessRequest.created_at))
    )
    result = await session.execute(stmt)
    requests = result.scalars().all()

    return [
        AccessRequestListItem(
            id=req.id,
            patient_id=req.patient_id,
            patient_name=req.patient.full_name if req.patient else "Unknown",
            patient_mrn=req.patient.mrn if req.patient else "Unknown",
            requester_id=req.user_id,
            requester_name=req.user.full_name if req.user else "Unknown",
            requester_role=req.user.role if req.user else "Unknown",
            status=req.status,
            justification=req.justification,
            created_at=req.created_at,
        )
        for req in requests
    ]


@router.get("/{request_id}", response_model=AccessRequestDetail)
async def get_access_request(
    request_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AccessRequestDetail:
    if current_user.role not in ("admin", "security"):
        raise HTTPException(status_code=403, detail="Not authorized to view requests")

    stmt = (
        select(AccessRequest)
        .options(
            joinedload(AccessRequest.patient), joinedload(AccessRequest.user), joinedload(AccessRequest.reviewed_by)
        )
        .where(AccessRequest.id == request_id)
    )
    result = await session.execute(stmt)
    req = result.scalar_one_or_none()

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    return AccessRequestDetail(
        id=req.id,
        patient_id=req.patient_id,
        patient_name=req.patient.full_name if req.patient else "Unknown",
        patient_mrn=req.patient.mrn if req.patient else "Unknown",
        requester_id=req.user_id,
        requester_name=req.user.full_name if req.user else "Unknown",
        requester_role=req.user.role if req.user else "Unknown",
        status=req.status,
        justification=req.justification,
        created_at=req.created_at,
        reviewed_by_name=req.reviewed_by.full_name if req.reviewed_by else None,
        reviewed_at=req.reviewed_at,
        review_notes=req.review_notes,
    )


@router.put("/{request_id}/review", response_model=AccessRequestResponse)
async def review_access_request(
    request_id: UUID,
    payload: AccessRequestReview,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AccessRequestResponse:
    if current_user.role not in ("admin", "security"):
        raise HTTPException(status_code=403, detail="Not authorized to review requests")

    if payload.status not in ("approved", "denied", "pending_info"):
        raise HTTPException(status_code=400, detail="Invalid review status.")

    if payload.status in ("denied", "pending_info") and not payload.notes.strip():
        raise HTTPException(status_code=400, detail=f"Notes are required to set status to {payload.status}.")

    req = await session.get(AccessRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.status not in ("pending", "pending_info"):
        raise HTTPException(status_code=400, detail="Request already resolved")

    req.status = payload.status
    req.reviewed_by_user_id = current_user.id
    req.reviewed_at = datetime.now(timezone.utc)
    req.review_notes = payload.notes

    trace_id = new_trace_id()

    if payload.status == "approved":
        expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
        permission = PatientPermission(
            user_id=req.user_id,
            patient_id=req.patient_id,
            scope="read",
            source="access_request",
            expires_at=expires_at,
        )
        session.add(permission)

    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="access_request.review",
        object_type="access_request",
        object_id=req.id,
        patient_id=req.patient_id,
        outcome="allowed",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
        metadata={"status": payload.status, "notes": payload.notes},
    )
    await session.commit()

    return AccessRequestResponse(
        id=req.id,
        message=f"Access request {payload.status}.",
        patient_id=req.patient_id,
        status=req.status,
    )
