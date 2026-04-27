import pytest
from sqlalchemy import select

from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.core.security import PATIENT_READ_SCOPES, new_trace_id
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID, RECORDS_ID
from hospital_ai.db.models import AuditLog, Document, User
from hospital_ai.services.permissions import PermissionService, active_patient_permission_exists


def test_active_patient_permission_exists_uses_canonical_lifecycle_predicate():
    stmt = select(
        active_patient_permission_exists(
            user_id=DOCTOR_ID,
            patient_id=PATIENT_ALICE_ID,
            accepted_scopes=PATIENT_READ_SCOPES,
        )
    )
    sql = str(stmt.compile(compile_kwargs={"literal_binds": False})).lower()

    assert "exists" in sql
    assert "patient_permissions.user_id" in sql
    assert "patient_permissions.patient_id" in sql
    assert "patient_permissions.scope in" in sql
    assert "patient_permissions.deleted_at is null" in sql
    assert "patient_permissions.expires_at is null" in sql
    assert "patient_permissions.expires_at >" in sql


@pytest.mark.asyncio
async def test_doctor_can_read_assigned_patient(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    await PermissionService(session).require_read(
        user=doctor,
        patient_id=PATIENT_ALICE_ID,
        action="patient.read",
        trace_id=new_trace_id(),
    )


@pytest.mark.asyncio
async def test_unauthorized_patient_is_blocked_and_audited(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    with pytest.raises(PermissionDeniedError):
        await PermissionService(session).require_read(
            user=doctor,
            patient_id=PATIENT_BOB_ID,
            action="patient.read",
            trace_id="trace-denied",
        )

    result = await session.execute(
        select(AuditLog).where(
            AuditLog.actor_user_id == DOCTOR_ID,
            AuditLog.patient_id == PATIENT_BOB_ID,
            AuditLog.outcome == "denied",
        )
    )
    assert result.scalar_one().trace_id == "trace-denied"


@pytest.mark.asyncio
async def test_upload_denial_creates_no_document(session_and_settings):
    session, _ = session_and_settings
    records_user = await session.get(User, RECORDS_ID)

    with pytest.raises(PermissionDeniedError):
        await PermissionService(session).require_upload_or_admin_role(
            user=records_user,
            patient_id=PATIENT_BOB_ID,
            action="document.upload",
            trace_id="trace-upload-denied",
        )

    result = await session.execute(select(Document).where(Document.patient_id == PATIENT_BOB_ID))
    assert result.scalars().all() == []
