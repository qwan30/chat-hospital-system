from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from hospital_ai.db.models import ClinicalAlert, Document, DocumentChunk, DocumentPage, Patient, User
from hospital_ai.services.llm.base import LLMResponse
from hospital_ai.workers.cdss import run_cdss_analysis


@pytest.mark.asyncio
async def test_run_cdss_analysis(session_and_settings):
    db_session, _ = session_and_settings
    # Create patient
    patient = Patient(mrn="CDSS-001", full_name="John Doe", status="active")
    db_session.add(patient)
    await db_session.flush()

    # Create user for uploaded_by
    user = User(email="cdss@example.com", full_name="CDSS", role="doctor")
    db_session.add(user)
    await db_session.flush()

    # Create document
    document = Document(
        patient_id=patient.id,
        uploaded_by=user.id,
        title="Test Report",
        document_type="report",
        storage_uri="mock://test",
        mime_type="text/plain",
        status="ready",
    )
    db_session.add(document)
    await db_session.flush()

    # Create chunk
    page = DocumentPage(document_id=document.id, page_number=1, ocr_text="Patient takes Aspirin.")
    db_session.add(page)
    await db_session.flush()

    chunk = DocumentChunk(
        document_id=document.id,
        page_id=page.id,
        patient_id=patient.id,
        chunk_index=0,
        content="Patient takes Aspirin.",
        token_count=4,
        embedding=[0.0] * 1024,
        meta={},
    )
    db_session.add(chunk)
    await db_session.commit()

    # Mock LLM
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = LLMResponse(
        text='{"alerts": [{"severity": "high", "title": "Bleeding Risk", "description": "Aspirin risk."}]}'
    )

    with patch("hospital_ai.workers.cdss.get_llm_manager") as mock_get_manager:
        mock_manager = MagicMock()
        mock_manager.get.return_value = mock_llm
        mock_get_manager.return_value = mock_manager

        await run_cdss_analysis(db_session, document.id)

    # Check alert was created
    result = await db_session.execute(select(ClinicalAlert).where(ClinicalAlert.source_document_id == document.id))
    alerts = result.scalars().all()
    assert len(alerts) == 1
    assert alerts[0].severity == "high"
    assert alerts[0].title == "Bleeding Risk"
