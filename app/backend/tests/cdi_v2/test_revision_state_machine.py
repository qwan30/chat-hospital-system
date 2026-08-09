from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import ConflictError
from hospital_ai.db.clinical_documents import (
    PAGE_REVISION_STATES,
    REVISION_SET_STATES,
    DocumentDraftHead,
    DocumentPageRevision,
    DocumentRevisionSet,
)
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, RECORDS_ID
from hospital_ai.db.models import Document, User


@pytest_asyncio.fixture
async def revision_fixture(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    assert doctor is not None

    document = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id,
        title="State machine test document",
        document_type="progress_note",
        storage_uri="local://test/state-machine.pdf",
        mime_type="application/pdf",
        status="ready",
        page_count=1,
    )
    session.add(document)
    await session.flush()

    page_revision = DocumentPageRevision(
        id=uuid.uuid4(),
        document_id=document.id,
        page_number=1,
        revision_number=1,
        revision_type="machine_ocr",
        raw_text_snapshot="initial text",
        corrected_text="initial text",
        confidence=0.95,
        status="machine_draft",
        created_by_user_id=doctor.id,
        content_sha256="a" * 64,
        version=1,
    )
    session.add(page_revision)
    session.add(
        DocumentDraftHead(
            document_id=document.id,
            selected_pages={"1": str(page_revision.id)},
            lock_version=1,
            updated_by_user_id=doctor.id,
        )
    )
    await session.commit()
    return session, document, doctor, page_revision


@pytest.mark.asyncio
async def test_state_machine_uses_only_documented_states(revision_fixture) -> None:
    assert "machine_initial" not in PAGE_REVISION_STATES
    assert "restored" not in PAGE_REVISION_STATES
    assert "build_authorized" in REVISION_SET_STATES


@pytest.mark.asyncio
async def test_reject_is_only_legal_for_submitted_revision_set(revision_fixture) -> None:
    session, document, doctor, _ = revision_fixture
    from hospital_ai.services.revisions import RejectCommand, RevisionService, SubmitCommand

    service = RevisionService(session)
    submitted = await service.submit(document.id, SubmitCommand(actor_id=doctor.id))
    await service.reject(submitted.revision_set_id, RejectCommand(actor_id=doctor.id, reason="incorrect"))

    with pytest.raises(ConflictError, match="submitted"):
        await service.reject(submitted.revision_set_id, RejectCommand(actor_id=doctor.id, reason="again"))


@pytest.mark.asyncio
async def test_request_demo_flag_cannot_enable_self_approval(revision_fixture) -> None:
    session, document, doctor, _ = revision_fixture
    from hospital_ai.services.revisions import ApproveRevisionCommand, RevisionService, SubmitCommand

    service = RevisionService(session)
    submitted = await service.submit(document.id, SubmitCommand(actor_id=doctor.id))

    with pytest.raises(ConflictError, match="[Ss]elf-approval"):
        await service.approve(
            submitted.revision_set_id,
            ApproveRevisionCommand(actor_id=doctor.id, demo_mode=True),
            enqueue=False,
        )


@pytest.mark.asyncio
async def test_self_approval_requires_server_demo_policy_and_synthetic_document(revision_fixture) -> None:
    session, document, doctor, _ = revision_fixture
    from hospital_ai.services.revisions import ApproveRevisionCommand, RevisionService, SubmitCommand

    document.is_synthetic = True
    await session.commit()
    submitted = await RevisionService(session).submit(document.id, SubmitCommand(actor_id=doctor.id))

    settings = Settings(demo_mode=True, allow_self_approval_for_synthetic_data=True)
    accepted = await RevisionService(session, settings=settings).approve(
        submitted.revision_set_id,
        ApproveRevisionCommand(actor_id=doctor.id),
        enqueue=False,
    )
    assert accepted.state == "building"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("is_synthetic", "demo_mode"),
    [(False, True), (True, False)],
)
async def test_self_approval_rejects_real_data_or_non_demo_server(
    revision_fixture, is_synthetic: bool, demo_mode: bool
) -> None:
    session, document, doctor, _ = revision_fixture
    from hospital_ai.services.revisions import ApproveRevisionCommand, RevisionService, SubmitCommand

    document.is_synthetic = is_synthetic
    await session.commit()
    submitted = await RevisionService(session).submit(document.id, SubmitCommand(actor_id=doctor.id))

    with pytest.raises(ConflictError, match="[Ss]elf-approval"):
        await RevisionService(
            session,
            settings=Settings(demo_mode=demo_mode, allow_self_approval_for_synthetic_data=True),
        ).approve(
            submitted.revision_set_id,
            ApproveRevisionCommand(actor_id=doctor.id),
            enqueue=False,
        )


@pytest.mark.asyncio
async def test_approval_authorizes_build_without_publishing_document_pointer(revision_fixture) -> None:
    session, document, doctor, _ = revision_fixture
    from hospital_ai.services.revisions import ApproveRevisionCommand, RevisionService, SubmitCommand

    submitted = await RevisionService(session).submit(document.id, SubmitCommand(actor_id=doctor.id))
    accepted = await RevisionService(session).approve(
        submitted.revision_set_id,
        ApproveRevisionCommand(actor_id=RECORDS_ID),
        enqueue=False,
    )

    await session.refresh(document)
    persisted = await session.scalar(
        select(DocumentRevisionSet).where(DocumentRevisionSet.id == submitted.revision_set_id)
    )
    assert persisted is not None
    assert accepted.state == "building"
    assert persisted.status == "build_authorized"
    assert document.approved_revision_set_id is None


@pytest.mark.asyncio
async def test_activation_transitions_build_authorized_to_approved_and_supersedes_previous(revision_fixture) -> None:
    session, document, doctor, _ = revision_fixture
    from hospital_ai.db.clinical_documents import DocumentIndexGeneration, GenerationStageResult
    from hospital_ai.services.generations import GENERATION_STAGES, GenerationService, calculate_generation_hash
    from hospital_ai.services.revisions import ApproveRevisionCommand, RevisionService, SubmitCommand

    rev_service = RevisionService(session)
    submitted1 = await rev_service.submit(document.id, SubmitCommand(actor_id=doctor.id))
    accepted1 = await rev_service.approve(
        submitted1.revision_set_id,
        ApproveRevisionCommand(actor_id=RECORDS_ID),
        enqueue=False,
    )
    gen1 = await session.get(DocumentIndexGeneration, accepted1.generation_id)
    assert gen1 is not None
    gen1.generation_sha256 = calculate_generation_hash(["0" * 64] * len(GENERATION_STAGES))
    for stg in GENERATION_STAGES:
        session.add(GenerationStageResult(generation_id=gen1.id, stage=stg, status="completed", output_sha256="0" * 64))
    await session.commit()

    gen_service = GenerationService(session)
    await gen_service.activate(gen1.id)

    persisted1 = await session.get(DocumentRevisionSet, submitted1.revision_set_id)
    assert persisted1 is not None
    assert persisted1.status == "approved"

    submitted2 = await rev_service.submit(document.id, SubmitCommand(actor_id=doctor.id))
    accepted2 = await rev_service.approve(
        submitted2.revision_set_id,
        ApproveRevisionCommand(actor_id=RECORDS_ID),
        enqueue=False,
    )
    gen2 = await session.get(DocumentIndexGeneration, accepted2.generation_id)
    assert gen2 is not None
    gen2.generation_sha256 = calculate_generation_hash(["1" * 64] * len(GENERATION_STAGES))
    for stg in GENERATION_STAGES:
        session.add(GenerationStageResult(generation_id=gen2.id, stage=stg, status="completed", output_sha256="1" * 64))
    await session.commit()

    await gen_service.activate(gen2.id, expected_active_generation_id=gen1.id)
    await session.refresh(persisted1)
    persisted2 = await session.get(DocumentRevisionSet, submitted2.revision_set_id)
    assert persisted2 is not None
    assert persisted1.status == "superseded"
    assert persisted2.status == "approved"


@pytest.mark.asyncio
async def test_machine_draft_to_human_draft_transition(revision_fixture) -> None:
    session, document, doctor, page_revision = revision_fixture
    from hospital_ai.services.revisions import RevisionService, SavePageCommand

    result = await RevisionService(session).save_page(
        document.id,
        1,
        SavePageCommand(
            text="human edited text",
            parent_revision_id=page_revision.id,
            lock_version=1,
            actor_id=doctor.id,
        ),
    )
    assert result.status == "human_draft"
