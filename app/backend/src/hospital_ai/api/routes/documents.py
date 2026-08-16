import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.errors import NotFoundError, PermissionDeniedError, ValidationAppError
from hospital_ai.core.security import PATIENT_READ_SCOPES, PATIENT_UPLOAD_SCOPES, new_trace_id
from hospital_ai.db.models import (
    ClinicalFact,
    Document,
    DocumentPage,
    DocumentProcessingEvent,
    DocumentReviewItem,
    User,
)
from hospital_ai.schemas.documents import (
    DocumentDetailRead,
    DocumentListResponse,
    DocumentPageRead,
    DocumentRead,
    DocumentSearchRequest,
    DocumentSearchResponse,
    EvidenceRead,
)
from hospital_ai.services.audit import AuditService
from hospital_ai.services.embeddings import EmbeddingService
from hospital_ai.services.permissions import PermissionService, active_patient_permission_exists
from hospital_ai.services.retrieval import RetrievalService
from hospital_ai.services.storage import get_storage_service
from hospital_ai.workers.jobs import process_document
from hospital_ai.workers.queue import enqueue_document_indexing

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "application/json",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/png",
    "image/jpeg",
}

HL7_UPLOAD_MIME_TYPES = {
    "application/octet-stream",
    "text/plain",
    "application/hl7-v2",
    "application/hl7-v2+er7",
}

ALLOWED_DOCUMENT_TYPES = {
    "chat_attachment",
    "clinical_note",
    "lab_result",
    "prescription",
    "discharge_summary",
    "imaging_report",
}


def normalize_upload_mime_type(filename: str | None, content_type: str | None) -> str:
    """Normalize browser HL7 uploads without admitting generic binary files."""
    if not content_type or not content_type.strip():
        return "application/octet-stream"

    mime_type = content_type.strip().lower()
    if (filename or "").lower().endswith(".hl7") and mime_type in HL7_UPLOAD_MIME_TYPES:
        return "text/plain"
    return mime_type


@router.post("", response_model=DocumentRead)
async def upload_document(
    request: Request,
    patient_id: uuid.UUID = Form(...),
    title: str = Form(..., min_length=1, max_length=255),
    document_type: str = Form(..., min_length=1, max_length=64),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> Document:
    trace_id = new_trace_id()
    await PermissionService(session).require_upload_or_admin_role(
        user=current_user,
        patient_id=patient_id,
        action="document.upload",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )

    # F-SEC-005: enforce length limits even though Form already validates
    # so that early rejection happens before any storage IO.
    title = title.strip()
    document_type = document_type.strip()
    if not title or not document_type:
        raise ValidationAppError("Title and document_type must not be blank.")

    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise ValidationAppError(f"Invalid document type. Allowed types: {', '.join(sorted(ALLOWED_DOCUMENT_TYPES))}")

    mime_type = normalize_upload_mime_type(file.filename, file.content_type)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValidationAppError(f"Unsupported file type: {mime_type}")

    document = Document(
        patient_id=patient_id,
        uploaded_by=current_user.id,
        title=title,
        document_type=document_type,
        storage_uri="pending",
        mime_type=mime_type,
        status="uploaded",
    )
    session.add(document)
    await session.flush()
    document.storage_uri = await get_storage_service(settings).save_upload(
        patient_id=patient_id,
        document_id=document.id,
        file=file,
    )
    session.add(
        DocumentProcessingEvent(
            document_id=document.id,
            attempt=0,
            sequence=1,
            stage="upload",
            state="completed",
        )
    )
    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="document.upload",
        object_type="document",
        object_id=document.id,
        patient_id=patient_id,
        outcome="allowed",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
        metadata={"has_title": bool(title), "document_type": document_type},
    )
    await session.commit()

    if settings.worker_inline:
        await process_document(session, document.id, settings)
        await session.refresh(document)
    else:
        enqueue_status = enqueue_document_indexing(document.id, settings)
        await AuditService(session).record(
            actor_user_id=current_user.id,
            action="document.index.enqueue",
            object_type="document",
            object_id=document.id,
            patient_id=patient_id,
            outcome="allowed",
            trace_id=trace_id,
            ip_address=get_request_ip(request),
            metadata={"enqueue_status": enqueue_status},
        )
        await session.commit()
    return document


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    request: Request,
    patient_id: Optional[uuid.UUID] = None,
    status: Optional[str] = Query(default=None, min_length=1, max_length=32),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentListResponse:
    stmt = select(Document).where(Document.deleted_at.is_(None)).order_by(Document.created_at.desc())
    if patient_id is not None:
        stmt = stmt.where(Document.patient_id == patient_id)
    if status is not None:
        stmt = stmt.where(Document.status == status)
    # Enforce patient permission check on all roles.
    stmt = stmt.where(
        active_patient_permission_exists(
            user_id=current_user.id,
            patient_id=Document.patient_id,
            accepted_scopes=set(PATIENT_READ_SCOPES) | set(PATIENT_UPLOAD_SCOPES),
        )
    )
    result = await session.execute(stmt.limit(limit))
    documents = list(result.scalars().all())
    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="document.list",
        object_type="document",
        patient_id=patient_id,
        outcome="allowed",
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
        metadata={"result_count": len(documents), "status": status},
    )
    await session.commit()
    return DocumentListResponse(items=documents)


@router.get("/{document_id}", response_model=DocumentDetailRead)
async def get_document(
    document_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Document:
    document = await _get_document_or_404(session, document_id)
    trace_id = new_trace_id()
    await PermissionService(session).require_read(
        user=current_user,
        patient_id=document.patient_id,
        action="document.read",
        trace_id=trace_id,
        object_type="document",
        object_id=document.id,
        ip_address=get_request_ip(request),
    )
    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="document.read",
        object_type="document",
        object_id=document.id,
        patient_id=document.patient_id,
        outcome="allowed",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )
    await session.commit()
    await session.refresh(document, attribute_names=["processing_events"])
    return document


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    """Serve the original upload only after the normal document read check."""
    document = await _get_document_or_404(session, document_id)
    trace_id = new_trace_id()
    await PermissionService(session).require_read(
        user=current_user,
        patient_id=document.patient_id,
        action="document.content.read",
        trace_id=trace_id,
        object_type="document",
        object_id=document.id,
        ip_address=get_request_ip(request),
    )
    try:
        content = await asyncio.to_thread(get_storage_service(settings).read_bytes, document.storage_uri)
    except (FileNotFoundError, ValueError) as exc:
        raise NotFoundError("Document content not found.") from exc
    return Response(content=content, media_type=document.mime_type)


@router.get("/{document_id}/pages/{page_number}", response_model=DocumentPageRead)
async def get_document_page(
    document_id: uuid.UUID,
    page_number: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentPage:
    document = await _get_document_or_404(session, document_id)
    trace_id = new_trace_id()
    await PermissionService(session).require_read(
        user=current_user,
        patient_id=document.patient_id,
        action="document.page.read",
        trace_id=trace_id,
        object_type="document",
        object_id=document.id,
        ip_address=get_request_ip(request),
    )
    result = await session.execute(
        select(DocumentPage).where(
            DocumentPage.document_id == document_id,
            DocumentPage.page_number == page_number,
        )
    )
    page = result.scalar_one_or_none()
    if page is None:
        raise NotFoundError("Document page not found.")
    return page


@router.get("/{document_id}/pages/{page_number}/image")
async def get_document_page_image(
    document_id: uuid.UUID,
    page_number: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    document = await _get_document_or_404(session, document_id)
    trace_id = new_trace_id()
    await PermissionService(session).require_read(
        user=current_user,
        patient_id=document.patient_id,
        action="document.page.image.read",
        trace_id=trace_id,
        object_type="document",
        object_id=document.id,
        ip_address=get_request_ip(request),
    )

    try:
        image_bytes = await asyncio.to_thread(
            get_storage_service(settings).read_page_image,
            document.patient_id,
            document.id,
            page_number,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise NotFoundError("Document page image not found.") from exc

    return Response(content=image_bytes, media_type="image/png")


@router.post("/{document_id}/retry-index", response_model=DocumentRead)
async def retry_index(
    document_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> Document:
    document = await _get_document_or_404(session, document_id)
    trace_id = new_trace_id()
    await PermissionService(session).require_upload_or_admin_role(
        user=current_user,
        patient_id=document.patient_id,
        action="document.retry_index",
        trace_id=trace_id,
        object_type="document",
        object_id=document.id,
        ip_address=get_request_ip(request),
    )
    document.status = "uploaded"
    document.ocr_error = None
    await session.commit()

    if settings.worker_inline:
        await process_document(session, document.id, settings)
        await session.refresh(document)
    else:
        enqueue_document_indexing(document.id, settings)
    return document


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    payload: DocumentSearchRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> DocumentSearchResponse:
    trace_id = new_trace_id()
    await PermissionService(session).require_read(
        user=current_user,
        patient_id=payload.patient_id,
        action="document.search",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )
    query_embedding = await EmbeddingService(settings).embed(payload.query)
    evidence = await RetrievalService(session).search(
        user_id=current_user.id,
        patient_id=payload.patient_id,
        query_embedding=query_embedding,
        top_k=payload.top_k,
    )
    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="document.search",
        object_type="document_chunk",
        patient_id=payload.patient_id,
        outcome="allowed",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
        metadata={"result_count": len(evidence)},
    )
    await session.commit()
    return DocumentSearchResponse(items=[evidence_to_schema(item) for item in evidence])


async def _get_document_or_404(session: AsyncSession, document_id: uuid.UUID) -> Document:
    document = await session.get(Document, document_id)
    if document is None or document.deleted_at is not None:
        raise NotFoundError("Document not found.")
    return document


def evidence_to_schema(item) -> EvidenceRead:
    return EvidenceRead(
        evidence_id=item.evidence_id,
        document_id=item.document_id,
        document_title=item.document_title,
        page=item.page,
        chunk_id=item.chunk_id,
        score=item.score,
        content=item.content,
        metadata=item.metadata,
    )


class ReviewItemPatchRequest(BaseModel):
    action: str
    value: Optional[dict[str, Any]] = None
    reason: str
    version: int


@router.get("/{document_id}/intelligence")
async def get_document_intelligence(
    document_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    document = await _get_document_or_404(session, document_id)
    trace_id = new_trace_id()
    await PermissionService(session).require_read(
        user=current_user,
        patient_id=document.patient_id,
        action="document.intelligence.read",
        trace_id=trace_id,
        object_type="document",
        object_id=document.id,
        ip_address=get_request_ip(request),
    )

    facts_result = await session.execute(
        select(ClinicalFact).where(
            ClinicalFact.document_id == document_id,
            ClinicalFact.generation_id.is_not_distinct_from(document.active_index_generation_id)
        )
    )
    facts = facts_result.scalars().all()

    reviews_result = await session.execute(
        select(DocumentReviewItem).where(DocumentReviewItem.document_id == document_id)
    )
    reviews = reviews_result.scalars().all()

    return {
        "document_id": str(document.id),
        "status": document.status,
        "facts_count": len(facts),
        "review_items_count": len(reviews),
    }


@router.get("/{document_id}/facts")
async def get_document_facts(
    document_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    document = await _get_document_or_404(session, document_id)
    trace_id = new_trace_id()
    await PermissionService(session).require_read(
        user=current_user,
        patient_id=document.patient_id,
        action="document.facts.read",
        trace_id=trace_id,
        object_type="document",
        object_id=document.id,
        ip_address=get_request_ip(request),
    )

    facts_result = await session.execute(
        select(ClinicalFact).where(
            ClinicalFact.document_id == document_id,
            ClinicalFact.generation_id.is_not_distinct_from(document.active_index_generation_id)
        )
    )
    facts = facts_result.scalars().all()

    return {
        "document_id": str(document.id),
        "facts": [
            {
                "id": str(f.id),
                "fact_type": f.fact_type,
                "raw_value": f.raw_value,
                "normalized_value": f.normalized_value,
                "confidence": float(f.confidence) if f.confidence is not None else None,
                "source_page": f.source_page,
                "status": f.status,
                "bounding_box": f.bounding_box,
            }
            for f in facts
        ],
    }


@router.get("/{document_id}/review-items")
async def get_document_review_items(
    document_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    document = await _get_document_or_404(session, document_id)
    trace_id = new_trace_id()
    await PermissionService(session).require_read(
        user=current_user,
        patient_id=document.patient_id,
        action="document.review_items.read",
        trace_id=trace_id,
        object_type="document",
        object_id=document.id,
        ip_address=get_request_ip(request),
    )

    reviews_result = await session.execute(
        select(DocumentReviewItem).where(DocumentReviewItem.document_id == document_id)
    )
    reviews = reviews_result.scalars().all()

    return {
        "document_id": str(document.id),
        "review_items": [
            {
                "id": str(r.id),
                "fact_id": str(r.fact_id) if r.fact_id else None,
                "field_name": r.field_name,
                "original_value": r.original_value,
                "suggested_value": r.suggested_value,
                "review_status": r.review_status,
            }
            for r in reviews
        ],
    }


@router.patch("/{document_id}/review-items/{review_item_id}")
async def patch_review_item(
    document_id: uuid.UUID,
    review_item_id: uuid.UUID,
    payload: ReviewItemPatchRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    document = await _get_document_or_404(session, document_id)
    trace_id = new_trace_id()

    # Must have read access at minimum to view/patch
    await PermissionService(session).require_read(
        user=current_user,
        patient_id=document.patient_id,
        action="document.review_item.patch",
        trace_id=trace_id,
        object_type="document",
        object_id=document.id,
        ip_address=get_request_ip(request),
    )

    review_item = await session.get(DocumentReviewItem, review_item_id)
    if not review_item or review_item.document_id != document_id:
        raise NotFoundError("Review item not found")

    fact_type = "general"
    if review_item.fact_id:
        fact = await session.get(ClinicalFact, review_item.fact_id)
        if fact:
            fact_type = fact.fact_type

    # Field-level RBAC check
    role = current_user.role

    if role not in ("admin", "doctor", "hospitalist", "cardiologist", "nurse", "rn", "pharmacist", "lab_staff"):
        raise PermissionDeniedError(f"{role} cannot confirm clinical fields.")

    if fact_type in ("medication", "allergy") and role not in ("doctor", "hospitalist", "cardiologist", "pharmacist"):
        raise PermissionDeniedError(f"{role} cannot confirm {fact_type} fields.")

    if fact_type == "lab" and role not in ("doctor", "hospitalist", "cardiologist", "lab_staff"):
        raise PermissionDeniedError(f"{role} cannot confirm {fact_type} fields.")

    if payload.action == "approve":
        review_item.review_status = "approved"
        if review_item.fact_id:
            fact = await session.get(ClinicalFact, review_item.fact_id)
            if fact:
                fact.status = "confirmed"
    elif payload.action == "reject":
        review_item.review_status = "rejected"
        if review_item.fact_id:
            fact = await session.get(ClinicalFact, review_item.fact_id)
            if fact:
                fact.status = "rejected"
    elif payload.action == "correct":
        review_item.review_status = "approved"
        if payload.value is not None:
            review_item.suggested_value = str(payload.value)
        if review_item.fact_id:
            fact = await session.get(ClinicalFact, review_item.fact_id)
            if fact:
                if payload.value is not None:
                    fact.normalized_value = str(payload.value)
                fact.status = "confirmed"

    review_item.reviewed_by_user_id = current_user.id
    review_item.reviewed_at = datetime.now(UTC)

    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="document.review_item.patch",
        object_type="document_review_item",
        object_id=review_item.id,
        patient_id=document.patient_id,
        outcome="allowed",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
        metadata={"action": payload.action, "reason": payload.reason},
    )

    await session.commit()

    return {"review_item_id": str(review_item_id), "status": review_item.review_status}
