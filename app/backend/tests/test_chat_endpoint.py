"""Tests for the POST /chat endpoint (non-streaming).

Exercises the chat route handler through its FastAPI dependencies,
confirming that Pydantic validation, authorization, pipeline dispatch,
and response serialisation work end to end.
"""
from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError
from starlette.requests import Request

from hospital_ai.api.routes.chat import chat
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import User
from hospital_ai.schemas.chat import ChatRequest, ChatResponse
from hospital_ai.schemas.documents import EvidenceRead
from tests.conftest import create_indexed_document


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/chat",
            "headers": [],
            "client": ("testclient", 50000),
        }
    )


@pytest.mark.asyncio
async def test_chat_valid_request_returns_chat_response(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Progress Note",
        content=("Patient shows signs of recovery. Status: improving. Vital signs: stable."),
    )

    payload = ChatRequest(
        patient_id=PATIENT_ALICE_ID,
        question="What is the patient's status?",
        top_k=5,
    )

    response = await chat(
        payload=payload,
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    assert isinstance(response, ChatResponse)
    assert isinstance(response.query_id, uuid.UUID)
    assert isinstance(response.answer, str)
    assert len(response.answer) > 0
    assert isinstance(response.citations, list)
    assert response.confidence in {"low", "medium", "high"}
    assert isinstance(response.disclaimer, str)
    assert response.pipeline is not None


@pytest.mark.asyncio
async def test_chat_missing_question_returns_422(session_and_settings):
    with pytest.raises(ValidationError) as exc_info:
        ChatRequest(patient_id=PATIENT_ALICE_ID)
    assert "question" in str(exc_info.value).lower()

    with pytest.raises(ValidationError) as exc_info:
        ChatRequest(patient_id=PATIENT_ALICE_ID, question="")
    assert "question" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_chat_invalid_patient_id_returns_error(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    nonexistent_id = uuid.UUID("99999999-0000-0000-0000-000000000000")
    from hospital_ai.db.models import Patient

    session.add(Patient(id=nonexistent_id, full_name="Test", mrn="MRN"))
    await session.commit()

    payload = ChatRequest(
        patient_id=nonexistent_id,
        question="What is the patient's condition?",
    )

    with pytest.raises(PermissionDeniedError) as exc_info:
        await chat(
            payload=payload,
            request=_request(),
            session=session,
            current_user=doctor,
            settings=settings,
        )

    assert "not authorized" in str(exc_info.value).lower()
    assert exc_info.value.code == "FORBIDDEN"


@pytest.mark.asyncio
async def test_chat_pipeline_dispatch(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Lab Report",
        content=("Hemoglobin: 13.5. White blood cells: 6800. Status: stable."),
    )

    for pipeline in ("auto", "simple", "decompose", "patient_summary"):
        payload = ChatRequest(
            patient_id=PATIENT_ALICE_ID,
            question=("What are the lab results and what is the patient's overall status?"),
            pipeline=pipeline,
        )

        response = await chat(
            payload=payload,
            request=_request(),
            session=session,
            current_user=doctor,
            settings=settings,
        )

        assert isinstance(response, ChatResponse), f"pipeline={pipeline!r} did not produce a ChatResponse"
        assert len(response.answer) > 0
        assert response.pipeline is not None


@pytest.mark.asyncio
async def test_chat_response_matches_schema(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Admission Note",
        content=("Patient admitted for observation. Status: critical. Vital signs: unstable."),
    )

    payload = ChatRequest(
        patient_id=PATIENT_ALICE_ID,
        question="What is the patient's admission status?",
    )

    response = await chat(
        payload=payload,
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    assert isinstance(response.query_id, uuid.UUID)
    assert isinstance(response.answer, str) and len(response.answer) > 0
    assert isinstance(response.citations, list)
    assert isinstance(response.confidence, str)
    assert isinstance(response.disclaimer, str)

    for citation in response.citations:
        assert isinstance(citation, EvidenceRead)
        assert isinstance(citation.evidence_id, str) and citation.evidence_id
        assert isinstance(citation.document_id, uuid.UUID)
        assert isinstance(citation.document_title, str)
        assert isinstance(citation.chunk_id, uuid.UUID)

    assert response.pipeline is not None
    assert response.thread_id is None
    assert isinstance(response.warnings, list)


@pytest.mark.asyncio
async def test_chat_global_query_without_patient_context(session_and_settings):
    from hospital_ai.services.chat import SAFE_NO_EVIDENCE_ANSWER

    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    await create_indexed_document(
        session,
        patient_id=None,
        uploaded_by=DOCTOR_ID,
        title="Apixaban Guideline",
        content=(
            "DOAC renal-dose adjustment rules for apixaban: reduce dose to 2.5 mg BID if serum creatinine >= 1.5 mg/dL."
        ),
    )

    payload = ChatRequest(
        patient_id=None,
        question="What are the DOAC renal-dose adjustment rules for apixaban?",
        top_k=5,
    )

    response = await chat(
        payload=payload,
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    assert isinstance(response, ChatResponse)
    assert response.answer == SAFE_NO_EVIDENCE_ANSWER
    assert response.citations == []
