import pytest
import uuid
from hospital_ai.services.retrieval import RetrievalService
from hospital_ai.services.general_knowledge import GeneralKnowledgeService
from hospital_ai.db.models import User


@pytest.mark.asyncio
async def test_general_knowledge_answers_expanded_protocols(session_and_settings):
    _, settings = session_and_settings
    service = GeneralKnowledgeService(settings)

    # Test STEMI protocol lookup
    res_stemi = await service.answer("What is the hospital STEMI emergency protocol?")
    assert "STEMI" in res_stemi.answer or "infarction" in res_stemi.answer.lower()
    assert len(res_stemi.citations) > 0

    # Test SBAR handoff protocol
    res_sbar = await service.answer("How to perform SBAR handoff between shifts?")
    assert "SBAR" in res_sbar.answer or "handoff" in res_sbar.answer.lower()
    assert len(res_sbar.citations) > 0

    # Test NEWS2 clinical scoring
    res_news = await service.answer("What are the NEWS2 escalation triggers?")
    assert "NEWS2" in res_news.answer or "escalation" in res_news.answer.lower()
    assert len(res_news.citations) > 0


@pytest.mark.asyncio
async def test_retrieval_service_hospital_wide_flag(session_and_settings):
    session, _ = session_and_settings
    service = RetrievalService(session)
    dummy_user_id = uuid.uuid4()
    dummy_embedding = [0.0] * 1024

    # When hospital_wide is False and patient_id is None, it should return []
    chunks = await service.search(
        user_id=dummy_user_id,
        patient_id=None,
        query_embedding=dummy_embedding,
        top_k=5,
        hospital_wide=False,
    )
    assert chunks == []

    # When hospital_wide is True, it allows search across public/authorized documents
    chunks_hw = await service.search(
        user_id=dummy_user_id,
        patient_id=None,
        query_embedding=dummy_embedding,
        top_k=5,
        hospital_wide=True,
    )
    assert isinstance(chunks_hw, list)
