from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError
from sqlalchemy import select, update
from starlette.requests import Request

from hospital_ai.api.routes.patients import PatientCreate, create_patient, search_patients
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.core.security import PATIENT_READ_SCOPES
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_ELEANOR_ID
from hospital_ai.db.models import AuditLog, PatientPermission, User


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


def _post_request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/patients",
            "headers": [],
            "client": ("testclient", 50000),
        }
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["doctor", "nurse", "pharmacist", "lab_staff", "security"])
async def test_create_patient_denies_non_records_roles(session_and_settings, role):
    session, _ = session_and_settings
    user = User(email=f"{role}@test.local", full_name=role, role=role)
    session.add(user)
    await session.commit()

    with pytest.raises(PermissionDeniedError):
        await create_patient(
            PatientCreate(mrn="MRN-90001", full_name="Synthetic Person"),
            _post_request(),
            session,
            user,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["records_staff", "admin"])
async def test_create_patient_allows_records_roles(session_and_settings, role):
    session, _ = session_and_settings
    user = User(email=f"{role}@test.local", full_name=role, role=role)
    session.add(user)
    await session.commit()

    patient = await create_patient(
        PatientCreate(mrn="MRN-90002", full_name="Synthetic Person"),
        _post_request(),
        session,
        user,
    )

    assert patient.mrn == "MRN-90002"


@pytest.mark.asyncio
async def test_create_patient_grants_no_implicit_patient_permissions(session_and_settings):
    session, _ = session_and_settings
    user = User(email="records@test.local", full_name="Records Staff", role="records_staff")
    session.add(user)
    await session.commit()

    patient = await create_patient(
        PatientCreate(mrn="MRN-90003", full_name="Synthetic Person"),
        _post_request(),
        session,
        user,
    )
    permissions = list(
        (
            await session.scalars(
                select(PatientPermission).where(
                    PatientPermission.user_id == user.id,
                    PatientPermission.patient_id == patient.id,
                )
            )
        ).all()
    )

    assert permissions == []


@pytest.mark.parametrize(
    "payload",
    [
        {"mrn": "MRN-90004", "full_name": ""},
        {"mrn": "MRN-90004", "full_name": "   "},
        {"mrn": "mrn-90004", "full_name": "Synthetic Person"},
        {"mrn": "MRN-90004", "full_name": "Synthetic Person", "status": "discharged"},
    ],
)
def test_patient_create_rejects_invalid_input(payload):
    with pytest.raises(ValidationError):
        PatientCreate(**payload)


@pytest.mark.asyncio
async def test_create_patient_audit_omits_phi(session_and_settings):
    session, _ = session_and_settings
    user = User(email="records-audit@test.local", full_name="Records Staff", role="records_staff")
    session.add(user)
    await session.commit()

    patient = await create_patient(
        PatientCreate(
            mrn="MRN-90005",
            full_name="  Synthetic Person  ",
            department="Records",
            status="stable",
        ),
        _post_request(),
        session,
        user,
    )
    audit_log = await session.scalar(
        select(AuditLog).where(
            AuditLog.action == "patient.create",
            AuditLog.object_id == patient.id,
        )
    )

    assert patient.full_name == "Synthetic Person"
    assert audit_log is not None
    assert audit_log.meta == {"source": "patient_registration"}
    assert "mrn" not in audit_log.meta
    assert "full_name" not in audit_log.meta


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
        .values(deleted_at=datetime.now(UTC))
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
        .values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
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
