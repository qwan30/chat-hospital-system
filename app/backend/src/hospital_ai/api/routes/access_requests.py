from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.models import User, PatientPermission
from hospital_ai.services.audit import AuditService

router = APIRouter()


class AccessRequestCreate(BaseModel):
    patient_id: UUID
    justification: str = Field(..., min_length=15)


class AccessRequestResponse(BaseModel):
    message: str
    patient_id: UUID
    expires_at: datetime


@router.post("", response_model=AccessRequestResponse)
async def create_access_request(
    payload: AccessRequestCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AccessRequestResponse:
    trace_id = new_trace_id()
    
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    permission = PatientPermission(
        user_id=current_user.id,
        patient_id=payload.patient_id,
        scope="read",
        source="access_request",
        expires_at=expires_at,
    )
    session.add(permission)
    
    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="access_request.create",
        object_type="patient_permission",
        object_id=permission.id,
        patient_id=payload.patient_id,
        outcome="allowed",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
        metadata={"justification": payload.justification},
    )
    await session.commit()
    
    return AccessRequestResponse(
        message="Temporary clinical access scope granted for 1 hour.",
        patient_id=payload.patient_id,
        expires_at=expires_at,
    )
