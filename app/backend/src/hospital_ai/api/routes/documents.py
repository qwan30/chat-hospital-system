import uuid

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.errors import NotFoundError, ValidationAppError
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.models import Document, DocumentPage, User
from hospital_ai.schemas.documents import (
    DocumentPageRead,
    DocumentRead,
    DocumentSearchRequest,
    DocumentSearchResponse,
    EvidenceRead,
)
from hospital_ai.services.audit import AuditService
from hospital_ai.services.embeddings import EmbeddingService
from hospital_ai.services.permissions import PermissionService
from hospital_ai.services.retrieval import RetrievalService
from hospital_ai.services.storage import LocalStorageService
from hospital_ai.workers.jobs import process_document
from hospital_ai.workers.queue import enqueue_document_indexing

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "application/json",
    "application/pdf",
    "image/png",
    "image/jpeg",
}


@router.post("", response_model=DocumentRead)
async def upload_document(
    request: Request,
    patient_id: uuid.UUID = Form(...),
    title: str = Form(...),
    document_type: str = Form(...),
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

    mime_type = file.content_type or "application/octet-stream"
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
    document.storage_uri = await LocalStorageService(settings).save_upload(
        patient_id=patient_id,
        document_id=document.id,
        file=file,
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
        metadata={"title": title, "document_type": document_type},
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


@router.get("/{document_id}", response_model=DocumentRead)
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
    return document


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
