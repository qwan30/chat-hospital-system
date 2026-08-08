from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from hospital_ai.core.errors import ConflictError
from hospital_ai.db.clinical_documents import (
    DocumentDraftHead,
    DocumentPageRevision,
    DocumentRevisionSet,
)
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import Document, User


@pytest.fixture
async def seeded_document(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    if not doctor:
        doctor = User(id=uuid.uuid4(), email="doc@test.com", full_name="Doc", role="doctor", is_active=True)
        session.add(doctor)
        await session.commit()

    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id,
        title="Test Doc",
        document_type="progress_note",
        storage_uri="local://test/doc.pdf",
        mime_type="application/pdf",
        status="ready",
    )
    session.add(doc)

    machine_id = uuid.uuid4()
    rev = DocumentPageRevision(
        id=machine_id,
        document_id=doc.id,
        page_number=1,
        revision_number=1,
        revision_type="machine_initial",
        raw_text_snapshot="initial text",
        corrected_text="initial text",
        confidence=0.95,
        status="machine_initial",
        created_by_user_id=doctor.id,
        content_sha256="a" * 64,
        version=1,
    )
    session.add(rev)

    head = DocumentDraftHead(
        document_id=doc.id,
        selected_pages={"1": str(machine_id)},
        lock_version=1,
        updated_by_user_id=doctor.id,
    )
    session.add(head)
    await session.commit()
    doc.machine_id = machine_id
    doc.doctor_id = doctor.id
    return doc


@pytest.fixture
async def submitted_set(session_and_settings, seeded_document):
    session, settings = session_and_settings
    set_id = uuid.uuid4()
    rev_set = DocumentRevisionSet(
        id=set_id,
        document_id=seeded_document.id,
        revision_number=1,
        status="submitted",
        created_by_user_id=seeded_document.doctor_id,
        submitted_at=datetime.now(UTC),
    )
    session.add(rev_set)
    await session.commit()
    return rev_set


@pytest.mark.asyncio
async def test_stale_draft_save_returns_conflict_without_revision(session_and_settings, seeded_document) -> None:
    session, _ = session_and_settings
    from hospital_ai.services.revisions import RevisionService, SavePageCommand

    service = RevisionService(session)
    machine_id = seeded_document.machine_id
    doctor_id = seeded_document.doctor_id
    records_id = uuid.uuid4()

    first = await service.save_page(
        seeded_document.id,
        1,
        SavePageCommand(
            text="first", parent_revision_id=machine_id, lock_version=1, actor_id=doctor_id, edit_reason="fix"
        ),
    )
    with pytest.raises(ConflictError):
        await service.save_page(
            seeded_document.id,
            1,
            SavePageCommand(
                text="stale", parent_revision_id=machine_id, lock_version=1, actor_id=records_id, edit_reason="fix"
            ),
        )
    rows = list(
        await session.scalars(
            select(DocumentPageRevision).where(
                DocumentPageRevision.document_id == seeded_document.id,
                DocumentPageRevision.revision_type == "human_edit",
            )
        )
    )
    assert [row.id for row in rows] == [first.page_revision_id]


@pytest.mark.asyncio
async def test_production_editor_cannot_approve_own_submission(session_and_settings, submitted_set) -> None:
    session, _ = session_and_settings
    from hospital_ai.services.revisions import ApproveRevisionCommand, RevisionService

    with pytest.raises(ConflictError):
        await RevisionService(session).approve(
            submitted_set.id,
            ApproveRevisionCommand(actor_id=submitted_set.created_by_user_id, demo_mode=False),
        )


@pytest.mark.asyncio
async def test_submit_reject_and_restore(session_and_settings, seeded_document) -> None:
    session, _ = session_and_settings
    from hospital_ai.services.revisions import RejectCommand, RestoreCommand, RevisionService, SubmitCommand

    service = RevisionService(session)

    sub = await service.submit(seeded_document.id, SubmitCommand(actor_id=seeded_document.doctor_id))
    assert sub.status == "submitted"

    rejected = await service.reject(
        sub.revision_set_id, RejectCommand(actor_id=seeded_document.doctor_id, reason="incorrect")
    )
    assert rejected.status == "rejected"

    restored = await service.restore(
        seeded_document.id,
        1,
        RestoreCommand(
            revision_id=seeded_document.machine_id, actor_id=seeded_document.doctor_id, lock_version=1, reason="undo"
        ),
    )
    assert restored.lock_version == 2
