from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from hospital_ai.db.clinical_documents import (
    DocumentIndexGeneration,
    DocumentPageRevision,
    DocumentRevisionPage,
    DocumentRevisionSet,
)
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import AuditLog, Document, DocumentPage, User


@pytest.fixture
async def worker_fixture(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    if not doctor:
        doctor = User(id=uuid.uuid4(), email="doc@test.com", full_name="Doc", role="doctor", is_active=True)
        session.add(doctor)
        await session.commit()

    doc = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id,
        title="Worker Test Doc",
        document_type="progress_note",
        storage_uri="local://test/worker.pdf",
        mime_type="application/pdf",
        status="review_required",
    )
    session.add(doc)
    await session.flush()

    legacy_page = DocumentPage(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_number=1,
        ocr_text="legacy page must remain unchanged",
        ocr_confidence=0.5,
    )
    session.add(legacy_page)

    rev = DocumentPageRevision(
        document_id=doc.id,
        page_number=1,
        revision_number=1,
        revision_type="machine_ocr",
        raw_text_snapshot="Clinical content here.",
        corrected_text="Clinical content here.",
        confidence=0.99,
        status="approved",
        created_by_user_id=doctor.id,
        content_sha256="c" * 64,
        version=1,
    )
    session.add(rev)
    await session.flush()

    rev_set = DocumentRevisionSet(
        document_id=doc.id,
        revision_number=1,
        created_by_user_id=doctor.id,
        status="approved",
        submitted_at=datetime.now(UTC),
        approved_by_user_id=doctor.id,
        approved_at=datetime.now(UTC),
    )
    session.add(rev_set)
    await session.flush()

    rev_page = DocumentRevisionPage(
        revision_set_id=rev_set.id,
        page_number=1,
        page_revision_id=rev.id,
    )
    session.add(rev_page)

    gen = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=doc.id,
        revision_set_id=rev_set.id,
        state="building",
        revision_set_sha256="r" * 64,
    )
    session.add(gen)
    await session.flush()
    await session.commit()
    return session, settings, doc, gen


@pytest.mark.asyncio
async def test_chunk_stage_does_not_mutate_legacy_page(worker_fixture) -> None:
    session, settings, doc, gen = worker_fixture
    from hospital_ai.workers.generation_jobs import GenerationBuilder

    revision_set = await session.get(DocumentRevisionSet, gen.revision_set_id)
    page = await session.scalar(
        select(DocumentPage).where(DocumentPage.document_id == doc.id, DocumentPage.page_number == 1)
    )
    assert revision_set is not None
    assert page is not None

    await GenerationBuilder.from_settings(session, settings).stage_runner.run("chunks", gen, revision_set)
    await session.refresh(page)
    assert page.ocr_text == "legacy page must remain unchanged"
    await session.rollback()


@pytest.mark.asyncio
async def test_generation_builder_build_and_activate(worker_fixture) -> None:
    session, settings, doc, gen = worker_fixture
    from hospital_ai.workers.generation_jobs import GenerationBuilder

    builder = GenerationBuilder.from_settings(session, settings)
    result = await builder.build(gen.id)

    await session.refresh(doc)
    await session.refresh(gen)
    legacy_page = await session.scalar(
        select(DocumentPage).where(DocumentPage.document_id == doc.id, DocumentPage.page_number == 1)
    )
    assert gen.state == "active"
    assert doc.active_index_generation_id == gen.id
    assert result.active_generation_id == gen.id
    assert legacy_page is not None
    assert legacy_page.ocr_text == "Clinical content here."
    activation_audit = await session.scalar(
        select(AuditLog).where(
            AuditLog.action == "document_generation.activate",
            AuditLog.object_id == gen.id,
        )
    )
    assert activation_audit is not None
    assert activation_audit.outcome == "allowed"
