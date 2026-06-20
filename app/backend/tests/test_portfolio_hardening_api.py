import pytest
from sqlalchemy import select
from starlette.requests import Request

from hospital_ai.api.routes.audit import list_logs
from hospital_ai.api.routes.documents import list_documents
from hospital_ai.api.routes.feedback import get_metrics_summary
from hospital_ai.api.routes.hms import HmsSyncRequest, sync_full
from hospital_ai.api.routes.settings import (
    SettingsUpdateRequest,
    get_admin_settings,
    update_admin_settings,
)
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.db.migrations import (
    ADMIN_ID,
    DOCTOR_ID,
    PATIENT_ALICE_ID,
    PATIENT_BOB_ID,
    RECORDS_ID,
    SECURITY_ID,
)
from hospital_ai.db.models import AuditLog, User
from tests.conftest import create_indexed_document


def _request(method: str = "GET", path: str = "/api/v1") -> Request:
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
async def test_document_list_is_permission_filtered_and_returns_items(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    admin = await session.get(User, ADMIN_ID)
    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Alice note",
        content="Alice clinical context.",
    )
    await create_indexed_document(
        session,
        patient_id=PATIENT_BOB_ID,
        uploaded_by=ADMIN_ID,
        title="Bob note",
        content="Bob clinical context.",
    )

    from hospital_ai.db.models import PatientPermission

    # Ensure admin has permissions to read Bob to pass the test since bypass is removed (Alice is added in migrations)
    session.add(PatientPermission(user_id=admin.id, patient_id=PATIENT_BOB_ID, scope="admin"))
    await session.commit()

    doctor_response = await list_documents(
        request=_request(path="/api/v1/documents"),
        patient_id=None,
        status=None,
        limit=50,
        session=session,
        current_user=doctor,
    )
    admin_response = await list_documents(
        request=_request(path="/api/v1/documents"),
        patient_id=None,
        status=None,
        limit=50,
        session=session,
        current_user=admin,
    )

    assert [document.patient_id for document in doctor_response.items] == [PATIENT_ALICE_ID]
    assert {document.patient_id for document in admin_response.items} == {
        PATIENT_ALICE_ID,
        PATIENT_BOB_ID,
    }


@pytest.mark.asyncio
async def test_settings_read_write_role_policy_and_denial_audit(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    security = await session.get(User, SECURITY_ID)
    admin = await session.get(User, ADMIN_ID)

    security_response = await get_admin_settings(
        request=_request(path="/api/v1/settings"),
        session=session,
        settings=settings,
        current_user=security,
    )
    assert security_response.rag.retrieval_top_k == settings.retrieval_top_k

    with pytest.raises(PermissionDeniedError):
        await update_admin_settings(
            payload=SettingsUpdateRequest(retrieval_top_k=7),
            request=_request(method="PUT", path="/api/v1/settings"),
            session=session,
            settings=settings,
            current_user=doctor,
        )

    denied = await session.execute(
        select(AuditLog).where(
            AuditLog.actor_user_id == DOCTOR_ID,
            AuditLog.action == "settings.update",
            AuditLog.outcome == "denied",
        )
    )
    assert denied.scalar_one().meta["role"] == "doctor"

    admin_response = await update_admin_settings(
        payload=SettingsUpdateRequest(retrieval_top_k=7),
        request=_request(method="PUT", path="/api/v1/settings"),
        session=session,
        settings=settings,
        current_user=admin,
    )
    assert admin_response.rag.retrieval_top_k == 7


@pytest.mark.asyncio
async def test_doctor_hms_sync_full_is_denied_and_audited(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    with pytest.raises(PermissionDeniedError):
        await sync_full(
            payload=HmsSyncRequest(patient_id=PATIENT_ALICE_ID),
            request=_request(method="POST", path="/api/v1/hms/sync/full"),
            session=session,
            settings=settings,
            current_user=doctor,
        )

    audit = await session.execute(
        select(AuditLog).where(
            AuditLog.actor_user_id == DOCTOR_ID,
            AuditLog.patient_id == PATIENT_ALICE_ID,
            AuditLog.action == "hms.full.sync",
            AuditLog.outcome == "denied",
        )
    )
    assert audit.scalar_one().object_type == "hms_sync"


@pytest.mark.asyncio
async def test_audit_logs_filter_by_action_and_outcome(session_and_settings):
    session, _ = session_and_settings
    security = await session.get(User, SECURITY_ID)
    session.add(
        AuditLog(
            actor_user_id=DOCTOR_ID,
            action="settings.update",
            object_type="system_setting",
            outcome="denied",
            trace_id="trace-filtered-denial",
            meta={},
        )
    )
    session.add(
        AuditLog(
            actor_user_id=ADMIN_ID,
            action="settings.update",
            object_type="system_setting",
            outcome="allowed",
            trace_id="trace-filtered-allowed",
            meta={},
        )
    )
    await session.commit()

    response = await list_logs(
        patient_id=None,
        action="settings.update",
        outcome="denied",
        limit=50,
        session=session,
        current_user=security,
    )

    assert [log.trace_id for log in response.items] == ["trace-filtered-denial"]


@pytest.mark.asyncio
async def test_metrics_summary_includes_audit_denial_count(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    session.add(
        AuditLog(
            actor_user_id=DOCTOR_ID,
            action="patient.read",
            object_type="patient",
            patient_id=PATIENT_BOB_ID,
            outcome="denied",
            trace_id="trace-denied-metrics",
            meta={},
        )
    )
    await session.commit()

    response = await get_metrics_summary(user=doctor, session=session)

    assert response.audit_deny_count == 1
