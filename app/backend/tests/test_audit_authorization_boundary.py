import uuid
import pytest
from hospital_ai.api.routes.audit import list_logs, list_events_alias
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.db.models import AuditLog, User
from hospital_ai.db.migrations import DOCTOR_ID, ADMIN_ID, SECURITY_ID

pytestmark = pytest.mark.asyncio

async def test_audit_logs_unauthorized(session_and_settings):
    session, settings = session_and_settings
    doctor_user = await session.get(User, DOCTOR_ID)
    
    with pytest.raises(PermissionDeniedError):
        await list_logs(
            patient_id=None,
            action=None,
            outcome=None,
            limit=50,
            session=session,
            current_user=doctor_user
        )

    with pytest.raises(PermissionDeniedError):
        await list_events_alias(
            patient_id=None,
            action=None,
            outcome=None,
            limit=50,
            session=session,
            current_user=doctor_user
        )

async def test_audit_logs_authorized_admin(session_and_settings):
    session, settings = session_and_settings
    admin_user = await session.get(User, ADMIN_ID)
    
    patient_id = uuid.uuid4()
    audit_log = AuditLog(
        actor_user_id=admin_user.id,
        action="test.action",
        object_type="test",
        patient_id=patient_id,
        outcome="allowed",
        trace_id="test-trace-1",
        meta={"access_token": "secret123", "password": "mypassword", "raw_prompt_phi": "patient has diabetes", "safe_key": "safe_value"}
    )
    session.add(audit_log)
    await session.commit()

    # test /logs
    result = await list_logs(
        patient_id=patient_id,
        action="test.action",
        outcome="allowed",
        limit=50,
        session=session,
        current_user=admin_user
    )
    
    assert len(result.items) == 1
    item = result.items[0]
    
    # Check that Pydantic alias/meta redaction happened
    assert item.metadata["access_token"] == "***REDACTED***"
    assert item.metadata["password"] == "***REDACTED***"
    assert item.metadata["raw_prompt_phi"] == "***REDACTED***"
    assert item.metadata["safe_key"] == "safe_value"
    
    # test /events
    result_events = await list_events_alias(
        patient_id=patient_id,
        action="test.action",
        outcome="allowed",
        limit=50,
        session=session,
        current_user=admin_user
    )
    assert len(result_events.items) == 1

async def test_audit_logs_authorized_security(session_and_settings):
    session, settings = session_and_settings
    security_user = await session.get(User, SECURITY_ID)
    
    result = await list_logs(
        patient_id=None,
        action=None,
        outcome=None,
        limit=50,
        session=session,
        current_user=security_user
    )
    assert result is not None
