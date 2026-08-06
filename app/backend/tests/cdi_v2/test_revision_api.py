from __future__ import annotations

import uuid

import pytest
from fastapi import Request

from hospital_ai.db.clinical_documents import DocumentDraftHead, DocumentPageRevision
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, RECORDS_ID
from hospital_ai.db.models import Document, PatientPermission, User


def _request(method="POST", path="/test") -> Request:
    return Request({"type": "http", "client": ("127.0.0.1", 8000), "method": method, "path": path, "headers": []})


@pytest.fixture
async def setup_data(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    if not doctor:
        doctor = User(id=uuid.uuid4(), email="doc@test.com", full_name="Doc", role="doctor", is_active=True)
        session.add(doctor)
        await session.commit()

    admin = User(id=uuid.uuid4(), email="admin@test.com", full_name="Admin", role="admin", is_active=True)
    session.add(admin)
    session.add(PatientPermission(user_id=admin.id, patient_id=PATIENT_ALICE_ID, scope="admin"))

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
        revision_type="machine_ocr",
        raw_text_snapshot="initial text",
        corrected_text="initial text",
        confidence=0.95,
        status="machine_draft",
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
    return doc, doctor, admin, machine_id


@pytest.mark.asyncio
async def test_save_draft_page_endpoint(session_and_settings, setup_data) -> None:
    session, _ = session_and_settings
    doc, doctor, _, machine_id = setup_data
    from hospital_ai.api.routes import document_revisions as rev_routes
    from hospital_ai.schemas.document_revisions import DraftPageWrite

    payload = DraftPageWrite(text="new text", parent_revision_id=machine_id, edit_reason="correction")
    res = await rev_routes.save_draft_page(
        document_id=doc.id,
        page_number=1,
        payload=payload,
        request=_request(method="PATCH", path=f"/api/v1/documents/{doc.id}/draft/pages/1"),
        if_match=1,
        idempotency_key="rev-save-1",
        current_user=doctor,
        session=session,
    )
    assert res.lock_version == 2
    assert res.page_revision_id is not None


@pytest.mark.asyncio
async def test_submit_and_approve_endpoints(session_and_settings, setup_data, monkeypatch: pytest.MonkeyPatch) -> None:
    session, _ = session_and_settings
    doc, doctor, admin, _ = setup_data
    from hospital_ai.api.routes import document_revisions as rev_routes
    from hospital_ai.schemas.document_revisions import ApproveRevisionRequest

    sub = await rev_routes.submit_draft(
        document_id=doc.id,
        request=_request(method="POST", path=f"/api/v1/documents/{doc.id}/draft/submit"),
        if_match=1,
        idempotency_key="rev-sub-1",
        current_user=doctor,
        session=session,
    )
    assert sub.status == "submitted"

    # Mock enqueue_generation_job so we don't depend on worker setup in API test
    monkeypatch.setattr(
        "hospital_ai.services.revisions.enqueue_build_generation_job", lambda *args, **kwargs: None, raising=False
    )

    approved = await rev_routes.approve_revision_set(
        document_id=doc.id,
        revision_set_id=sub.revision_set_id,
        payload=ApproveRevisionRequest(demo_mode=False),
        request=_request(method="POST", path=f"/api/v1/documents/{doc.id}/revision-sets/{sub.revision_set_id}/approve"),
        idempotency_key="rev-app-1",
        current_user=admin,
        session=session,
    )
    assert approved.state == "building"


@pytest.mark.asyncio
async def test_reject_endpoint_enforces_idempotency_payload(session_and_settings, setup_data) -> None:
    session, _ = session_and_settings
    doc, doctor, _, _ = setup_data
    records = await session.get(User, RECORDS_ID)
    from hospital_ai.api.routes import document_revisions as rev_routes
    from hospital_ai.schemas.document_revisions import RejectRevisionRequest

    submitted = await rev_routes.submit_draft(
        document_id=doc.id,
        request=_request(method="POST", path=f"/api/v1/documents/{doc.id}/draft/submit"),
        if_match=1,
        idempotency_key="reject-submit-1",
        current_user=doctor,
        session=session,
    )
    first = await rev_routes.reject_revision_set(
        document_id=doc.id,
        revision_set_id=submitted.revision_set_id,
        payload=RejectRevisionRequest(reason="first reason"),
        request=_request(path=f"/api/v1/documents/{doc.id}/revision-sets/{submitted.revision_set_id}/reject"),
        idempotency_key="reject-1",
        current_user=records,
        session=session,
    )
    assert first.status == "rejected"

    replay = await rev_routes.reject_revision_set(
        document_id=doc.id,
        revision_set_id=submitted.revision_set_id,
        payload=RejectRevisionRequest(reason="first reason"),
        request=_request(path=f"/api/v1/documents/{doc.id}/revision-sets/{submitted.revision_set_id}/reject"),
        idempotency_key="reject-1",
        current_user=records,
        session=session,
    )
    assert replay.status == "rejected"

    from hospital_ai.core.errors import ConflictError

    with pytest.raises(ConflictError):
        await rev_routes.reject_revision_set(
            document_id=doc.id,
            revision_set_id=submitted.revision_set_id,
            payload=RejectRevisionRequest(reason="different reason"),
            request=_request(path=f"/api/v1/documents/{doc.id}/revision-sets/{submitted.revision_set_id}/reject"),
            idempotency_key="reject-1",
            current_user=records,
            session=session,
        )

    from hospital_ai.db.clinical_documents import DocumentRevisionSet
    import datetime
    second_sub = DocumentRevisionSet(document_id=doc.id, revision_number=2, created_by_user_id=doctor.id, status="submitted", submitted_at=datetime.datetime.now(datetime.timezone.utc))
    session.add(second_sub)
    await session.commit()

    with pytest.raises(ConflictError):
        await rev_routes.reject_revision_set(
            document_id=doc.id,
            revision_set_id=second_sub.id,
            payload=RejectRevisionRequest(reason="first reason"),
            request=_request(path=f"/api/v1/documents/{doc.id}/revision-sets/{second_sub.id}/reject"),
            idempotency_key="reject-1",
            current_user=records,
            session=session,
        )


@pytest.mark.asyncio
async def test_restore_endpoint_enforces_idempotency_payload(session_and_settings, setup_data) -> None:
    session, _ = session_and_settings
    doc, doctor, _, machine_id = setup_data
    records = await session.get(User, RECORDS_ID)
    from hospital_ai.api.routes import document_revisions as rev_routes
    from hospital_ai.schemas.document_revisions import RestoreRevisionRequest
    from hospital_ai.db.clinical_documents import DocumentRevisionSet
    import datetime

    submitted = await rev_routes.submit_draft(
        document_id=doc.id,
        request=_request(method="POST", path=f"/api/v1/documents/{doc.id}/draft/submit"),
        if_match=1,
        idempotency_key="restore-submit-1",
        current_user=doctor,
        session=session,
    )
    first = await rev_routes.restore_revision(
        document_id=doc.id,
        revision_set_id=submitted.revision_set_id,
        payload=RestoreRevisionRequest(revision_id=machine_id, reason="first reason"),
        request=_request(path=f"/api/v1/documents/{doc.id}/revision-sets/{submitted.revision_set_id}/restore"),
        idempotency_key="restore-1",
        current_user=records,
        session=session,
    )
    assert first.status == "human_draft"

    replay = await rev_routes.restore_revision(
        document_id=doc.id,
        revision_set_id=submitted.revision_set_id,
        payload=RestoreRevisionRequest(revision_id=machine_id, reason="first reason"),
        request=_request(path=f"/api/v1/documents/{doc.id}/revision-sets/{submitted.revision_set_id}/restore"),
        idempotency_key="restore-1",
        current_user=records,
        session=session,
    )
    assert replay.status == "human_draft"

    from hospital_ai.core.errors import ConflictError

    with pytest.raises(ConflictError):
        await rev_routes.restore_revision(
            document_id=doc.id,
            revision_set_id=submitted.revision_set_id,
            payload=RestoreRevisionRequest(revision_id=machine_id, reason="different reason"),
            request=_request(path=f"/api/v1/documents/{doc.id}/revision-sets/{submitted.revision_set_id}/restore"),
            idempotency_key="restore-1",
            current_user=records,
            session=session,
        )

    second_sub2 = DocumentRevisionSet(document_id=doc.id, revision_number=3, created_by_user_id=doctor.id, status="submitted", submitted_at=datetime.datetime.now(datetime.timezone.utc))
    session.add(second_sub2)
    await session.commit()

    with pytest.raises(ConflictError):
        await rev_routes.restore_revision(
            document_id=doc.id,
            revision_set_id=second_sub2.id,
            payload=RestoreRevisionRequest(revision_id=machine_id, reason="first reason"),
            request=_request(path=f"/api/v1/documents/{doc.id}/revision-sets/{second_sub2.id}/restore"),
            idempotency_key="restore-1",
            current_user=records,
            session=session,
        )


def test_routes_registered_in_router() -> None:
    from hospital_ai.api.router import api_router

    paths = [route.path for route in api_router.routes]
    assert any("draft/pages" in p for p in paths)
    assert any("draft/submit" in p for p in paths)
    assert any("revision-sets" in p for p in paths)
