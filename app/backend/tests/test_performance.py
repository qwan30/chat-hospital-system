import time

import pytest
from starlette.requests import Request

from hospital_ai.api.routes.chat import chat
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import User
from hospital_ai.schemas.chat import ChatRequest
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
async def test_summary_latency_under_30s(session_and_settings):
    """
    Test that the RAG summary generation or compilation
    meets the < 30 seconds latency requirement as defined in the test plan.
    """
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Patient History",
        content=(
            "Patient has a long history of hypertension and diabetes. "
            "Current medications include Lisinopril and Metformin."
        ),
    )

    payload = ChatRequest(
        patient_id=PATIENT_ALICE_ID, question="Summarize the patient's medical history.", pipeline="patient_summary"
    )

    start_time = time.time()

    response = await chat(
        payload=payload,
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    end_time = time.time()
    latency = end_time - start_time

    assert response is not None
    assert latency < 30.0, f"Summary latency was {latency:.2f}s, exceeding the 30s threshold."
