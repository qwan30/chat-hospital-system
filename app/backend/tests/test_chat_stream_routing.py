from __future__ import annotations

import json
import uuid
from datetime import date

import pytest
from starlette.requests import Request

from hospital_ai.api.routes.chat_stream import chat_stream
from hospital_ai.db.models import Patient, PatientPermission, User
from hospital_ai.schemas.chat import ChatRequest


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/chat/stream",
            "headers": [],
            "client": ("127.0.0.1", 50000),
        }
    )


def _parse_sse_events(body: bytes) -> list[dict]:
    text = body.decode("utf-8")
    events = []
    for line in text.strip().split("\n\n"):
        line = line.strip()
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


@pytest.fixture
async def sample_chat_patient(session_and_settings):
    session, _ = session_and_settings
    # Create doctor user
    doctor = User(
        id=uuid.uuid4(),
        email="doctor_stream@example.test",
        full_name="Dr. Stream Test",
        department="Cardiology",
        role="doctor",
    )
    # Create patient Bui Duc Hung
    patient = Patient(
        id=uuid.uuid4(),
        mrn="MRN-0015",
        full_name="Bùi Đức Hùng",
        dob=date(1978, 5, 20),
        department="Cardiology 4N",
        status="active",
    )
    perm = PatientPermission(
        user_id=doctor.id,
        patient_id=patient.id,
        scope="read",
    )
    session.add_all([doctor, patient, perm])
    await session.commit()
    return {"doctor": doctor, "patient": patient}


@pytest.mark.asyncio
async def test_chat_stream_resolves_patient_in_general_mode(session_and_settings, sample_chat_patient):
    session, settings = session_and_settings
    doctor = sample_chat_patient["doctor"]
    patient = sample_chat_patient["patient"]

    payload = ChatRequest(
        question="do you know bui duc hung patient?",
        patient_id=None,  # General mode
        top_k=5,
    )

    response = await chat_stream(
        payload=payload,
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )
    assert response.status_code == 200

    body = b""
    async for chunk in response.body_iterator:
        body += chunk.encode("utf-8")

    events = _parse_sse_events(body)
    event_types = [e.get("type") for e in events]
    assert "context_resolved" in event_types
    resolved_event = next(e for e in events if e.get("type") == "context_resolved")
    assert resolved_event["patient_id"] == str(patient.id)
    assert resolved_event["mrn"] == "MRN-0015"


@pytest.mark.asyncio
async def test_chat_stream_answers_hospital_protocols_in_general_mode(session_and_settings, sample_chat_patient):
    session, settings = session_and_settings
    doctor = sample_chat_patient["doctor"]

    payload = ChatRequest(
        question="What is the hospital STEMI emergency protocol?",
        patient_id=None,
        top_k=5,
    )

    response = await chat_stream(
        payload=payload,
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )
    assert response.status_code == 200

    body = b""
    async for chunk in response.body_iterator:
        body += chunk.encode("utf-8")

    events = _parse_sse_events(body)
    token_texts = [e.get("content", "") for e in events if e.get("type") == "token"]
    full_answer = "".join(token_texts)
    assert "STEMI" in full_answer or "infarction" in full_answer.lower() or "ecg" in full_answer.lower()


@pytest.mark.asyncio
async def test_chat_stream_disambiguation_multi_match(session_and_settings):
    session, settings = session_and_settings
    doctor = User(
        id=uuid.uuid4(),
        email="doctor_disam@example.test",
        full_name="Dr. Disam",
        department="Cardiology",
        role="doctor",
    )
    p1 = Patient(
        id=uuid.uuid4(),
        mrn="MRN-9001",
        full_name="Bùi Đức Hùng",
        dob=date(1978, 5, 20),
        department="Cardiology 4N",
        status="active",
    )
    p2 = Patient(
        id=uuid.uuid4(),
        mrn="MRN-9002",
        full_name="Bùi Đức Hùng",
        dob=date(1980, 1, 1),
        department="ICU",
        status="active",
    )
    session.add_all(
        [
            doctor,
            p1,
            p2,
            PatientPermission(user_id=doctor.id, patient_id=p1.id, scope="read"),
            PatientPermission(user_id=doctor.id, patient_id=p2.id, scope="read"),
        ]
    )
    await session.commit()

    payload = ChatRequest(question="bui duc hung di ung thuoc gi?", patient_id=None, top_k=5)
    response = await chat_stream(
        payload=payload,
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )
    assert response.status_code == 200
    events = []
    async for chunk in response.body_iterator:
        events.append(chunk)
    assert any("disambiguation_required" in c for c in events)
    assert any('"type": "done"' in c or '"type":"done"' in c for c in events)
