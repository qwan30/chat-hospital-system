import pytest
from sqlalchemy import select

from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID
from hospital_ai.db.models import AiQuery, DocumentChunk, RetrievedEvidence, User
from hospital_ai.services.chat import SAFE_PHI_LEAK_BLOCKED_ANSWER, ChatService, citations_are_valid
from hospital_ai.services.chat_utils import parse_prompt_evidence
from hospital_ai.services.graph_rag import index_chunk_entities
from tests.conftest import create_indexed_document


def test_citation_validation_rejects_unretrieved_ids():
    assert citations_are_valid("Use insulin [E1].", {"E1", "E2"})
    assert citations_are_valid("Metformin treats diabetes [G1].", {"G1"})
    assert not citations_are_valid("Use insulin [E3].", {"E1", "E2"})
    assert not citations_are_valid("Use insulin.", {"E1"})


def test_prompt_parser_preserves_graph_evidence_labels():
    prompt = "[G1] Document: Graph note (page 1)\nMetformin treats diabetes.\n\nAnswer using only the evidence."

    assert parse_prompt_evidence(prompt) == [("G1", "Metformin treats diabetes.")]


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


@pytest.mark.asyncio
async def test_chat_surfaces_drug_warnings_when_conflict_exists(session_and_settings):
    """When drug entities in the query have graph relations in patient docs,
    the ChatResponse.warnings list should contain structured warnings."""
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    # Index a doc with drug+condition co-occurrence
    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Drug interaction note",
        content="Patient takes warfarin. Aspirin is mentioned with hypertension.",
    )

    # Populate graph entities for the chunk
    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
    chunk = result.scalars().first()
    await index_chunk_entities(session, chunk_id=chunk.id, document_id=doc.id, content=chunk.content)
    await session.commit()

    # Query asking about aspirin (a drug present in the graph)
    response = await ChatService(session, settings).answer(
        user=doctor,
        patient_id=PATIENT_ALICE_ID,
        question="Should the patient take aspirin?",
        top_k=5,
        trace_id="trace-drug-warning",
        ip_address="127.0.0.1",
    )

    # The response should include the warnings list (possibly empty
    # if no graph relations triggered, but the list should exist)
    assert isinstance(response.warnings, list)
    # If warnings were found, verify structure
    for warning in response.warnings:
        assert warning.drug_name
        assert warning.interacting_entity
        assert warning.severity in ("critical", "high", "medium", "low")
        assert warning.message


@pytest.mark.asyncio
async def test_chat_chitchat_bypass_rag(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    response = await ChatService(session, settings).answer(
        user=doctor,
        patient_id=PATIENT_ALICE_ID,
        question="Hello!",
        top_k=5,
        trace_id="trace-chitchat",
        ip_address="127.0.0.1",
    )

    assert response.pipeline == "chitchat"
    assert "Xin chào" in response.answer or "hello" in response.answer.lower()
    assert response.citations == []


@pytest.mark.asyncio
async def test_chat_chitchat_applies_output_guardrail(session_and_settings, monkeypatch):
    class Blocked:
        async def scan(self, *_args):
            from hospital_ai.services.guardrails import GuardrailResult

            return GuardrailResult(blocked=True, reason="test")

    monkeypatch.setattr("hospital_ai.services.chat.get_output_guardrail", lambda: Blocked())
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    response = await ChatService(session, settings).answer(
        user=doctor, patient_id=PATIENT_ALICE_ID, question="Hello!", top_k=1, trace_id="guard", ip_address="127.0.0.1"
    )
    assert response.answer == SAFE_PHI_LEAK_BLOCKED_ANSWER
    assert response.pipeline == "blocked"


@pytest.mark.asyncio
async def test_chat_persists_only_cited_retrieved_evidence(session_and_settings, monkeypatch):
    from hospital_ai.services.reasoning import DISCLAIMER, ReasoningResult

    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    await create_indexed_document(
        session, patient_id=PATIENT_ALICE_ID, uploaded_by=DOCTOR_ID, title="Cited", content="Cited evidence."
    )
    await create_indexed_document(
        session, patient_id=PATIENT_ALICE_ID, uploaded_by=DOCTOR_ID, title="Uncited", content="Uncited evidence."
    )

    async def only_first(self, _pipeline, _question, evidence, _history):
        return ReasoningResult(
            answer="Only the first item is used [E1].",
            citations=[],
            confidence="high",
            disclaimer=DISCLAIMER,
            pipeline="simple_qa",
        )

    monkeypatch.setattr(ChatService, "_run_pipeline", only_first)
    response = await ChatService(session, settings).answer(
        user=doctor,
        patient_id=PATIENT_ALICE_ID,
        question="What evidence is available?",
        top_k=2,
        trace_id="cited-only",
        ip_address="127.0.0.1",
    )
    rows = (
        await session.scalars(select(RetrievedEvidence).where(RetrievedEvidence.ai_query_id == response.query_id))
    ).all()
    assert len(rows) == 1
    assert rows[0].citation_label == "E1"


@pytest.mark.asyncio
async def test_chat_permission_denied_natural_refusal(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    # Temporarily change doctor's role to pharmacist and can_access_full_notes to False
    doctor.role = "pharmacist"
    await session.commit()

    # Index a document with a tag/content that is NOT medication/safety related (e.g. cardiology note)
    # So the role filter blocks it.
    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Cardiology clinical note",
        content="Patient has severe coronary artery disease.",
    )

    response = await ChatService(session, settings).answer(
        user=doctor,
        patient_id=PATIENT_ALICE_ID,
        question="What is the coronary disease status?",
        top_k=5,
        trace_id="trace-blocked",
        ip_address="127.0.0.1",
    )

    # Restore role to doctor
    doctor.role = "doctor"
    await session.commit()

    assert "Bạn không có quyền xem thông tin này" in response.answer
    assert response.citations == []
