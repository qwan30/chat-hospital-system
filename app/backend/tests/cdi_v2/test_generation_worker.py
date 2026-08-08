from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from hospital_ai.db.clinical_documents import (
    DocumentIndexGeneration,
    DocumentPageRevision,
    DocumentRevisionPage,
    DocumentRevisionSet,
)
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import Document, User


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

    rev = DocumentPageRevision(
        document_id=doc.id,
        page_number=1,
        revision_number=1,
        revision_type="machine_initial",
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
async def test_generation_builder_build_and_activate(worker_fixture) -> None:
    session, settings, doc, gen = worker_fixture
    from hospital_ai.workers.generation_jobs import GenerationBuilder

    builder = GenerationBuilder.from_settings(session, settings)
    result = await builder.build(gen.id)

    await session.refresh(doc)
    await session.refresh(gen)
    assert gen.state == "active"
    assert doc.active_index_generation_id == gen.id
    assert result.active_generation_id == gen.id
