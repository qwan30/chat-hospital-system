import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from starlette.requests import Request

from hospital_ai.api.routes.access_requests import (
    AccessRequestCreate,
    AccessRequestReview,
    create_access_request,
    get_access_request,
    list_access_requests,
    review_access_request,
)
from hospital_ai.api.routes.patients import get_patient_overview
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.db.migrations import ADMIN_ID, DOCTOR_ID, PATIENT_BOB_ID
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

    assert "submitted" in res.message.lower()
    assert res.patient_id == PATIENT_BOB_ID
    assert res.status == "pending"

    # Verify that get_patient_overview is still DENIED!
    with pytest.raises(PermissionDeniedError):
        await get_patient_overview(
            patient_id=PATIENT_BOB_ID,
            request=_request(method="GET", path=f"/api/v1/patients/{PATIENT_BOB_ID}/overview"),
            session=session,
            current_user=doctor,
            settings=settings,
        )

    # Admin approves the request
    admin = await session.get(User, ADMIN_ID)
    review_payload = AccessRequestReview(status="approved", notes="LGTM")
    review_res = await review_access_request(
        request_id=res.id,
        payload=review_payload,
        request=_request(method="PUT", path=f"/api/v1/access-requests/{res.id}/review"),
        session=session,
        current_user=admin,
    )
    assert review_res.status == "approved"

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


@pytest.mark.asyncio
async def test_get_and_list_access_requests(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    admin = await session.get(User, ADMIN_ID)

    settings.hms_sync_enabled = False

    payload = AccessRequestCreate(patient_id=PATIENT_BOB_ID, justification="Testing listing access requests endpoints")
    res = await create_access_request(
        payload=payload,
        request=_request(path="/api/v1/access-requests"),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    # List endpoints
    with pytest.raises(HTTPException):
        await list_access_requests(session=session, current_user=doctor)

    requests_list = await list_access_requests(session=session, current_user=admin)
    assert len(requests_list) >= 1
    assert any(req.id == res.id for req in requests_list)

    # Get endpoint
    detail = await get_access_request(request_id=res.id, session=session, current_user=admin)
    assert detail.id == res.id
    assert detail.status == "pending"
    assert detail.justification == payload.justification


@pytest.mark.asyncio
async def test_access_request_review_validation_and_pending_info(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    admin = await session.get(User, ADMIN_ID)
    settings.hms_sync_enabled = False

    payload = AccessRequestCreate(
        patient_id=PATIENT_BOB_ID, justification="Requesting access for clinical medication safety pre-check review."
    )
    res = await create_access_request(
        payload=payload,
        request=_request(path="/api/v1/access-requests"),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    # Deny without notes should raise HTTPException(400)
    with pytest.raises(HTTPException) as excinfo:
        await review_access_request(
            request_id=res.id,
            payload=AccessRequestReview(status="denied", notes=""),
            request=_request(method="PUT", path=f"/api/v1/access-requests/{res.id}/review"),
            session=session,
            current_user=admin,
        )
    assert excinfo.value.status_code == 400
    assert "Notes are required" in excinfo.value.detail

    # pending_info without notes should raise HTTPException(400)
    with pytest.raises(HTTPException) as excinfo:
        await review_access_request(
            request_id=res.id,
            payload=AccessRequestReview(status="pending_info", notes=""),
            request=_request(method="PUT", path=f"/api/v1/access-requests/{res.id}/review"),
            session=session,
            current_user=admin,
        )
    assert excinfo.value.status_code == 400

    # pending_info with notes should succeed
    review_res = await review_access_request(
        request_id=res.id,
        payload=AccessRequestReview(
            status="pending_info", notes="Need more clinical context for this consult request."
        ),
        request=_request(method="PUT", path=f"/api/v1/access-requests/{res.id}/review"),
        session=session,
        current_user=admin,
    )
    assert review_res.status == "pending_info"

    # Now we can review the request again (e.g. approve it)
    approve_res = await review_access_request(
        request_id=res.id,
        payload=AccessRequestReview(status="approved", notes="Additional info provided, approved."),
        request=_request(method="PUT", path=f"/api/v1/access-requests/{res.id}/review"),
        session=session,
        current_user=admin,
    )
    assert approve_res.status == "approved"
