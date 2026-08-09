from __future__ import annotations

import hashlib
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select

from hospital_ai.db.clinical_documents import DocumentDraftHead, DocumentPageRevision, OcrBlock, OcrLine, OcrSpan
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
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
        title="Geometry test document",
        document_type="progress_note",
        storage_uri="local://test/geometry.pdf",
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


async def _add_geometry(session, page_revision_id: uuid.UUID, text: str) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    block = OcrBlock(
        page_revision_id=page_revision_id,
        text_start_offset=0,
        text_end_offset=len(text),
        polygon={"points": [[0, 0], [1, 1]]},
        confidence=0.99,
        reading_order=1,
        alignment_status="aligned",
    )
    session.add(block)
    await session.flush()
    line = OcrLine(
        block_id=block.id,
        page_revision_id=page_revision_id,
        text_start_offset=0,
        text_end_offset=len(text),
        polygon={"points": [[0, 0], [1, 1]]},
        confidence=0.99,
        reading_order=1,
        alignment_status="aligned",
    )
    session.add(line)
    await session.flush()
    span = OcrSpan(
        line_id=line.id,
        page_revision_id=page_revision_id,
        text_start_offset=0,
        text_end_offset=len(text),
        polygon={"points": [[0, 0], [1, 1]]},
        confidence=0.99,
        reading_order=1,
        alignment_status="aligned",
        normalized_text=text,
        source_engine_metadata={"engine": "test"},
    )
    session.add(span)
    await session.commit()
    return block.id, line.id, span.id


@pytest.mark.asyncio
async def test_changed_text_clones_geometry_as_stale(revision_fixture) -> None:
    session, document, doctor, page_revision = revision_fixture
    await _add_geometry(session, page_revision.id, page_revision.corrected_text)

    from hospital_ai.services.revisions import RevisionService, SavePageCommand

    result = await RevisionService(session).save_page(
        document.id,
        1,
        SavePageCommand(
            text="changed clinical text",
            parent_revision_id=page_revision.id,
            lock_version=1,
            actor_id=doctor.id,
        ),
    )

    cloned_block = await session.scalar(select(OcrBlock).where(OcrBlock.page_revision_id == result.page_revision_id))
    cloned_line = await session.scalar(select(OcrLine).where(OcrLine.page_revision_id == result.page_revision_id))
    cloned_span = await session.scalar(select(OcrSpan).where(OcrSpan.page_revision_id == result.page_revision_id))
    assert cloned_block is not None and cloned_block.alignment_status == "stale"
    assert cloned_line is not None and cloned_line.alignment_status == "stale"
    assert cloned_span is not None and cloned_span.alignment_status == "stale"


@pytest.mark.asyncio
async def test_exact_text_edit_preserves_aligned_geometry(revision_fixture) -> None:
    session, document, doctor, page_revision = revision_fixture
    await _add_geometry(session, page_revision.id, page_revision.corrected_text)

    from hospital_ai.services.revisions import RevisionService, SavePageCommand

    result = await RevisionService(session).save_page(
        document.id,
        1,
        SavePageCommand(
            text=page_revision.corrected_text,
            parent_revision_id=page_revision.id,
            lock_version=1,
            actor_id=doctor.id,
        ),
    )
    cloned_span = await session.scalar(select(OcrSpan).where(OcrSpan.page_revision_id == result.page_revision_id))
    assert cloned_span is not None and cloned_span.alignment_status == "aligned"


@pytest.mark.asyncio
async def test_revision_set_hash_is_content_and_geometry_bound(revision_fixture) -> None:
    session, document, doctor, page_revision = revision_fixture
    from hospital_ai.services.revisions import RevisionService, SubmitCommand

    service = RevisionService(session)
    submitted = await service.submit(document.id, SubmitCommand(actor_id=doctor.id))
    first_hash = await service._revision_set_hash(submitted.revision_set_id)
    assert first_hash != hashlib.sha256(str(submitted.revision_set_id).encode()).hexdigest()

    page_revision.corrected_text = "changed clinical text"
    page_revision.content_sha256 = hashlib.sha256(page_revision.corrected_text.encode()).hexdigest()
    await session.commit()
    second_hash = await service._revision_set_hash(submitted.revision_set_id)
    assert second_hash != first_hash


@pytest.mark.asyncio
async def test_serialize_exact_evidence_rejects_stale_geometry(revision_fixture) -> None:
    session, document, doctor, page_revision = revision_fixture
    await _add_geometry(session, page_revision.id, page_revision.corrected_text)

    from hospital_ai.core.errors import ConflictError
    from hospital_ai.services.revisions import RevisionService, SavePageCommand

    service = RevisionService(session)
    evidence = await service.serialize_exact_evidence(document.id, page_revision.id)
    assert evidence["alignment_state"] == "aligned"
    assert len(evidence["spans"]) == 1

    result = await service.save_page(
        document.id,
        1,
        SavePageCommand(
            text="changed clinical text",
            parent_revision_id=page_revision.id,
            lock_version=1,
            actor_id=doctor.id,
        ),
    )
    with pytest.raises(ConflictError, match="[Ss]tale geometry|[Ss]tale"):
        await service.serialize_exact_evidence(document.id, result.page_revision_id)
