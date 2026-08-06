import json
import uuid

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.core.errors import ConflictError, NotFoundError
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.clinical_documents import DocumentUpload
from hospital_ai.db.models import Document, User
from hospital_ai.schemas.document_uploads import UploadFinalizeResult, UploadSessionCreate, UploadSessionRead
from hospital_ai.services.audit import AuditService
from hospital_ai.services.idempotency import IdempotencyService
from hospital_ai.services.permissions import PermissionService
from hospital_ai.services.upload_sessions import UploadSessionService

router = APIRouter()


@router.post("/upload-sessions", response_model=UploadSessionRead, status_code=201)
async def create_upload_session(
    payload: UploadSessionCreate,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UploadSessionRead:
    await PermissionService(session).require_upload_or_admin_role(
        user=current_user,
        patient_id=payload.patient_id,
        action="document.upload_session.create",
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
    )
    result = await UploadSessionService.from_request(session, request).create(
        actor=current_user, payload=payload, idempotency_key=idempotency_key
    )
    await session.commit()
    return result


@router.post("/{document_id}/uploads/{upload_id}/finalize", response_model=UploadFinalizeResult, status_code=200)
async def finalize_upload_session(
    document_id: uuid.UUID,
    upload_id: uuid.UUID,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UploadFinalizeResult:
    document = await session.get(Document, document_id)
    upload = await session.get(DocumentUpload, upload_id)
    if document is None or upload is None or upload.document_id != document.id:
        if current_user:
            await AuditService(session).record(
                actor_user_id=current_user.id,
                action="document.upload_session.finalize",
                object_type="document",
                object_id=document_id,
                patient_id=document.patient_id if document else None,
                outcome="denied",
                trace_id=new_trace_id(),
                ip_address=get_request_ip(request),
                metadata={"reason": "upload_document_mismatch" if (document and upload) else "not_found"},
            )
            await session.commit()
        raise NotFoundError("Document or upload session not found.")
    await PermissionService(session).require_upload_or_admin_role(
        user=current_user,
        patient_id=document.patient_id,
        action="document.upload_session.finalize",
        trace_id=new_trace_id(),
        object_type="document",
        object_id=document.id,
        ip_address=get_request_ip(request),
    )
    idemp = IdempotencyService(session, current_user.id)
    decision = await idemp.begin(
        f"upload.finalize.{document_id}:{upload_id}",
        idempotency_key,
        {"document_id": str(document_id), "upload_id": str(upload_id)},
    )
    if decision.is_in_progress:
        raise ConflictError("Request is already in progress; retry later.")
    if decision.is_replay:
        return UploadFinalizeResult(**decision.response_body)

    try:
        result = await UploadSessionService.from_request(session, request).finalize(
            document_id=document_id, upload_id=upload_id, actor=current_user, commit=False
        )
        if result.state == "finalized":
            from hospital_ai.core.config import get_settings
            from hospital_ai.workers.queue import enqueue_document_indexing
            enqueue_document_indexing(document.id, get_settings())
    except Exception:
        await idemp.abort(decision.record_id)
        raise
    await idemp.complete(
        decision.record_id,
        200,
        json.loads(result.model_dump_json() if hasattr(result, "model_dump_json") else result.json()),
    )
    await session.commit()
    return result
