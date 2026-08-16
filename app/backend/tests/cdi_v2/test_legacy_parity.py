from __future__ import annotations

import uuid

import pytest

from hospital_ai.core.config import get_settings
from hospital_ai.db.clinical_graph import LegacyGraphEntity, LegacyGraphRelation
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage, User
from hospital_ai.migrations.cdi_v2_backfill import BackfillPolicy, CdiV2Backfill


@pytest.fixture
async def session(session_and_settings):
    session, _ = session_and_settings
    return session


def test_cdi_v2_feature_flags_default_false():
    settings = get_settings()
    assert getattr(settings, "cdi_v2_dual_read", True) is False
    assert getattr(settings, "cdi_v2_active_generation_reads", True) is False
    assert getattr(settings, "cdi_v2_authoring_enabled", True) is False


@pytest.mark.asyncio
async def test_parity_verification_succeeds_on_clean_synthetic(session) -> None:
    doctor = await session.get(User, DOCTOR_ID)
    doc = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id if doctor else uuid.uuid4(),
        title="Parity Clean Synth",
        document_type="progress_note",
        storage_uri="local://test/parity_clean.pdf",
        mime_type="application/pdf",
        status="ready",
        is_synthetic=True,
        indexed_source_sha256="0011223344556677889900112233445566778899001122334455667788990011",
    )
    session.add(doc)
    await session.flush()

    page = DocumentPage(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_number=1,
        ocr_text="Clean parity text",
        ocr_confidence=1.0,
    )
    session.add(page)
    await session.flush()

    chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_id=page.id,
        patient_id=PATIENT_ALICE_ID,
        chunk_index=0,
        content="Clean parity text",
        token_count=3,
        text_start_offset=0,
        text_end_offset=17,
    )
    session.add(chunk)
    await session.flush()

    entity1 = LegacyGraphEntity(
        id=uuid.uuid4(),
        source_document_id=doc.id,
        source_chunk_id=chunk.id,
        name="Hypertension",
        entity_type="Condition",
        confidence=1.0,
    )
    session.add(entity1)

    entity2 = LegacyGraphEntity(
        id=uuid.uuid4(),
        source_document_id=doc.id,
        source_chunk_id=chunk.id,
        name="Lisinopril",
        entity_type="Medication",
        confidence=1.0,
    )
    session.add(entity2)

    relation = LegacyGraphRelation(
        id=uuid.uuid4(),
        source_entity_id=entity1.id,
        target_entity_id=entity2.id,
        relation_type="Treated_By",
        weight=1.0,
        source_chunk_id=chunk.id,
    )
    session.add(relation)

    await session.flush()
    await session.commit()

    runner = CdiV2Backfill(session, policy=BackfillPolicy(autoapprove_synthetic=True))
    await runner.run_document(doc.id)

    parity_report = await runner.compute_parity_report([doc.id])
    assert parity_report["wrong_patient_count"] == 0
    assert parity_report["superseded_generation_count"] == 0
    assert parity_report["status"] == "passed"
    assert len(parity_report["documents"]) == 1


@pytest.mark.asyncio
async def test_parity_fails_on_wrong_patient_and_flags_remain_off(session) -> None:
    doctor = await session.get(User, DOCTOR_ID)
    doc = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id if doctor else uuid.uuid4(),
        title="Parity Corrupt Synth",
        document_type="progress_note",
        storage_uri="local://test/parity_corrupt.pdf",
        mime_type="application/pdf",
        status="ready",
        is_synthetic=True,
        indexed_source_sha256="ffeebbddccaa99887766554433221100ffeebbddccaa99887766554433221100",
    )
    session.add(doc)
    await session.flush()

    page = DocumentPage(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_number=1,
        ocr_text="Corrupt text",
        ocr_confidence=1.0,
    )
    session.add(page)
    await session.flush()

    chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_id=page.id,
        patient_id=PATIENT_BOB_ID,
        chunk_index=0,
        content="Corrupt text",
        token_count=2,
    )
    session.add(chunk)
    await session.flush()
    await session.commit()

    runner = CdiV2Backfill(session, policy=BackfillPolicy(autoapprove_synthetic=True))
    parity_report = await runner.compute_parity_report([doc.id])
    assert parity_report["wrong_patient_count"] > 0
    assert parity_report["status"] == "failed"

    settings = get_settings()
    assert getattr(settings, "cdi_v2_dual_read", True) is False
    assert getattr(settings, "cdi_v2_active_generation_reads", True) is False
    assert getattr(settings, "cdi_v2_authoring_enabled", True) is False
