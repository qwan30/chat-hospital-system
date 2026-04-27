import pytest
from sqlalchemy import select

from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID
from hospital_ai.db.models import AiQuery, User
from hospital_ai.services.chat import ChatService, citations_are_valid
from tests.conftest import create_indexed_document


def test_citation_validation_rejects_unretrieved_ids():
    assert citations_are_valid("Use insulin [E1].", {"E1", "E2"})
    assert not citations_are_valid("Use insulin [E3].", {"E1", "E2"})
    assert not citations_are_valid("Use insulin.", {"E1"})


@pytest.mark.asyncio
async def test_chat_refuses_without_evidence(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    response = await ChatService(session, settings).answer(
        user=doctor,
        patient_id=PATIENT_ALICE_ID,
        question="What is the latest diagnosis?",
        top_k=5,
        trace_id="trace-no-evidence",
        ip_address="127.0.0.1",
    )

    assert response.citations == []
    assert response.confidence == "low"
    result = await session.execute(select(AiQuery).where(AiQuery.id == response.query_id))
    assert result.scalar_one().status == "no_evidence"


@pytest.mark.asyncio
async def test_cited_chat_uses_only_retrieved_evidence(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice allergy note",
        content="Alice has a documented allergy to penicillin.",
    )

    response = await ChatService(session, settings).answer(
        user=doctor,
        patient_id=PATIENT_ALICE_ID,
        question="What allergy is documented?",
        top_k=5,
        trace_id="trace-cited",
        ip_address="127.0.0.1",
    )

    assert "[E1]" in response.answer
    assert [citation.evidence_id for citation in response.citations] == ["E1"]


@pytest.mark.asyncio
async def test_chat_denied_before_retrieval(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    with pytest.raises(PermissionDeniedError):
        await ChatService(session, settings).answer(
            user=doctor,
            patient_id=PATIENT_BOB_ID,
            question="What is in Bob's chart?",
            top_k=5,
            trace_id="trace-chat-denied",
            ip_address="127.0.0.1",
        )
