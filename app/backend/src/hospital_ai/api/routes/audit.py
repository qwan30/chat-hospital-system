import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_session
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.db.models import AuditLog, User
from hospital_ai.schemas.audit import AuditLogList

router = APIRouter()


async def _list_logs(
    patient_id: Optional[uuid.UUID],
    limit: int,
    session: AsyncSession,
    current_user: User,
) -> AuditLogList:
    if current_user.role not in {"security", "admin"}:
        raise PermissionDeniedError("Only security or admin users can view audit logs.")

    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if patient_id is not None:
        stmt = stmt.where(AuditLog.patient_id == patient_id)
    result = await session.execute(stmt)
    return AuditLogList(items=list(result.scalars().all()))


@router.get("/logs", response_model=AuditLogList)
async def list_logs(
    patient_id: Optional[uuid.UUID] = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AuditLogList:
    return await _list_logs(patient_id, limit, session, current_user)


@router.get("/events", response_model=AuditLogList)
async def list_events_alias(
    patient_id: Optional[uuid.UUID] = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AuditLogList:
    return await _list_logs(patient_id, limit, session, current_user)
