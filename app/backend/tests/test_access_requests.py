import pytest
from pydantic import ValidationError
from sqlalchemy import select
from starlette.requests import Request

from hospital_ai.api.routes.access_requests import AccessRequestCreate, create_access_request
from hospital_ai.api.routes.patients import get_patient_overview
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_BOB_ID
from hospital_ai.db.models import AuditLog, User


def _request(method: str = "POST", path: str = "/") -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [],
            "client": ("testclient", 50000),
        }
    )


@pytest.mark.asyncio
async def test_access_request_flow(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    # settings: disable HMS sync to use local DB permission checks
    settings.hms_sync_enabled = False

    # Bob is initially unauthorized for Doctor (should raise PermissionDeniedError)
    with pytest.raises(PermissionDeniedError):
        await get_patient_overview(
            patient_id=PATIENT_BOB_ID,
            request=_request(method="GET", path=f"/api/v1/patients/{PATIENT_BOB_ID}/overview"),
            session=session,
            current_user=doctor,
            settings=settings,
        )

    # Submit temporary access request justification (length >= 15)
    payload = AccessRequestCreate(
        patient_id=PATIENT_BOB_ID, justification="Attending physician reviewing cardiologist notes for consult request."
    )
    res = await create_access_request(
        payload=payload,
        request=_request(path="/api/v1/access-requests"),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    assert "granted" in res.message.lower()
    assert res.patient_id == PATIENT_BOB_ID

    # Verify that get_patient_overview is now ALLOWED!
    overview = await get_patient_overview(
        patient_id=PATIENT_BOB_ID,
        request=_request(method="GET", path=f"/api/v1/patients/{PATIENT_BOB_ID}/overview"),
        session=session,
        current_user=doctor,
        settings=settings,
    )
    assert overview.patient_id == PATIENT_BOB_ID

    # Verify audit log entry was created
    stmt = select(AuditLog).where(AuditLog.action == "access_request.create")
    audit_res = await session.execute(stmt)
    audit_entries = audit_res.scalars().all()
    assert len(audit_entries) == 1
    assert audit_entries[0].patient_id == PATIENT_BOB_ID
    assert audit_entries[0].meta.get("justification") == payload.justification


@pytest.mark.asyncio
async def test_access_request_validation():
    # Should raise validation error if justification < 15 characters
    with pytest.raises(ValidationError):
        AccessRequestCreate(patient_id=PATIENT_BOB_ID, justification="Too short")
