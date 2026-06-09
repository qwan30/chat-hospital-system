from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select, update
from starlette.requests import Request

from hospital_ai.api.routes.chat_threads import (
    archive_thread,
    ask_thread_message,
    create_thread,
    get_thread,
    list_thread_messages,
    list_threads,
)
from hospital_ai.core.errors import ExternalServiceError, PermissionDeniedError
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, RECORDS_ID
from hospital_ai.db.models import (
    AiQuery,
    AuditLog,
    ChatMessage,
    ChatThread,
    PatientPermission,
    User,
)
from hospital_ai.schemas.chat_threads import (
    ChatThreadCreate,
    ChatThreadDetail,
    ChatThreadMessageRequest,
)
from hospital_ai.services.chat import ChatGenerator
from tests.conftest import create_indexed_document


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
async def test_patient_thread_message_persists_question_answer_and_citations(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice allergy note",
        content="Alice has a documented allergy to penicillin.",
    )
    thread = await create_thread(
        payload=ChatThreadCreate(
            title="Alice care question",
            scope="patient-linked",
            patient_id=PATIENT_ALICE_ID,
        ),
        request=_request(),
        session=session,
        current_user=doctor,
    )

    response = await ask_thread_message(
        thread_id=thread.id,
        payload=ChatThreadMessageRequest(question="What allergy is documented?", top_k=5),
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    assert response.user_message.role == "user"
    assert response.user_message.sender_user_id == DOCTOR_ID
    assert response.user_message.patient_permission_state == "allowed"
    assert response.assistant_message.role == "assistant"
    assert response.assistant_message.ai_query_id is not None
    assert [citation.evidence_id for citation in response.assistant_message.citations] == ["E1"]
    assert response.assistant_message.metadata["confidence"] in {"low", "medium", "high"}

    persisted_thread = await session.get(ChatThread, thread.id)
    assert persisted_thread.last_message_at is not None

    listed = await list_thread_messages(
        thread_id=thread.id,
        request=_request("GET"),
        session=session,
        current_user=doctor,
    )
    assert [message.role for message in listed.items] == ["user", "assistant"]
    assert listed.items[1].ai_query_id == response.assistant_message.ai_query_id
    detail = ChatThreadDetail.from_orm(
        await get_thread(
            thread_id=thread.id,
            request=_request("GET"),
            session=session,
            current_user=doctor,
        )
    )
    assert detail.messages[1].metadata["confidence"] in {"low", "medium", "high"}

    audit_result = await session.execute(
        select(AuditLog).where(
            AuditLog.action == "chat_thread.message.create",
            AuditLog.object_id == thread.id,
            AuditLog.outcome == "allowed",
        )
    )
    assert audit_result.scalar_one().meta["ai_query_id"] == str(response.assistant_message.ai_query_id)


@pytest.mark.asyncio
async def test_thread_message_denied_participant_is_forbidden_and_audited(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    records_user = await session.get(User, RECORDS_ID)
    thread = await create_thread(
        payload=ChatThreadCreate(
            title="Private Alice thread",
            scope="patient-linked",
            patient_id=PATIENT_ALICE_ID,
        ),
        request=_request(),
        session=session,
        current_user=doctor,
    )

    with pytest.raises(PermissionDeniedError):
        await ask_thread_message(
            thread_id=thread.id,
            payload=ChatThreadMessageRequest(question="Can I read this?"),
            request=_request(),
            session=session,
            current_user=records_user,
            settings=settings,
        )

    with pytest.raises(PermissionDeniedError):
        await list_thread_messages(
            thread_id=thread.id,
            request=_request("GET"),
            session=session,
            current_user=records_user,
        )

    audit_result = await session.execute(
        select(AuditLog).where(
            AuditLog.object_id == thread.id,
            AuditLog.outcome == "denied",
        )
    )
    reasons = [row.meta["reason"] for row in audit_result.scalars()]
    assert reasons == ["thread_access_denied", "thread_access_denied"]


@pytest.mark.asyncio
async def test_revoked_patient_permission_blocks_thread_message_before_query(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    thread = await create_thread(
        payload=ChatThreadCreate(
            title="Revoked Alice thread",
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
        .values(deleted_at=datetime.now(timezone.utc))
    )
    await session.commit()

    with pytest.raises(PermissionDeniedError):
        await ask_thread_message(
            thread_id=thread.id,
            payload=ChatThreadMessageRequest(question="What changed?"),
            request=_request(),
            session=session,
            current_user=doctor,
            settings=settings,
        )

    message_count = await session.scalar(select(func.count()).select_from(ChatMessage))
    query_count = await session.scalar(select(func.count()).select_from(AiQuery))
    assert message_count == 0
    assert query_count == 0

    audit_result = await session.execute(
        select(AuditLog).where(
            AuditLog.action == "chat_thread.message.create",
            AuditLog.object_id == thread.id,
            AuditLog.patient_id == PATIENT_ALICE_ID,
            AuditLog.outcome == "denied",
        )
    )
    assert audit_result.scalar_one() is not None


@pytest.mark.asyncio
async def test_general_thread_message_uses_approved_non_phi_knowledge(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    thread = await create_thread(
        payload=ChatThreadCreate(title="General transfer policy", scope="general"),
        request=_request(),
        session=session,
        current_user=doctor,
    )

    response = await ask_thread_message(
        thread_id=thread.id,
        payload=ChatThreadMessageRequest(question="What approval is needed for a ward transfer?", top_k=5),
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    assert response.user_message.scope == "general"
    assert response.user_message.patient_id is None
    assert response.user_message.patient_permission_state == "not-required"
    assert response.assistant_message.scope == "general"
    assert response.assistant_message.patient_id is None
    assert response.assistant_message.patient_permission_state == "not-required"
    assert [citation.evidence_id for citation in response.assistant_message.citations] == ["E1"]
    assert response.assistant_message.citations[0].metadata["approved_non_phi"] is True
    assert response.assistant_message.citations[0].metadata["contains_phi"] is False

    query_count = await session.scalar(select(func.count()).select_from(AiQuery))
    assert query_count == 0

    audit_result = await session.execute(
        select(AuditLog).where(
            AuditLog.action == "chat_thread.message.create",
            AuditLog.object_id == thread.id,
            AuditLog.patient_id.is_(None),
            AuditLog.outcome == "allowed",
        )
    )
    assert audit_result.scalar_one().meta["source_scope"] == "general-hospital-knowledge"


@pytest.mark.asyncio
async def test_general_thread_message_cannot_leak_patient_chunks(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice confidential allergy note",
        content="Alice has a documented allergy to penicillin.",
    )
    thread = await create_thread(
        payload=ChatThreadCreate(title="General no patient data", scope="general"),
        request=_request(),
        session=session,
        current_user=doctor,
    )

    response = await ask_thread_message(
        thread_id=thread.id,
        payload=ChatThreadMessageRequest(question="What allergy is documented for Alice?", top_k=5),
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    assert response.assistant_message.patient_id is None
    assert response.assistant_message.citations == []
    assert "approved general hospital knowledge" in response.assistant_message.content

    message_count = await session.scalar(select(func.count()).select_from(ChatMessage))
    query_count = await session.scalar(select(func.count()).select_from(AiQuery))
    assert message_count == 2
    assert query_count == 0


@pytest.mark.asyncio
async def test_general_thread_invalid_citations_do_not_commit_partial_messages(
    session_and_settings,
    monkeypatch,
):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    thread = await create_thread(
        payload=ChatThreadCreate(title="General invalid citation", scope="general"),
        request=_request(),
        session=session,
        current_user=doctor,
    )

    async def missing_citation(_: ChatGenerator, __: str) -> str:
        return "This answer forgot to cite evidence."

    monkeypatch.setattr(ChatGenerator, "generate", missing_citation)

    with pytest.raises(ExternalServiceError):
        await ask_thread_message(
            thread_id=thread.id,
            payload=ChatThreadMessageRequest(question="What approval is needed for a ward transfer?", top_k=5),
            request=_request(),
            session=session,
            current_user=doctor,
            settings=settings,
        )

    await session.rollback()
    message_count = await session.scalar(select(func.count()).select_from(ChatMessage))
    query_count = await session.scalar(select(func.count()).select_from(AiQuery))
    assert message_count == 0
    assert query_count == 0


@pytest.mark.asyncio
async def test_patient_thread_invalid_citations_do_not_commit_orphaned_user_message(
    session_and_settings,
    monkeypatch,
):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice allergy note",
        content="Alice has a documented allergy to penicillin.",
    )
    thread = await create_thread(
        payload=ChatThreadCreate(
            title="Patient invalid citation",
            scope="patient-linked",
            patient_id=PATIENT_ALICE_ID,
        ),
        request=_request(),
        session=session,
        current_user=doctor,
    )

    async def invalid_citation(_: ChatGenerator, __: str) -> str:
        return "The record says this without a valid citation [E99]."

    monkeypatch.setattr(ChatGenerator, "generate", invalid_citation)

    with pytest.raises(ExternalServiceError):
        await ask_thread_message(
            thread_id=thread.id,
            payload=ChatThreadMessageRequest(question="What allergy is documented?", top_k=5),
            request=_request(),
            session=session,
            current_user=doctor,
            settings=settings,
        )

    message_count = await session.scalar(select(func.count()).select_from(ChatMessage))
    failed_query_count = await session.scalar(
        select(func.count()).select_from(AiQuery).where(AiQuery.status == "failed")
    )
    assert message_count == 0
    assert failed_query_count == 1


@pytest.mark.asyncio
async def test_archived_threads_are_hidden_from_default_thread_list(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    thread = await create_thread(
        payload=ChatThreadCreate(title="Archive me", scope="general"),
        request=_request(),
        session=session,
        current_user=doctor,
    )

    archived = await archive_thread(
        thread_id=thread.id,
        request=_request("DELETE"),
        session=session,
        current_user=doctor,
    )
    listed = await list_threads(session=session, current_user=doctor)

    assert archived.status == "archived"
    assert all(item.id != thread.id for item in listed.items)
