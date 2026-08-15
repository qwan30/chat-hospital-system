from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import select, update
from starlette.requests import Request

from hospital_ai.api.routes.chat_threads import (
    add_thread_participant,
    create_thread,
    list_thread_participants,
    remove_thread_participant,
    update_thread_participant,
)
from hospital_ai.core.errors import PermissionDeniedError, ValidationAppError
from hospital_ai.db.migrations import ADMIN_ID, DOCTOR_ID, PATIENT_ALICE_ID, RECORDS_ID
from hospital_ai.db.models import (
    AuditLog,
    ChatThread,
    ChatThreadParticipant,
    PatientPermission,
    User,
)
from hospital_ai.schemas.chat_threads import (
    ChatThreadCreate,
    ChatThreadParticipantCreate,
    ChatThreadParticipantUpdate,
)


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
async def test_owner_can_add_list_update_and_remove_authorized_participant(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    thread = await create_thread(
        payload=ChatThreadCreate(
            title="Shared Alice thread",
            scope="patient-linked",
            patient_id=PATIENT_ALICE_ID,
        ),
        request=_request(),
        session=session,
        current_user=doctor,
    )

    added = await add_thread_participant(
        thread_id=thread.id,
        payload=ChatThreadParticipantCreate(user_id=ADMIN_ID, access_level="read"),
        request=_request(),
        session=session,
        current_user=doctor,
    )

    assert added.user_id == ADMIN_ID
    assert added.access_level == "read"
    assert added.can_share is False
    assert (await session.get(ChatThread, thread.id)).visibility == "shared"

    participants = await list_thread_participants(
        thread_id=thread.id,
        request=_request("GET"),
        session=session,
        current_user=doctor,
    )
    assert [participant.access_level for participant in participants.items] == ["owner", "read"]
    owner_participant = participants.items[0]

    with pytest.raises(ValidationAppError):
        await remove_thread_participant(
            thread_id=thread.id,
            participant_id=owner_participant.id,
            request=_request("DELETE"),
            session=session,
            current_user=doctor,
        )

    updated = await update_thread_participant(
        thread_id=thread.id,
        participant_id=added.id,
        payload=ChatThreadParticipantUpdate(access_level="write", can_share=True),
        request=_request("PATCH"),
        session=session,
        current_user=doctor,
    )
    assert updated.access_level == "write"
    assert updated.can_share is True

    removed = await remove_thread_participant(
        thread_id=thread.id,
        participant_id=added.id,
        request=_request("DELETE"),
        session=session,
        current_user=doctor,
    )
    assert removed.id == added.id

    participants_after_remove = await list_thread_participants(
        thread_id=thread.id,
        request=_request("GET"),
        session=session,
        current_user=doctor,
    )
    assert [participant.user_id for participant in participants_after_remove.items] == [DOCTOR_ID]


@pytest.mark.asyncio
async def test_non_owner_cannot_share_thread_and_denial_is_audited(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    records_user = await session.get(User, RECORDS_ID)
    thread = await create_thread(
        payload=ChatThreadCreate(title="Owner only thread"),
        request=_request(),
        session=session,
        current_user=doctor,
    )

    with pytest.raises(PermissionDeniedError):
        await add_thread_participant(
            thread_id=thread.id,
            payload=ChatThreadParticipantCreate(user_id=ADMIN_ID, access_level="read"),
            request=_request(),
            session=session,
            current_user=records_user,
        )

    audit_result = await session.execute(
        select(AuditLog).where(
            AuditLog.action == "chat_thread.participant.add",
            AuditLog.object_id == thread.id,
            AuditLog.outcome == "denied",
        )
    )
    assert audit_result.scalar_one().meta["reason"] == "thread_access_denied"


@pytest.mark.asyncio
async def test_patient_thread_share_requires_target_patient_read_permission(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    thread = await create_thread(
        payload=ChatThreadCreate(
            title="Alice share denied",
            scope="patient-linked",
            patient_id=PATIENT_ALICE_ID,
        ),
        request=_request(),
        session=session,
        current_user=doctor,
    )

    with pytest.raises(PermissionDeniedError):
        await add_thread_participant(
            thread_id=thread.id,
            payload=ChatThreadParticipantCreate(user_id=RECORDS_ID, access_level="read"),
            request=_request(),
            session=session,
            current_user=doctor,
        )

    participant_result = await session.execute(
        select(ChatThreadParticipant).where(
            ChatThreadParticipant.thread_id == thread.id,
            ChatThreadParticipant.user_id == RECORDS_ID,
        )
    )
    assert participant_result.scalar_one_or_none() is None

    audit_result = await session.execute(
        select(AuditLog).where(
            AuditLog.action == "chat_thread.participant.add",
            AuditLog.object_id == thread.id,
            AuditLog.patient_id == PATIENT_ALICE_ID,
            AuditLog.outcome == "denied",
        )
    )
    assert audit_result.scalar_one().meta["reason"] == "target_missing_patient_read_scope"


@pytest.mark.asyncio
async def test_revoked_owner_patient_permission_blocks_participant_management(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    thread = await create_thread(
        payload=ChatThreadCreate(
            title="Alice owner revoked",
            scope="patient-linked",
            patient_id=PATIENT_ALICE_ID,
        ),
        request=_request(),
        session=session,
        current_user=doctor,
    )
    await session.execute(
        update(PatientPermission)
        .where(PatientPermission.user_id == DOCTOR_ID, PatientPermission.patient_id == PATIENT_ALICE_ID)
        .values(deleted_at=datetime.now(UTC))
    )
    await session.commit()

    with pytest.raises(PermissionDeniedError):
        await list_thread_participants(
            thread_id=thread.id,
            request=_request("GET"),
            session=session,
            current_user=doctor,
        )

    audit_result = await session.execute(
        select(AuditLog).where(
            AuditLog.action == "chat_thread.participants.read",
            AuditLog.object_id == thread.id,
            AuditLog.patient_id == PATIENT_ALICE_ID,
            AuditLog.outcome == "denied",
        )
    )
    assert audit_result.scalar_one() is not None
