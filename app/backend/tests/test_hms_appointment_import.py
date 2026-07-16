import uuid
from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select, update
from starlette.requests import Request

from hospital_ai.api.routes.chat_threads import ask_thread_message, create_thread
from hospital_ai.api.routes.hms import import_hms_appointment_summary
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID, RECORDS_ID
from hospital_ai.db.models import AiQuery, ChatMessage, Document, PatientPermission, User
from hospital_ai.schemas.chat_threads import ChatThreadCreate, ChatThreadMessageRequest
from hospital_ai.schemas.hms import HmsAppointmentSummaryImport

APPOINTMENT_ID = uuid.UUID("30000000-0000-0000-0000-000000000101")


def _request(method: str = "POST", path: str = "/api/v1/hms/appointments/import") -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [],
            "client": ("testclient", 50000),
        }
    )


def _appointment_payload(
    *,
    appointment_id: uuid.UUID = APPOINTMENT_ID,
    patient_id: uuid.UUID = PATIENT_ALICE_ID,
    source_patient_id: uuid.UUID = PATIENT_ALICE_ID,
) -> HmsAppointmentSummaryImport:
    return HmsAppointmentSummaryImport(
        source_appointment_id=appointment_id,
        patient_id=patient_id,
        source_patient_id=source_patient_id,
        appointment_date=date(2026, 4, 28),
        status="CHECKED_IN",
        department="Internal Medicine",
        doctor_name="Dr. Dev Doctor",
        start_time="09:00",
        end_time="09:30",
        reason="Synthetic follow-up appointment",
        symptoms="Synthetic dizziness and medication review notes.",
        vital_signs_summary="Blood pressure 128/78, heart rate 78, oxygen saturation 98%.",
        follow_up_summary="Review symptoms and medication reconciliation.",
    )


@pytest.mark.asyncio
async def test_hms_appointment_import_becomes_permission_filtered_patient_evidence(session_and_settings):
    session, settings = session_and_settings
    records_user = await session.get(User, RECORDS_ID)
    doctor = await session.get(User, DOCTOR_ID)

    imported = await import_hms_appointment_summary(
        payload=_appointment_payload(),
        request=_request(),
        session=session,
        current_user=records_user,
        settings=settings,
    )

    assert imported.source_system == "hospital-management-system"
    assert imported.source_family == "appointments"
    assert imported.patient_id == PATIENT_ALICE_ID

    thread = await create_thread(
        payload=ChatThreadCreate(
            title="Alice appointment review",
            scope="patient-linked",
            patient_id=PATIENT_ALICE_ID,
        ),
        request=_request(path="/api/v1/chat-threads"),
        session=session,
        current_user=doctor,
    )

    response = await ask_thread_message(
        thread_id=thread.id,
        payload=ChatThreadMessageRequest(question="What is the appointment status and vital signs?", top_k=5),
        request=_request(path=f"/api/v1/chat-threads/{thread.id}/messages"),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    citation = response.assistant_message.citations[0]
    assert citation.document_id == imported.document_id
    assert citation.content is not None
    assert "HMS appointment summary" in citation.content
    assert citation.metadata["source_system"] == "hospital-management-system"
    assert citation.metadata["source_family"] == "appointments"
    assert citation.metadata["source_record_id"] == str(APPOINTMENT_ID)
    assert citation.metadata["patient_permission_required"] is True
    assert "CHECKED_IN" in response.assistant_message.content
    assert "Blood pressure 128/78" in response.assistant_message.content


@pytest.mark.asyncio
async def test_hms_appointment_import_requires_records_or_admin_scope(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    with pytest.raises(PermissionDeniedError):
        await import_hms_appointment_summary(
            payload=_appointment_payload(),
            request=_request(),
            session=session,
            current_user=doctor,
            settings=settings,
        )


def test_hms_appointment_import_rejects_mismatched_patient_ownership():
    with pytest.raises(ValidationError):
        _appointment_payload(patient_id=PATIENT_ALICE_ID, source_patient_id=PATIENT_BOB_ID)


@pytest.mark.asyncio
async def test_revoked_permission_blocks_hms_appointment_evidence_before_query(session_and_settings):
    session, settings = session_and_settings
    records_user = await session.get(User, RECORDS_ID)
    doctor = await session.get(User, DOCTOR_ID)
    await import_hms_appointment_summary(
        payload=_appointment_payload(appointment_id=uuid.UUID("30000000-0000-0000-0000-000000000102")),
        request=_request(),
        session=session,
        current_user=records_user,
        settings=settings,
    )
    thread = await create_thread(
        payload=ChatThreadCreate(
            title="Revoked HMS appointment review",
            scope="patient-linked",
            patient_id=PATIENT_ALICE_ID,
        ),
        request=_request(path="/api/v1/chat-threads"),
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
        await ask_thread_message(
            thread_id=thread.id,
            payload=ChatThreadMessageRequest(question="What is the appointment status?", top_k=5),
            request=_request(path=f"/api/v1/chat-threads/{thread.id}/messages"),
            session=session,
            current_user=doctor,
            settings=settings,
        )

    message_count = await session.scalar(select(func.count()).select_from(ChatMessage))
    query_count = await session.scalar(select(func.count()).select_from(AiQuery))
    assert message_count == 0
    assert query_count == 0


@pytest.mark.asyncio
async def test_deleted_hms_source_record_is_not_retrieved(session_and_settings):
    session, settings = session_and_settings
    records_user = await session.get(User, RECORDS_ID)
    doctor = await session.get(User, DOCTOR_ID)
    imported = await import_hms_appointment_summary(
        payload=_appointment_payload(appointment_id=uuid.UUID("30000000-0000-0000-0000-000000000103")),
        request=_request(),
        session=session,
        current_user=records_user,
        settings=settings,
    )
    await session.execute(
        update(Document)
        .where(Document.id == imported.document_id)
        .values(deleted_at=datetime.now(UTC), status="archived")
    )
    await session.commit()
    thread = await create_thread(
        payload=ChatThreadCreate(
            title="Deleted HMS appointment review",
            scope="patient-linked",
            patient_id=PATIENT_ALICE_ID,
        ),
        request=_request(path="/api/v1/chat-threads"),
        session=session,
        current_user=doctor,
    )

    response = await ask_thread_message(
        thread_id=thread.id,
        payload=ChatThreadMessageRequest(question="What is the appointment status?", top_k=5),
        request=_request(path=f"/api/v1/chat-threads/{thread.id}/messages"),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    assert response.assistant_message.citations == []
    assert "could not find authorized evidence" in response.assistant_message.content.lower()
