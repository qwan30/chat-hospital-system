from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import update
from starlette.requests import Request

from hospital_ai.api.routes.patients import search_patients
from hospital_ai.core.security import PATIENT_READ_SCOPES
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_ELEANOR_ID
from hospital_ai.db.models import PatientPermission, User


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/patients/search",
            "headers": [],
            "client": ("testclient", 50000),
        }
    )


@pytest.mark.asyncio
async def test_patient_search_returns_active_permission_match(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    response = await search_patients(
        request=_request(),
        q="Alice",
        limit=20,
        session=session,
        current_user=doctor,
    )

    assert [patient.id for patient in response.items] == [PATIENT_ALICE_ID]


@pytest.mark.asyncio
async def test_patient_search_excludes_revoked_permissions(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    await session.execute(
        update(PatientPermission)
        .where(
            PatientPermission.user_id == DOCTOR_ID,
            PatientPermission.patient_id.in_([PATIENT_ALICE_ID, PATIENT_ELEANOR_ID]),
            PatientPermission.scope.in_(PATIENT_READ_SCOPES),
        )
        .values(deleted_at=datetime.now(timezone.utc))
    )
    await session.commit()

    response = await search_patients(
        request=_request(),
        q=None,
        limit=20,
        session=session,
        current_user=doctor,
    )

    assert response.items == []


@pytest.mark.asyncio
async def test_patient_search_excludes_expired_permissions(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    await session.execute(
        update(PatientPermission)
        .where(
            PatientPermission.user_id == DOCTOR_ID,
            PatientPermission.patient_id.in_([PATIENT_ALICE_ID, PATIENT_ELEANOR_ID]),
            PatientPermission.scope.in_(PATIENT_READ_SCOPES),
        )
        .values(expires_at=datetime.now(timezone.utc) - timedelta(minutes=1))
    )
    await session.commit()

    response = await search_patients(
        request=_request(),
        q=None,
        limit=20,
        session=session,
        current_user=doctor,
    )

    assert response.items == []
