from __future__ import annotations

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


@pytest.mark.asyncio
async def test_run_cdss_analysis_propagates_provider_failures(session_and_settings):
    db_session, _ = session_and_settings
    patient = Patient(mrn="CDSS-ERR-001", full_name="Error Case", status="active")
    user = User(email="cdss-error@example.com", full_name="CDSS", role="doctor")
    db_session.add_all([patient, user])
    await db_session.flush()

    document = Document(
        patient_id=patient.id,
        uploaded_by=user.id,
        title="Failure Case",
        document_type="report",
        storage_uri="mock://failure",
        mime_type="text/plain",
        status="ready",
    )
    db_session.add(document)
    await db_session.flush()

    page = DocumentPage(document_id=document.id, page_number=1, ocr_text="Clinical content")
    db_session.add(page)
    await db_session.flush()
    db_session.add(
        DocumentChunk(
            document_id=document.id,
            page_id=page.id,
            patient_id=patient.id,
            chunk_index=0,
            content="Clinical content",
            token_count=2,
            embedding=[0.0] * 1024,
            meta={},
        )
    )
    await db_session.commit()

    mock_llm = AsyncMock()
    mock_llm.generate.side_effect = RuntimeError("provider unavailable")
    with patch("hospital_ai.workers.cdss.get_llm_manager") as mock_get_manager:
        mock_get_manager.return_value = MagicMock(get=MagicMock(return_value=mock_llm))
        with pytest.raises(RuntimeError, match="provider unavailable"):
            await run_cdss_analysis(db_session, document.id)


@pytest.mark.asyncio
async def test_cdss_re_run_is_idempotent_and_preserves_acknowledged_alerts(session_and_settings):
    import uuid
    from datetime import datetime, timezone
    from hospital_ai.db.clinical_documents import DocumentIndexGeneration
    from hospital_ai.db.clinical_graph import GraphEntity

    db_session, _ = session_and_settings
    patient = Patient(mrn="CDSS-IDEM-001", full_name="Idem Patient", status="active")
    user = User(email="cdss-idem@example.com", full_name="CDSS Idem", role="doctor")
    db_session.add_all([patient, user])
    await db_session.flush()

    document = Document(
        patient_id=patient.id,
        uploaded_by=user.id,
        title="Idem Report",
        document_type="report",
        storage_uri="mock://idem",
        mime_type="text/plain",
        status="ready",
    )
    db_session.add(document)
    await db_session.flush()

    gen_active = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_set_id=uuid.uuid4(),
        revision_set_sha256="a" * 64,
        state="active",
    )
    gen_superseded = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_set_id=uuid.uuid4(),
        revision_set_sha256="b" * 64,
        state="superseded",
    )
    document.active_index_generation_id = gen_active.id
    db_session.add_all([gen_active, gen_superseded])
    await db_session.flush()

    page = DocumentPage(document_id=document.id, page_number=1, ocr_text="Active chunk content.")
    db_session.add(page)
    await db_session.flush()

    active_chunk = DocumentChunk(
        document_id=document.id,
        page_id=page.id,
        patient_id=patient.id,
        generation_id=gen_active.id,
        chunk_index=0,
        content="ACTIVE_GEN_CHUNK_TEXT",
        token_count=4,
        embedding=[0.0] * 1024,
        meta={},
    )
    superseded_chunk = DocumentChunk(
        document_id=document.id,
        page_id=page.id,
        patient_id=patient.id,
        generation_id=gen_superseded.id,
        chunk_index=1,
        content="SUPERSEDED_GEN_CHUNK_TEXT",
        token_count=4,
        embedding=[0.0] * 1024,
        meta={},
    )
    deleted_chunk = DocumentChunk(
        document_id=document.id,
        page_id=page.id,
        patient_id=patient.id,
        generation_id=gen_active.id,
        chunk_index=2,
        content="DELETED_CHUNK_TEXT",
        token_count=4,
        embedding=[0.0] * 1024,
        meta={},
        deleted_at=datetime.now(timezone.utc),
    )
    inactive_entity = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient.id,
        normalized_label="discontinued_heparin_secret",
        entity_type="drug",
        lifecycle_status="discontinued",
    )
    ack_alert = ClinicalAlert(
        patient_id=patient.id,
        source_document_id=document.id,
        severity="medium",
        title="Acknowledged Historical Alert",
        description="Already reviewed by clinician",
        is_acknowledged=True,
    )
    stale_unack_alert = ClinicalAlert(
        patient_id=patient.id,
        source_document_id=document.id,
        severity="low",
        title="Stale Unacknowledged Alert",
        description="Should be replaced on re-run",
        is_acknowledged=False,
    )
    db_session.add_all(
        [
            active_chunk,
            superseded_chunk,
            deleted_chunk,
            inactive_entity,
            ack_alert,
            stale_unack_alert,
        ]
    )
    await db_session.commit()

    mock_llm = AsyncMock()
    mock_llm.generate.return_value = LLMResponse(
        text='{"alerts": [{"severity": "high", "title": "Fresh Alert", "description": "Active risk."}]}'
    )

    with patch("hospital_ai.workers.cdss.get_llm_manager") as mock_get_manager:
        mock_get_manager.return_value = MagicMock(get=MagicMock(return_value=mock_llm))
        await run_cdss_analysis(db_session, document.id)
        await run_cdss_analysis(db_session, document.id)

    sent_prompt = mock_llm.generate.call_args[0][0][1].content
    assert "ACTIVE_GEN_CHUNK_TEXT" in sent_prompt
    assert "SUPERSEDED_GEN_CHUNK_TEXT" not in sent_prompt
    assert "DELETED_CHUNK_TEXT" not in sent_prompt
    assert "discontinued_heparin_secret" not in sent_prompt

    result = await db_session.execute(
        select(ClinicalAlert).where(ClinicalAlert.source_document_id == document.id)
    )
    alerts = result.scalars().all()
    titles = sorted(a.title for a in alerts)
    assert titles == ["Acknowledged Historical Alert", "Fresh Alert"]

