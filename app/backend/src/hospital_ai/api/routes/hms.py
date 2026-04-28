from fastapi import APIRouter, Depends, Request
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

router = APIRouter()


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
