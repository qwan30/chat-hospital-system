import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.core.security import PATIENT_READ_SCOPES, new_trace_id
from hospital_ai.db.models import Patient, User
from hospital_ai.schemas.patients import PatientRead, PatientSearchResponse
from hospital_ai.services.audit import AuditService
from hospital_ai.services.permissions import PermissionService, active_patient_permission_exists

router = APIRouter()


@router.get("/search", response_model=PatientSearchResponse)
async def search_patients(
    request: Request,
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PatientSearchResponse:
    permission_exists = active_patient_permission_exists(
        user_id=current_user.id,
        patient_id=Patient.id,
        accepted_scopes=PATIENT_READ_SCOPES,
    )
    stmt = (
        select(Patient)
        .where(Patient.deleted_at.is_(None), permission_exists)
        .order_by(Patient.full_name)
    )
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(or_(Patient.full_name.ilike(pattern), Patient.mrn.ilike(pattern)))
    result = await session.execute(stmt.limit(limit))
    patients = list(result.scalars().all())

    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="patient.search",
        object_type="patient",
        outcome="allowed",
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
        metadata={"q": q, "result_count": len(patients)},
    )
    await session.commit()
    return PatientSearchResponse(items=patients)


@router.get("/{patient_id}", response_model=PatientRead)
async def get_patient(
    patient_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Patient:
    trace_id = new_trace_id()
    await PermissionService(session).require_read(
        user=current_user,
        patient_id=patient_id,
        action="patient.read",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )
    patient = await session.get(Patient, patient_id)
    if patient is None or patient.deleted_at is not None:
        from hospital_ai.core.errors import NotFoundError

        raise NotFoundError("Patient not found.")
    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="patient.read",
        object_type="patient",
        object_id=patient_id,
        patient_id=patient_id,
        outcome="allowed",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )
    await session.commit()
    return patient
