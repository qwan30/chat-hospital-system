from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.models import User
from hospital_ai.schemas.hms import HmsAppointmentImportResponse, HmsAppointmentSummaryImport
from hospital_ai.services.hms_appointments import (
    HMS_APPOINTMENT_SOURCE_FAMILY,
    HMS_SOURCE_SYSTEM,
    HmsAppointmentEvidenceImporter,
)
from hospital_ai.services.hms_sync import HmsSyncService
from hospital_ai.services.permissions import PermissionService

router = APIRouter()


# ── Existing manual import endpoint ───────────────────────────────


@router.post(
    "/appointments/import",
    response_model=HmsAppointmentImportResponse,
    response_model_by_alias=False,
)
async def import_hms_appointment_summary(
    payload: HmsAppointmentSummaryImport,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> HmsAppointmentImportResponse:
    document = await HmsAppointmentEvidenceImporter(session, settings).import_summary(
        user=current_user,
        payload=payload,
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
    )
    return HmsAppointmentImportResponse(
        document_id=document.id,
        patient_id=document.patient_id,
        source_appointment_id=payload.source_appointment_id,
        document_title=document.title,
        source_family=HMS_APPOINTMENT_SOURCE_FAMILY,
        source_system=HMS_SOURCE_SYSTEM,
        status=document.status,
    )


# ── HMS sync endpoints (pull from HMS REST API) ───────────────────


class HmsSyncRequest(BaseModel):
    patient_id: UUID


class HmsSyncResponse(BaseModel):
    patient_id: UUID
    synced: Dict[str, int] = Field(default_factory=dict)
    message: str = "Sync completed."


@router.post("/sync/appointments", response_model=HmsSyncResponse)
async def sync_appointments(
    payload: HmsSyncRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> HmsSyncResponse:
    trace_id = new_trace_id()
    await _require_hms_sync_write(
        request=request,
        session=session,
        current_user=current_user,
        patient_id=payload.patient_id,
        action="hms.appointments.sync",
        trace_id=trace_id,
    )
    service = HmsSyncService(session, settings)
    docs = await service.sync_appointments(
        patient_id=payload.patient_id,
        actor_user_id=current_user.id,
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )
    return HmsSyncResponse(
        patient_id=payload.patient_id,
        synced={"appointments": len(docs)},
        message=f"Synced {len(docs)} appointment(s).",
    )


@router.post("/sync/lab-results", response_model=HmsSyncResponse)
async def sync_lab_results(
    payload: HmsSyncRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> HmsSyncResponse:
    trace_id = new_trace_id()
    await _require_hms_sync_write(
        request=request,
        session=session,
        current_user=current_user,
        patient_id=payload.patient_id,
        action="hms.lab_results.sync",
        trace_id=trace_id,
    )
    service = HmsSyncService(session, settings)
    docs = await service.sync_lab_results(
        patient_id=payload.patient_id,
        actor_user_id=current_user.id,
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )
    return HmsSyncResponse(
        patient_id=payload.patient_id,
        synced={"lab_results": len(docs)},
        message=f"Synced {len(docs)} lab result(s).",
    )


@router.post("/sync/medical-records", response_model=HmsSyncResponse)
async def sync_medical_records(
    payload: HmsSyncRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> HmsSyncResponse:
    trace_id = new_trace_id()
    await _require_hms_sync_write(
        request=request,
        session=session,
        current_user=current_user,
        patient_id=payload.patient_id,
        action="hms.medical_records.sync",
        trace_id=trace_id,
    )
    service = HmsSyncService(session, settings)
    docs = await service.sync_medical_records(
        patient_id=payload.patient_id,
        actor_user_id=current_user.id,
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )
    return HmsSyncResponse(
        patient_id=payload.patient_id,
        synced={"medical_records": len(docs)},
        message=f"Synced {len(docs)} medical record(s).",
    )


@router.post("/sync/full", response_model=HmsSyncResponse)
async def sync_full(
    payload: HmsSyncRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> HmsSyncResponse:
    trace_id = new_trace_id()
    await _require_hms_sync_write(
        request=request,
        session=session,
        current_user=current_user,
        patient_id=payload.patient_id,
        action="hms.full.sync",
        trace_id=trace_id,
    )
    service = HmsSyncService(session, settings)
    result = await service.sync_full(
        patient_id=payload.patient_id,
        actor_user_id=current_user.id,
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )
    return HmsSyncResponse(
        patient_id=payload.patient_id,
        synced=result,
        message=f"Full sync completed — {result['total']} record(s).",
    )


class HmsHealthResponse(BaseModel):
    hms_reachable: bool
    hms_url: str


@router.get("/health", response_model=HmsHealthResponse)
async def hms_health(
    settings: Settings = Depends(get_settings),
) -> HmsHealthResponse:
    from hospital_ai.services.hms_connector import HmsApiClient

    client = HmsApiClient(settings)
    reachable = await client.health_check()
    return HmsHealthResponse(
        hms_reachable=reachable,
        hms_url=settings.hms_base_url,
    )


async def _require_hms_sync_write(
    *,
    request: Request,
    session: AsyncSession,
    current_user: User,
    patient_id: UUID,
    action: str,
    trace_id: str,
) -> None:
    await PermissionService(session).require_upload_or_admin_role(
        user=current_user,
        patient_id=patient_id,
        action=action,
        trace_id=trace_id,
        object_type="hms_sync",
        object_id=patient_id,
        ip_address=get_request_ip(request),
    )
