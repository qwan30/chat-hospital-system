from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import select, update
from starlette.requests import Request

from hospital_ai.api.routes.chat_threads import (
    archive_thread,
    create_thread,
    get_thread,
    list_threads,
    update_thread,
)
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID, RECORDS_ID
from hospital_ai.db.models import (
    AuditLog,
    ChatThread,
    ChatThreadParticipant,
    PatientPermission,
    User,
)
from hospital_ai.schemas.chat_threads import ChatThreadCreate, ChatThreadUpdate


def _request(method: str = "POST") -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": "/api/v1/chat-threads",
            "headers": [],
            "client": ("testclient", 50000),
        }
    )


@pytest.mark.asyncio
async def test_create_list_update_and_archive_general_thread(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    created = await create_thread(
        payload=ChatThreadCreate(title="Shift handoff"),
        request=_request(),
        session=session,
        current_user=doctor,
    )

    assert created.title == "Shift handoff"
    assert created.scope == "general"
    assert created.owner_user_id == DOCTOR_ID

    listed = await list_threads(session=session, current_user=doctor)
    assert [thread.id for thread in listed.items] == [created.id]

    updated = await update_thread(
        thread_id=created.id,
        payload=ChatThreadUpdate(title="Updated handoff"),
        request=_request("PATCH"),
        session=session,
        current_user=doctor,
    )
    assert updated.title == "Updated handoff"

    archived = await archive_thread(
        thread_id=created.id,
        request=_request("DELETE"),
        session=session,
        current_user=doctor,
    )
    assert archived.status == "archived"

    participant_result = await session.execute(
        select(ChatThreadParticipant).where(ChatThreadParticipant.thread_id == created.id)
    )
    participant = participant_result.scalar_one()
    assert participant.user_id == DOCTOR_ID
    assert participant.access_level == "owner"
    assert participant.can_share is True

    audit_result = await session.execute(
        select(AuditLog.action).where(AuditLog.object_id == created.id).order_by(AuditLog.created_at)
    )
    assert list(audit_result.scalars()) == [
        "chat_thread.create",
        "chat_thread.update",
        "chat_thread.archive",
    ]


@pytest.mark.asyncio
async def test_patient_thread_requires_active_patient_permission(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    thread = await create_thread(
        payload=ChatThreadCreate(
            title="Alice patient review",
            scope="patient-linked",
            patient_id=PATIENT_ALICE_ID,
        ),
        request=_request(),
        session=session,
        current_user=doctor,
    )

    assert thread.patient_id == PATIENT_ALICE_ID

    await session.execute(
        update(PatientPermission)
        .where(PatientPermission.user_id == DOCTOR_ID, PatientPermission.patient_id == PATIENT_ALICE_ID)
        .values(deleted_at=datetime.now(UTC))
    )
    await session.commit()

    with pytest.raises(PermissionDeniedError):
        await get_thread(
            thread_id=thread.id,
            request=_request("GET"),
            session=session,
            current_user=doctor,
        )

    audit_result = await session.execute(
        select(AuditLog).where(
            AuditLog.action == "chat_thread.read",
            AuditLog.object_id == thread.id,
            AuditLog.outcome == "denied",
        )
    )
    assert audit_result.scalar_one().patient_id == PATIENT_ALICE_ID


@pytest.mark.asyncio
async def test_unauthorized_participant_cannot_read_thread(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    records_user = await session.get(User, RECORDS_ID)

    created = await create_thread(
        payload=ChatThreadCreate(title="Private thread"),
        request=_request(),
        session=session,
        current_user=doctor,
    )

    with pytest.raises(PermissionDeniedError):
        await get_thread(
            thread_id=created.id,
            request=_request("GET"),
            session=session,
            current_user=records_user,
        )

    audit_result = await session.execute(
        select(AuditLog).where(
            AuditLog.action == "chat_thread.read",
            AuditLog.object_id == created.id,
            AuditLog.outcome == "denied",
        )
    )
    assert audit_result.scalar_one().meta["reason"] == "thread_access_denied"


@pytest.mark.asyncio
async def test_patient_thread_create_denied_for_unauthorized_patient(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    with pytest.raises(PermissionDeniedError):
        await create_thread(
            payload=ChatThreadCreate(
                title="Bob review",
                scope="patient-linked",
                patient_id=PATIENT_BOB_ID,
            ),
            request=_request(),
            session=session,
            current_user=doctor,
        )

    thread_result = await session.execute(select(ChatThread).where(ChatThread.patient_id == PATIENT_BOB_ID))
    assert thread_result.scalars().all() == []

    audit_result = await session.execute(
        select(AuditLog).where(
            AuditLog.action == "chat_thread.create",
            AuditLog.patient_id == PATIENT_BOB_ID,
            AuditLog.outcome == "denied",
        )
    )
    assert audit_result.scalar_one() is not None
