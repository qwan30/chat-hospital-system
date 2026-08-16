import logging

import httpx
from fastapi import APIRouter, Depends, Request
from sqlalchemy import case, func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.security import PATIENT_READ_SCOPES, new_trace_id
from hospital_ai.db.models import AuditLog, Document, Patient, User
from hospital_ai.schemas.dashboard import DashboardSummaryResponse
from hospital_ai.services.audit import AuditService
from hospital_ai.services.hms_connector import HmsApiClient
from hospital_ai.services.metrics import MetricsService
from hospital_ai.services.permissions import active_patient_permission_exists

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> DashboardSummaryResponse:
    trace_id = new_trace_id()

    # 1. Recent patients accessed by the user (with permission check)
    permission_exists = active_patient_permission_exists(
        user_id=current_user.id,
        patient_id=Patient.id,
        accepted_scopes=PATIENT_READ_SCOPES,
    )

    stmt = (
        select(Patient.id, Patient.full_name, Patient.mrn, func.max(AuditLog.created_at).label("last_accessed"))
        .join(AuditLog, AuditLog.patient_id == Patient.id)
        .where(
            Patient.deleted_at.is_(None),
            AuditLog.actor_user_id == current_user.id,
            AuditLog.action.like("patient.%"),
            AuditLog.outcome == "allowed",
            permission_exists,
        )
        .group_by(Patient.id, Patient.full_name, Patient.mrn)
        .order_by(func.max(AuditLog.created_at).desc())
        .limit(5)
    )

    result = await session.execute(stmt)
    recent_patients = []
    for row in result.all():
        recent_patients.append(
            {"id": row.id, "full_name": row.full_name, "mrn": row.mrn, "last_accessed": row.last_accessed}
        )

    # 2. Document stats
    doc_stmt = select(
        func.sum(case((and_(Document.status.in_(["ready", "ready_with_warnings"]), Document.active_index_generation_id.is_not(None)), 1), else_=0)).label("indexed"),
        func.sum(case((Document.status.in_(["uploaded", "processing"]), 1), else_=0)).label("processing"),
        func.sum(case((Document.status.in_(["failed"]), 1), else_=0)).label("failed"),
    ).where(Document.deleted_at.is_(None))
    doc_result = await session.execute(doc_stmt)
    doc_row = doc_result.one()
    document_stats = {
        "indexed": doc_row.indexed or 0,
        "processing": doc_row.processing or 0,
        "failed": doc_row.failed or 0,
    }

    # 3. Metrics (Time & cost saved)
    metrics_summary = await MetricsService(session).get_summary()
    hours_saved = round(metrics_summary.total_time_saved_sec / 3600.0, 2)
    cost_saved_usd = round(metrics_summary.total_cost_saved, 2)
    metrics = {"hours_saved": hours_saved, "cost_saved_usd": cost_saved_usd}

    # 4. Systems health status (non-blocking, fast-fail)
    hms_client = HmsApiClient(settings)
    hms_healthy = await hms_client.health_check()
    hms_api = "healthy" if hms_healthy else "unreachable"

    ollama_healthy = False
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            res = await client.get(settings.ollama_base_url.rstrip("/"))
            ollama_healthy = res.status_code in (200, 404)
    except Exception:
        pass  # Ollama not running is normal in dev
    ollama_inference = "healthy" if ollama_healthy else "unreachable"

    systems_health = {"hms_api": hms_api, "ollama_inference": ollama_inference}

    # 5. Record audit log for dashboard read
    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="dashboard.read",
        object_type="dashboard",
        outcome="allowed",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )
    await session.commit()

    return DashboardSummaryResponse(
        recent_patients=recent_patients, document_stats=document_stats, metrics=metrics, systems_health=systems_health
    )
