from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from hospital_ai.db.models import Base
from hospital_ai.schemas.chat_threads import ChatMessageCreate, ChatThreadCreate


def test_chat_thread_models_define_shared_thread_contract():
    tables = Base.metadata.tables

    assert {"chat_threads", "chat_thread_participants", "chat_messages"}.issubset(tables)

    thread_columns = set(tables["chat_threads"].columns.keys())
    assert {
        "title",
        "scope",
        "visibility",
        "status",
        "owner_user_id",
        "patient_id",
        "created_trace_id",
        "last_message_at",
    }.issubset(thread_columns)

    participant_columns = set(tables["chat_thread_participants"].columns.keys())
    assert {
        "thread_id",
        "user_id",
        "access_level",
        "can_share",
        "added_by_user_id",
        "created_trace_id",
        "last_read_at",
    }.issubset(participant_columns)

    message_columns = set(tables["chat_messages"].columns.keys())
    assert {
        "thread_id",
        "sender_user_id",
        "ai_query_id",
        "patient_id",
        "role",
        "scope",
        "content",
        "patient_permission_state",
        "citations",
        "metadata",
        "trace_id",
    }.issubset(message_columns)


def test_chat_thread_contract_requires_patient_context_only_for_patient_scope():
    patient_id = uuid.uuid4()

    assert ChatThreadCreate(title="General", scope="general").patient_id is None
    assert (
        ChatThreadCreate(
            title="Patient",
            scope="patient-linked",
            patient_id=patient_id,
        ).patient_id
        == patient_id
    )

    with pytest.raises(ValidationError, match="patient-linked chat requires patient_id"):
        ChatThreadCreate(title="Patient", scope="patient-linked")

    with pytest.raises(ValidationError, match="general chat threads must not include patient_id"):
        ChatThreadCreate(title="General", scope="general", patient_id=patient_id)


def test_chat_message_contract_preserves_permission_state_and_scope_boundary():
    patient_id = uuid.uuid4()

    message = ChatMessageCreate(
        role="assistant",
        content="Cited answer",
        scope="patient-linked",
        patient_id=patient_id,
        patient_permission_state="allowed",
    )

    assert message.patient_permission_state == "allowed"
    assert message.citations == []
    assert message.metadata == {}

    with pytest.raises(ValidationError, match="patient-linked chat requires patient_id"):
        ChatMessageCreate(content="Missing patient", scope="patient-linked")
