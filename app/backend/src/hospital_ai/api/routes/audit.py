"""Security audit log API routes.
Các endpoint API tra cứu và liệt kê nhật ký kiểm kê bảo mật (chỉ dành cho vai trò security hoặc admin).
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_session
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.db.models import AuditLog, User
from hospital_ai.schemas.audit import AuditLogList

router = APIRouter()


async def _list_logs(
    patient_id: uuid.UUID | None,
    action: str | None,
    outcome: str | None,
    limit: int,
    session: AsyncSession,
    current_user: User,
) -> AuditLogList:
    """Helper function to query and filter audit log records based on patient, action, and outcome.
    Hàm hỗ trợ truy vấn và lọc các bản ghi nhật ký kiểm kê theo bệnh nhân, hành động và kết quả.
    """
    if current_user.role not in {"security", "admin"}:
        raise PermissionDeniedError("Only security or admin users can view audit logs.")

    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if patient_id is not None:
        stmt = stmt.where(AuditLog.patient_id == patient_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if outcome:
        stmt = stmt.where(AuditLog.outcome == outcome)
    result = await session.execute(stmt)
    return AuditLogList(items=list(result.scalars().all()))


@router.get("/logs", response_model=AuditLogList)
async def list_logs(
    patient_id: uuid.UUID | None = None,
    action: str | None = None,
    outcome: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AuditLogList:
    """Retrieve security audit logs filtered by patient, action type, or outcome status.
    Tra cứu danh sách nhật ký bảo mật theo bộ lọc bệnh nhân, loại hành động hoặc kết quả xử lý.
    """
    return await _list_logs(patient_id, action, outcome, limit, session, current_user)


@router.get("/events", response_model=AuditLogList)
async def list_events_alias(
    patient_id: uuid.UUID | None = None,
    action: str | None = None,
    outcome: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AuditLogList:
    """Alias route for retrieving security audit events (`/events`).
    Endpoint bí danh (alias) để lấy danh sách sự kiện kiểm kê bảo mật (`/events`).
    """
    return await _list_logs(patient_id, action, outcome, limit, session, current_user)
