from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

import pytest
from fastapi import Request
from sqlalchemy import select

from hospital_ai.core.errors import NotFoundError, PermissionDeniedError
from hospital_ai.db.clinical_documents import (
    DocumentDraftHead,
    DocumentIndexGeneration,
    DocumentPageRevision,
    DocumentRevisionSet,
)
from hospital_ai.db.migrations import ADMIN_ID, DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID, RECORDS_ID, SECURITY_ID
from hospital_ai.db.models import AuditLog, Document, User


def _request(method: str = "POST", path: str = "/test") -> Request:
    return Request({"type": "http", "client": ("127.0.0.1", 8000), "method": method, "path": path, "headers": []})


async def _make_document(
    session, *, patient_id: uuid.UUID, actor_id: uuid.UUID
) -> tuple[Document, DocumentRevisionSet, DocumentIndexGeneration, DocumentPageRevision]:
    document = Document(
        id=uuid.uuid4(),
        patient_id=patient_id,
        uploaded_by=actor_id,
        title="Binding test document",
        document_type="progress_note",
        storage_uri="local://binding.pdf",
        mime_type="application/pdf",
        status="ready",
    )
    session.add(document)
    await session.flush()

    page_revision = DocumentPageRevision(
        id=uuid.uuid4(),
        document_id=document.id,
        page_number=1,
        revision_number=1,
        revision_type="machine_ocr",
        raw_text_snapshot="synthetic text",
        corrected_text="synthetic text",
        confidence=1.0,
        status="approved",
        created_by_user_id=actor_id,
        content_sha256=hashlib.sha256(b"synthetic text").hexdigest(),
        version=1,
    )
    revision_set = DocumentRevisionSet(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_number=1,
        status="submitted",
        created_by_user_id=actor_id,
        submitted_at=datetime.now(UTC),
    )
    session.add_all([page_revision, revision_set])
    await session.flush()

    generation = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_set_id=revision_set.id,
        state="building",
        revision_set_sha256="a" * 64,
    )
    session.add(generation)
    await session.flush()
    document.active_index_generation_id = generation.id
    document.approved_revision_set_id = revision_set.id
    session.add(
        DocumentDraftHead(
            document_id=document.id,
            selected_pages={"1": str(page_revision.id)},
            lock_version=1,
            updated_by_user_id=actor_id,
        )
    )
    await session.commit()
    return document, revision_set, generation, page_revision


@pytest.mark.asyncio
async def test_revision_set_path_binding_is_not_found_and_audited(session_and_settings) -> None:
    session, _ = session_and_settings
    document_a, _, _, _ = await _make_document(session, patient_id=PATIENT_ALICE_ID, actor_id=DOCTOR_ID)
    _, revision_set_b, _, _ = await _make_document(session, patient_id=PATIENT_BOB_ID, actor_id=DOCTOR_ID)
    admin = await session.get(User, ADMIN_ID)

    from hospital_ai.api.routes.document_revisions import reject_revision_set
    from hospital_ai.schemas.document_revisions import RejectRevisionRequest

    with pytest.raises(NotFoundError):
        await reject_revision_set(
            document_id=document_a.id,
            revision_set_id=revision_set_b.id,
            payload=RejectRevisionRequest(reason="cross-resource probe"),
            request=_request(path="/revision-sets/reject"),
            idempotency_key="binding-reject-1",
            current_user=admin,
            session=session,
        )

    denial = await session.scalar(
        select(AuditLog)
        .where(
            AuditLog.actor_user_id == ADMIN_ID,
            AuditLog.patient_id == PATIENT_ALICE_ID,
            AuditLog.action == "document_revision.reject",
            AuditLog.outcome == "denied",
        )
        .order_by(AuditLog.created_at.desc())
    )
    assert denial is not None


@pytest.mark.asyncio
async def test_generation_path_binding_rejects_cross_document_retry(session_and_settings) -> None:
    session, _ = session_and_settings
    document_a, _, _, _ = await _make_document(session, patient_id=PATIENT_ALICE_ID, actor_id=DOCTOR_ID)
    _, _, generation_b, _ = await _make_document(session, patient_id=PATIENT_BOB_ID, actor_id=DOCTOR_ID)
    admin = await session.get(User, ADMIN_ID)

    from hospital_ai.api.routes.document_generations import retry_generation

    with pytest.raises(NotFoundError):
        await retry_generation(
            document_id=document_a.id,
            generation_id=generation_b.id,
            request=_request(path="/index-generations/retry"),
            idempotency_key="binding-gen-retry-1",
            current_user=admin,
            session=session,
        )

    assert await session.get(DocumentIndexGeneration, generation_b.id) is not None
    assert not any(
        row.retry_of_generation_id == generation_b.id for row in await session.scalars(select(DocumentIndexGeneration))
    )

    denial = await session.scalar(
        select(AuditLog)
        .where(
            AuditLog.actor_user_id == ADMIN_ID,
            AuditLog.patient_id == PATIENT_ALICE_ID,
            AuditLog.action == "document_generation.retry",
            AuditLog.outcome == "denied",
        )
        .order_by(AuditLog.created_at.desc())
    )
    assert denial is not None


@pytest.mark.asyncio
async def test_revision_page_path_binding_rejects_cross_document_page(session_and_settings) -> None:
    session, _ = session_and_settings
    document_a, _, _, _ = await _make_document(session, patient_id=PATIENT_ALICE_ID, actor_id=DOCTOR_ID)
    _, revision_set_b, _, _ = await _make_document(session, patient_id=PATIENT_BOB_ID, actor_id=DOCTOR_ID)
    doctor = await session.get(User, DOCTOR_ID)

    from hospital_ai.api.routes.document_revisions import get_revision_page

    with pytest.raises(NotFoundError):
        await get_revision_page(
            document_id=document_a.id,
            revision_set_id=revision_set_b.id,
            page_number=1,
            current_user=doctor,
            session=session,
        )

    denial = await session.scalar(
        select(AuditLog)
        .where(
            AuditLog.actor_user_id == DOCTOR_ID,
            AuditLog.patient_id == PATIENT_ALICE_ID,
            AuditLog.action == "document_revision.page.read",
            AuditLog.outcome == "denied",
        )
        .order_by(AuditLog.created_at.desc())
    )
    assert denial is not None


@pytest.mark.asyncio
async def test_page_revision_binding_rejects_cross_document_page_revision(session_and_settings) -> None:
    session, _ = session_and_settings
    document_a, revision_set_a, _, _ = await _make_document(session, patient_id=PATIENT_ALICE_ID, actor_id=DOCTOR_ID)
    _, _, _, page_revision_b = await _make_document(session, patient_id=PATIENT_BOB_ID, actor_id=DOCTOR_ID)
    doctor = await session.get(User, DOCTOR_ID)
    records = await session.get(User, RECORDS_ID)

    from hospital_ai.api.routes.document_revisions import restore_revision, save_draft_page
    from hospital_ai.schemas.document_revisions import DraftPageWrite, RestoreRevisionRequest

    with pytest.raises(NotFoundError):
        await save_draft_page(
            document_id=document_a.id,
            page_number=1,
            payload=DraftPageWrite(text="illegal edit", parent_revision_id=page_revision_b.id, edit_reason="probe"),
            request=_request(path=f"/documents/{document_a.id}/draft/pages/1"),
            if_match=1,
            idempotency_key="binding-save-page-1",
            current_user=doctor,
            session=session,
        )

    denial = await session.scalar(
        select(AuditLog)
        .where(
            AuditLog.actor_user_id == DOCTOR_ID,
            AuditLog.patient_id == PATIENT_ALICE_ID,
            AuditLog.action == "document_revision.page.save",
            AuditLog.outcome == "denied",
        )
        .order_by(AuditLog.created_at.desc())
    )
    assert denial is not None

    with pytest.raises(NotFoundError):
        await restore_revision(
            document_id=document_a.id,
            revision_set_id=revision_set_a.id,
            payload=RestoreRevisionRequest(revision_id=page_revision_b.id, reason="cross-resource restore probe"),
            request=_request(path=f"/documents/{document_a.id}/revision-sets/{revision_set_a.id}/restore"),
            idempotency_key="binding-restore-1",
            current_user=records,
            session=session,
        )

    denial_restore = await session.scalar(
        select(AuditLog)
        .where(
            AuditLog.actor_user_id == records.id,
            AuditLog.patient_id == PATIENT_ALICE_ID,
            AuditLog.action == "document_revision.restore",
            AuditLog.outcome == "denied",
        )
        .order_by(AuditLog.created_at.desc())
    )
    assert denial_restore is not None


@pytest.mark.asyncio
async def test_patient_a_user_cannot_access_graph_document_b(session_and_settings) -> None:
    session, _ = session_and_settings
    document_b, _, _, _ = await _make_document(session, patient_id=PATIENT_BOB_ID, actor_id=DOCTOR_ID)
    doctor = await session.get(User, DOCTOR_ID)

    from hospital_ai.api.routes.document_graph import get_document_graph, get_document_timeline
    from hospital_ai.services.graph_query import GraphFilters

    with pytest.raises(PermissionDeniedError):
        await get_document_graph(document_b.id, GraphFilters(), session, doctor)
    with pytest.raises(PermissionDeniedError):
        await get_document_timeline(document_b.id, session, doctor)

    denial = await session.scalar(
        select(AuditLog)
        .where(
            AuditLog.actor_user_id == DOCTOR_ID,
            AuditLog.patient_id == PATIENT_BOB_ID,
            AuditLog.outcome == "denied",
        )
        .order_by(AuditLog.created_at.desc())
    )
    assert denial is not None


@pytest.mark.asyncio
async def test_graph_and_timeline_require_patient_permission(session_and_settings) -> None:
    session, _ = session_and_settings
    document, _, _, _ = await _make_document(session, patient_id=PATIENT_ALICE_ID, actor_id=DOCTOR_ID)
    security = await session.get(User, SECURITY_ID)

    from hospital_ai.api.routes.document_graph import get_document_graph, get_document_timeline
    from hospital_ai.services.graph_query import GraphFilters

    with pytest.raises(PermissionDeniedError):
        await get_document_graph(document.id, GraphFilters(), session, security)
    with pytest.raises(PermissionDeniedError):
        await get_document_timeline(document.id, session, security)

    denial = await session.scalar(
        select(AuditLog)
        .where(
            AuditLog.actor_user_id == SECURITY_ID,
            AuditLog.patient_id == PATIENT_ALICE_ID,
            AuditLog.outcome == "denied",
        )
        .order_by(AuditLog.created_at.desc())
    )
    assert denial is not None


@pytest.mark.asyncio
async def test_raw_revision_read_requires_view_raw_capability(session_and_settings) -> None:
    session, _ = session_and_settings
    document, _, _, _ = await _make_document(session, patient_id=PATIENT_ALICE_ID, actor_id=DOCTOR_ID)
    admin = await session.get(User, ADMIN_ID)

    from hospital_ai.api.routes.document_revisions import get_draft_page

    with pytest.raises(PermissionDeniedError):
        await get_draft_page(document.id, 1, admin, session)

    denial = await session.scalar(
        select(AuditLog)
        .where(
            AuditLog.actor_user_id == ADMIN_ID,
            AuditLog.patient_id == PATIENT_ALICE_ID,
            AuditLog.action == "document_revision.draft.read",
            AuditLog.outcome == "denied",
        )
        .order_by(AuditLog.created_at.desc())
    )
    assert denial is not None


@pytest.mark.asyncio
async def test_upload_session_requires_upload_scope(session_and_settings) -> None:
    session, _ = session_and_settings
    security = await session.get(User, SECURITY_ID)

    from hospital_ai.api.routes.document_uploads import create_upload_session
    from hospital_ai.schemas.document_uploads import UploadSessionCreate

    with pytest.raises(PermissionDeniedError):
        await create_upload_session(
            payload=UploadSessionCreate(
                patient_id=PATIENT_ALICE_ID,
                filename="report.pdf",
                expected_size=8,
                expected_sha256="a" * 64,
                claimed_mime_type="application/pdf",
            ),
            request=_request(path="/upload-sessions"),
            idempotency_key="binding-upload-1",
            session=session,
            current_user=security,
        )

    denial = await session.scalar(
        select(AuditLog)
        .where(
            AuditLog.actor_user_id == SECURITY_ID,
            AuditLog.patient_id == PATIENT_ALICE_ID,
            AuditLog.action == "document.upload_session.create",
            AuditLog.outcome == "denied",
        )
        .order_by(AuditLog.created_at.desc())
    )
    assert denial is not None


@pytest.mark.asyncio
async def test_upload_finalize_binding_rejects_cross_document_upload(session_and_settings) -> None:
    session, _ = session_and_settings
    document_a, _, _, _ = await _make_document(session, patient_id=PATIENT_ALICE_ID, actor_id=DOCTOR_ID)
    document_b, _, _, _ = await _make_document(session, patient_id=PATIENT_BOB_ID, actor_id=DOCTOR_ID)
    admin = await session.get(User, ADMIN_ID)

    from hospital_ai.db.clinical_documents import DocumentUpload

    upload_b = DocumentUpload(
        id=uuid.uuid4(),
        document_id=document_b.id,
        state="pending_upload",
        object_key="test/key.pdf",
        expected_sha256="a" * 64,
        byte_size=100,
        mime_type="application/pdf",
        actor_user_id=admin.id,
    )
    session.add(upload_b)
    await session.commit()

    from hospital_ai.api.routes.document_uploads import finalize_upload_session

    with pytest.raises(NotFoundError):
        await finalize_upload_session(
            document_id=document_a.id,
            upload_id=upload_b.id,
            request=_request(path="/finalize"),
            idempotency_key="finalize-bind-1",
            session=session,
            current_user=admin,
        )

    denial = await session.scalar(
        select(AuditLog)
        .where(
            AuditLog.actor_user_id == ADMIN_ID,
            AuditLog.patient_id == PATIENT_ALICE_ID,
            AuditLog.action == "document.upload_session.finalize",
            AuditLog.outcome == "denied",
        )
        .order_by(AuditLog.created_at.desc())
    )
    assert denial is not None


@pytest.mark.asyncio
async def test_review_item_binding_rejects_cross_document_item(session_and_settings) -> None:
    session, _ = session_and_settings
    document_a, _, _, _ = await _make_document(session, patient_id=PATIENT_ALICE_ID, actor_id=DOCTOR_ID)
    document_b, _, _, _ = await _make_document(session, patient_id=PATIENT_BOB_ID, actor_id=DOCTOR_ID)
    admin = await session.get(User, ADMIN_ID)

    from hospital_ai.db.models import DocumentProcessingRun, DocumentReviewItem

    run_id = uuid.uuid4()
    run = DocumentProcessingRun(id=run_id, document_id=document_b.id, configuration_version="1.0", status="completed")
    session.add(run)

    item_b = DocumentReviewItem(
        id=uuid.uuid4(),
        document_id=document_b.id,
        run_id=run_id,
        field_name="patient_name",
        original_value="Bob",
        suggested_value="Robert",
        review_status="pending",
    )
    session.add(item_b)
    await session.commit()

    from hospital_ai.api.routes.documents import ReviewItemPatchRequest, patch_review_item

    with pytest.raises(NotFoundError):
        await patch_review_item(
            document_id=document_a.id,
            review_item_id=item_b.id,
            payload=ReviewItemPatchRequest(action="approve", reason="binding check", version=1),
            request=_request(path="/review-items/patch"),
            session=session,
            current_user=admin,
        )

    denial = await session.scalar(
        select(AuditLog)
        .where(
            AuditLog.actor_user_id == ADMIN_ID,
            AuditLog.patient_id == PATIENT_ALICE_ID,
            AuditLog.action == "document.review_item.patch",
            AuditLog.outcome == "denied",
        )
        .order_by(AuditLog.created_at.desc())
    )
    assert denial is not None
