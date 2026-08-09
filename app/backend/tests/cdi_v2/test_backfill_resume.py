from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select

from hospital_ai.db.clinical_documents import (
    DocumentDraftHead,
    DocumentIndexGeneration,
    DocumentPageRevision,
    DocumentRevisionSet,
)
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import AuditLog, Document, DocumentChunk, DocumentPage, User
from hospital_ai.migrations.cdi_v2_backfill import BackfillPolicy, CdiV2Backfill


@pytest.fixture
async def resumable_document(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    if not doctor:
        doctor = User(
            id=uuid.uuid4(),
            email="backfill-resume@test.com",
            full_name="Backfill Resume",
            role="doctor",
            is_active=True,
        )
        session.add(doctor)
        await session.commit()

    document = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id,
        title="Resumable Synthetic Backfill",
        document_type="progress_note",
        storage_uri="local://test/resumable-backfill.pdf",
        mime_type="application/pdf",
        status="ready",
        is_synthetic=True,
        indexed_source_sha256="a" * 64,
    )
    session.add(document)
    await session.flush()
    page = DocumentPage(
        id=uuid.uuid4(),
        document_id=document.id,
        page_number=1,
        ocr_text="Resumable synthetic text",
        ocr_confidence=1.0,
    )
    session.add(page)
    await session.flush()
    session.add(
        DocumentChunk(
            id=uuid.uuid4(),
            document_id=document.id,
            page_id=page.id,
            patient_id=PATIENT_ALICE_ID,
            chunk_index=0,
            content=page.ocr_text,
            token_count=3,
        )
    )
    await session.commit()
    return session, document


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "interrupted_phase",
    ("machine_revisions", "draft_heads", "submitted_sets", "legacy_generations", "complete"),
)
async def test_backfill_resumes_from_durable_checkpoint_without_duplicates(
    resumable_document, interrupted_phase: str
) -> None:
    session, document = resumable_document
    document_id = document.id
    runner = CdiV2Backfill(session, policy=BackfillPolicy(autoapprove_synthetic=True))
    original_checkpoint = runner._record_checkpoint

    async def interrupt_after_checkpoint(document_id, phase):
        await original_checkpoint(document_id, phase)
        if phase == interrupted_phase:
            await session.commit()
            raise RuntimeError(f"interrupted at {phase}")

    runner._record_checkpoint = interrupt_after_checkpoint
    with pytest.raises(RuntimeError, match=interrupted_phase):
        await runner.run_document(document_id)
    await session.rollback()

    runner._record_checkpoint = original_checkpoint
    result = await runner.run_document(document_id)
    assert result.generation_id is not None

    assert (
        await session.scalar(
            select(func.count())
            .select_from(DocumentPageRevision)
            .where(DocumentPageRevision.document_id == document_id)
        )
        == 1
    )
    assert (
        await session.scalar(
            select(func.count()).select_from(DocumentDraftHead).where(DocumentDraftHead.document_id == document_id)
        )
        == 1
    )
    assert (
        await session.scalar(
            select(func.count()).select_from(DocumentRevisionSet).where(DocumentRevisionSet.document_id == document_id)
        )
        == 1
    )
    assert (
        await session.scalar(
            select(func.count())
            .select_from(DocumentIndexGeneration)
            .where(DocumentIndexGeneration.document_id == document_id)
        )
        == 1
    )

    checkpoints = list(
        (
            await session.scalars(
                select(AuditLog).where(
                    AuditLog.action == "cdi_v2_backfill.checkpoint",
                    AuditLog.object_id == document_id,
                )
            )
        ).all()
    )
    assert {row.meta["phase"] for row in checkpoints} == {
        "machine_revisions",
        "draft_heads",
        "submitted_sets",
        "legacy_generations",
        "complete",
    }
    assert len(checkpoints) == 5


@pytest.mark.asyncio
async def test_backfill_dry_run_rolls_back_all_database_writes(resumable_document) -> None:
    session, document = resumable_document
    document_id = document.id
    runner = CdiV2Backfill(
        session,
        policy=BackfillPolicy(autoapprove_synthetic=True),
        dry_run=True,
    )

    result = await runner.run_document(document_id)
    assert result.generation_id is not None
    assert (
        await session.scalar(
            select(func.count())
            .select_from(DocumentPageRevision)
            .where(DocumentPageRevision.document_id == document_id)
        )
        == 0
    )
    assert (
        await session.scalar(
            select(func.count()).select_from(DocumentDraftHead).where(DocumentDraftHead.document_id == document_id)
        )
        == 0
    )
    assert (
        await session.scalar(
            select(func.count()).select_from(DocumentRevisionSet).where(DocumentRevisionSet.document_id == document_id)
        )
        == 0
    )
    assert (
        await session.scalar(
            select(func.count())
            .select_from(DocumentIndexGeneration)
            .where(DocumentIndexGeneration.document_id == document_id)
        )
        == 0
    )
    assert (
        await session.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(
                AuditLog.action == "cdi_v2_backfill.checkpoint",
                AuditLog.object_id == document_id,
            )
        )
        == 0
    )
