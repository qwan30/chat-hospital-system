from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from hospital_ai.db.clinical_documents import (
    DocumentIndexGeneration,
    DocumentRevisionSet,
    GenerationStageResult,
)
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage, User
from hospital_ai.services.generations import GENERATION_STAGES
from hospital_ai.workers.generation_jobs import GenerationBuilder, StageOutput


@pytest.fixture
async def failure_fixture(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    if not doctor:
        doctor = User(
            id=uuid.uuid4(),
            email="generation-failure@test.com",
            full_name="Generation Failure",
            role="doctor",
            is_active=True,
        )
        session.add(doctor)
        await session.commit()

    document = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id,
        title="Generation Failure Test",
        document_type="progress_note",
        storage_uri="local://test/generation-failure.pdf",
        mime_type="application/pdf",
        status="ready",
    )
    session.add(document)
    await session.flush()

    old_revision_set = DocumentRevisionSet(
        document_id=document.id,
        revision_number=1,
        created_by_user_id=doctor.id,
        status="approved",
        submitted_at=datetime.now(UTC),
        approved_by_user_id=doctor.id,
        approved_at=datetime.now(UTC),
    )
    new_revision_set = DocumentRevisionSet(
        document_id=document.id,
        revision_number=2,
        created_by_user_id=doctor.id,
        status="build_authorized",
        submitted_at=datetime.now(UTC),
    )
    session.add_all([old_revision_set, new_revision_set])
    await session.flush()

    old_generation = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_set_id=old_revision_set.id,
        state="active",
        revision_set_sha256="old-revision" * 8,
        generation_sha256="old-generation" * 8,
        activated_at=datetime.now(UTC),
    )
    new_generation = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_set_id=new_revision_set.id,
        state="building",
        revision_set_sha256="new-revision" * 8,
    )
    session.add_all([old_generation, new_generation])
    document.active_index_generation_id = old_generation.id
    document.approved_revision_set_id = old_revision_set.id
    await session.commit()
    return session, settings, document, old_generation, new_generation


@pytest.mark.asyncio
@pytest.mark.parametrize("failed_stage", GENERATION_STAGES)
async def test_failed_stage_preserves_active_generation_and_records_failure(failure_fixture, failed_stage: str) -> None:
    session, settings, document, old_generation, new_generation = failure_fixture
    builder = GenerationBuilder.from_settings(session, settings)
    page = DocumentPage(
        id=uuid.uuid4(),
        document_id=document.id,
        page_number=1,
        ocr_text="legacy active text",
    )
    session.add(page)
    await session.commit()

    async def injected_stage(stage, generation, revision_set, custom_metadata=None):
        if stage == failed_stage:
            raise RuntimeError(f"injected failure at {stage}")
        if stage == "chunks":
            session.add(
                DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=document.id,
                    page_id=page.id,
                    patient_id=document.patient_id,
                    chunk_index=0,
                    content="staged-only content",
                    generation_id=new_generation.id,
                    revision_set_id=new_generation.revision_set_id,
                )
            )
            await session.flush()
        return StageOutput(sha256=hashlib.sha256(stage.encode("utf-8")).hexdigest(), row_count=1)

    builder.stage_runner.run = injected_stage

    with pytest.raises(RuntimeError, match=f"injected failure at {failed_stage}"):
        await builder.build(new_generation.id)

    await session.refresh(document)
    await session.refresh(old_generation)
    await session.refresh(new_generation)
    assert document.active_index_generation_id == old_generation.id
    assert document.approved_revision_set_id == old_generation.revision_set_id
    assert old_generation.state == "active"
    assert new_generation.state == "failed"
    await session.refresh(page)
    assert page.ocr_text == "legacy active text"

    failed_result = await session.scalar(
        select(GenerationStageResult).where(
            GenerationStageResult.generation_id == new_generation.id,
            GenerationStageResult.stage == failed_stage,
        )
    )
    assert failed_result is not None
    assert failed_result.status == "failed"
    assert failed_result.error_code == "STAGE_FAILED"

    staged_rows = list(
        await session.scalars(select(DocumentChunk).where(DocumentChunk.generation_id == new_generation.id))
    )
    if failed_stage in ("ocr_normalization", "facts", "chunks"):
        assert not staged_rows

    active_rows = list(
        await session.scalars(
            select(DocumentChunk)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(DocumentChunk.generation_id == Document.active_index_generation_id)
        )
    )
    assert all(row.generation_id == old_generation.id for row in active_rows)


@pytest.mark.asyncio
async def test_graph_stage_failure_is_not_degraded_silently(failure_fixture, monkeypatch: pytest.MonkeyPatch) -> None:
    session, settings, document, _, new_generation = failure_fixture
    page = DocumentPage(
        id=uuid.uuid4(),
        document_id=document.id,
        page_number=1,
        ocr_text="graph source",
    )
    session.add(page)
    await session.flush()
    session.add(
        DocumentChunk(
            id=uuid.uuid4(),
            document_id=document.id,
            page_id=page.id,
            patient_id=document.patient_id,
            chunk_index=0,
            content="graph source",
            generation_id=new_generation.id,
            revision_set_id=new_generation.revision_set_id,
        )
    )
    await session.commit()

    async def fail_graph(*args, **kwargs):
        raise RuntimeError("graph extractor unavailable")

    monkeypatch.setattr("hospital_ai.services.graph_rag.extract_entities_and_relations_nlp", fail_graph)
    runner = GenerationBuilder.from_settings(session, settings).stage_runner
    revision_set = await session.get(DocumentRevisionSet, new_generation.revision_set_id)
    assert revision_set is not None

    with pytest.raises(RuntimeError, match="graph extractor unavailable"):
        await runner.run("graph", new_generation, revision_set)
