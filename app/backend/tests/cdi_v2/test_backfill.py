import uuid

import pytest

from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage, User
from hospital_ai.migrations.cdi_v2_backfill import BackfillPolicy, CdiV2Backfill


@pytest.fixture
async def session(session_and_settings):
    session, _ = session_and_settings
    return session


@pytest.fixture
async def setup_doctor(session):
    doctor = await session.get(User, DOCTOR_ID)
    if not doctor:
        doctor = User(id=uuid.uuid4(), email="doctor_bf@test.com", full_name="Doc BF", role="doctor", is_active=True)
        session.add(doctor)
        await session.commit()
    return doctor


@pytest.fixture
async def legacy_real_document(session, setup_doctor):
    doctor = setup_doctor
    doc = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id,
        title="Legacy Real Doc",
        document_type="progress_note",
        storage_uri="local://test/real_doc.pdf",
        mime_type="application/pdf",
        status="ready",
        is_synthetic=False,
        indexed_source_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    session.add(doc)
    await session.flush()

    page = DocumentPage(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_number=1,
        ocr_text="Real clinical report text.",
        ocr_confidence=0.98,
    )
    session.add(page)
    await session.flush()

    chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_id=page.id,
        patient_id=PATIENT_ALICE_ID,
        chunk_index=0,
        content="Real clinical report text.",
        token_count=4,
    )
    session.add(chunk)
    await session.flush()
    await session.commit()
    return doc


@pytest.fixture
async def legacy_document(session, setup_doctor):
    doctor = setup_doctor
    doc = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id,
        title="Legacy Synthetic Doc",
        document_type="progress_note",
        storage_uri="local://test/synth_doc.pdf",
        mime_type="application/pdf",
        status="ready",
        is_synthetic=True,
        indexed_source_sha256="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
    )
    session.add(doc)
    await session.flush()

    page = DocumentPage(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_number=1,
        ocr_text="Synthetic demo patient notes.",
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
        content="Synthetic demo patient notes.",
        token_count=4,
    )
    session.add(chunk)
    await session.flush()
    await session.commit()
    return doc


@pytest.fixture
async def wrong_patient_chunk(session, legacy_document):
    from sqlalchemy import select

    res = await session.execute(select(DocumentPage).where(DocumentPage.document_id == legacy_document.id))
    pages = list(res.scalars().all())
    chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=legacy_document.id,
        page_id=pages[0].id if pages else uuid.uuid4(),
        patient_id=PATIENT_BOB_ID,
        chunk_index=99,
        content="Wrong patient content.",
        token_count=3,
    )
    session.add(chunk)
    await session.flush()
    await session.commit()
    return chunk


@pytest.mark.asyncio
async def test_backfill_is_resumable_and_does_not_autoapprove_real_data(session, legacy_real_document) -> None:
    runner = CdiV2Backfill(session, policy=BackfillPolicy(autoapprove_synthetic=True))
    first = await runner.run_document(legacy_real_document.id)
    second = await runner.run_document(legacy_real_document.id)
    assert first.machine_revision_ids == second.machine_revision_ids
    document = await session.get(Document, legacy_real_document.id)
    assert document.approved_revision_set_id is None
    assert document.active_index_generation_id is None


@pytest.mark.asyncio
async def test_legacy_generation_rejects_wrong_patient_chunk(session, legacy_document, wrong_patient_chunk) -> None:
    result = await CdiV2Backfill(session, BackfillPolicy()).verify_legacy_lineage(legacy_document.id)
    assert result.passed is False
    assert "wrong_patient_chunk" in result.failure_codes


@pytest.mark.asyncio
async def test_backfill_autoapproves_synthetic_document_and_creates_legacy_generation(session, legacy_document) -> None:
    runner = CdiV2Backfill(session, policy=BackfillPolicy(autoapprove_synthetic=True))
    res = await runner.run_document(legacy_document.id)
    assert res.generation_id is not None
    document = await session.get(Document, legacy_document.id)
    assert document.approved_revision_set_id == res.submitted_set_id
    assert document.active_index_generation_id == res.generation_id
