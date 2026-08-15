from __future__ import annotations

import uuid

import pytest
from fastapi import Request

from hospital_ai.api.routes.documents import (
    ReviewItemPatchRequest,
    get_document_facts,
    get_document_intelligence,
    patch_review_item,
)
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, RECORDS_ID
from hospital_ai.db.models import (
    ClinicalFact,
    Document,
    DocumentProcessingRun,
    DocumentReviewItem,
    PatientPermission,
    User,
)


@pytest.mark.asyncio
async def test_get_document_intelligence(session_and_settings):
    session, settings = session_and_settings
    current_user = await session.get(User, DOCTOR_ID)

    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Test Intelligence",
        document_type="clinical_note",
        storage_uri="mock/path",
        mime_type="text/plain",
        status="ready",
    )
    session.add(document)
    await session.commit()

    request = Request({"type": "http", "client": ("127.0.0.1", 8000)})
    result = await get_document_intelligence(
        document_id=document.id, request=request, session=session, current_user=current_user
    )

    assert result["document_id"] == str(document.id)
    assert result["status"] == "ready"


@pytest.mark.asyncio
async def test_get_document_facts(session_and_settings):
    session, settings = session_and_settings
    current_user = await session.get(User, DOCTOR_ID)

    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Test Facts",
        document_type="clinical_note",
        storage_uri="mock/path",
        mime_type="text/plain",
        status="ready",
    )
    session.add(document)
    await session.commit()

    request = Request({"type": "http", "client": ("127.0.0.1", 8000)})
    result = await get_document_facts(
        document_id=document.id, request=request, session=session, current_user=current_user
    )

    assert result["document_id"] == str(document.id)
    assert isinstance(result["facts"], list)


@pytest.mark.asyncio
async def test_patch_review_item_success(session_and_settings):
    session, settings = session_and_settings
    current_user = await session.get(User, DOCTOR_ID)

    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Test Review",
        document_type="clinical_note",
        storage_uri="mock/path",
        mime_type="text/plain",
        status="review_required",
    )
    session.add(document)
    await session.commit()

    run_id = uuid.uuid4()
    run = DocumentProcessingRun(id=run_id, document_id=document.id, configuration_version="1.0", status="completed")
    session.add(run)

    fact = ClinicalFact(
        document_id=document.id, run_id=run_id, fact_type="medication", raw_value="Aspirin", status="unverified"
    )
    session.add(fact)
    await session.flush()

    review_item = DocumentReviewItem(
        document_id=document.id, run_id=run_id, fact_id=fact.id, field_name="medication", review_status="pending"
    )
    session.add(review_item)
    await session.commit()

    request = Request({"type": "http", "client": ("127.0.0.1", 8000)})
    payload = ReviewItemPatchRequest(
        action="approve", value={"medication": "Aspirin"}, reason="Looks correct", version=1, fact_type="medication"
    )

    result = await patch_review_item(
        document_id=document.id,
        review_item_id=review_item.id,
        payload=payload,
        request=request,
        session=session,
        current_user=current_user,
    )

    assert result["review_item_id"] == str(review_item.id)
    assert result["status"] == "approved"


@pytest.mark.asyncio
async def test_patch_review_item_rbac_rejection(session_and_settings):
    session, settings = session_and_settings
    current_user = await session.get(User, RECORDS_ID)  # records staff

    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Test Review RBAC",
        document_type="clinical_note",
        storage_uri="mock/path",
        mime_type="text/plain",
        status="review_required",
    )
    session.add(document)
    await session.commit()

    run_id = uuid.uuid4()
    run = DocumentProcessingRun(id=run_id, document_id=document.id, configuration_version="1.0", status="completed")
    session.add(run)

    fact = ClinicalFact(
        document_id=document.id, run_id=run_id, fact_type="medication", raw_value="Aspirin", status="unverified"
    )
    session.add(fact)
    await session.flush()

    review_item = DocumentReviewItem(
        document_id=document.id, run_id=run_id, fact_id=fact.id, field_name="medication", review_status="pending"
    )
    session.add(review_item)

    perm = PatientPermission(user_id=RECORDS_ID, patient_id=PATIENT_ALICE_ID, scope="read")
    session.add(perm)
    await session.commit()

    request = Request({"type": "http", "client": ("127.0.0.1", 8000)})
    payload = ReviewItemPatchRequest(
        action="approve", value={"medication": "Aspirin"}, reason="Looks correct", version=1, fact_type="medication"
    )

    # records_staff cannot confirm medication fields
    with pytest.raises(PermissionDeniedError) as exc:
        await patch_review_item(
            document_id=document.id,
            review_item_id=review_item.id,
            payload=payload,
            request=request,
            session=session,
            current_user=current_user,
        )
    assert "records_staff cannot confirm clinical fields." in str(exc.value)
