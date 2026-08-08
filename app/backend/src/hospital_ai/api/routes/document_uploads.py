import json
import uuid

from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.errors import ConflictError, NotFoundError, ValidationAppError
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.clinical_documents import DocumentUpload
from hospital_ai.db.models import Document, User
from hospital_ai.schemas.document_uploads import UploadFinalizeResult, UploadSessionCreate, UploadSessionRead
from hospital_ai.services.audit import AuditService
from hospital_ai.services.idempotency import IdempotencyService
from hospital_ai.services.permissions import PermissionService
from hospital_ai.services.storage import LocalStorageService, validate_storage_object_key
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


@router.put("/upload-objects/{object_key:path}", status_code=204)
async def put_local_upload_object(
    object_key: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> Response:
    """Accept local direct-upload bytes for development and CI only.

    R2 sessions return a real presigned URL. The local adapter returns a
    ``local://`` marker instead, which the frontend maps to this authenticated
    endpoint so browser E2E can exercise the same create/PUT/finalize flow.
    """
    if settings.storage_backend.strip().lower() != "local":
        raise NotFoundError("Local upload endpoint is unavailable for this storage backend.")

    try:
        validated_key = validate_storage_object_key(object_key, allowed_prefixes=("source/",))
        parts = validated_key.split("/")
        if len(parts) != 5 or parts[0] != "source":
            raise ValueError("Unexpected upload object key shape.")
        patient_id = uuid.UUID(parts[1])
        document_id = uuid.UUID(parts[2])
        upload_id = uuid.UUID(parts[3])
    except (ValueError, TypeError) as exc:
        raise ValidationAppError("Invalid upload object key.") from exc

    document = await session.get(Document, document_id)
    upload = await session.get(DocumentUpload, upload_id)
    if (
        document is None
        or upload is None
        or upload.document_id != document.id
        or document.patient_id != patient_id
        or upload.object_key != validated_key
    ):
        raise NotFoundError("Upload session not found.")

    await PermissionService(session).require_upload_or_admin_role(
        user=current_user,
        patient_id=patient_id,
        action="document.upload_session.put",
        trace_id=new_trace_id(),
        object_type="document",
        object_id=document.id,
        ip_address=get_request_ip(request),
    )

    if request.headers.get("if-none-match") != "*":
        raise ValidationAppError("Immutable upload requires If-None-Match: *.")
    if request.headers.get("content-type", "").split(";", 1)[0].strip() != upload.mime_type:
        raise ValidationAppError("Upload Content-Type does not match the upload session.")

    content = await request.body()
    if upload.byte_size is None or len(content) != upload.byte_size:
        raise ValidationAppError("Upload size does not match the upload session.")

    try:
        LocalStorageService(settings).put_object(key=validated_key, content=content)
    except FileExistsError as exc:
        raise ConflictError("Object key already exists in storage.") from exc

    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="document.upload_session.put",
        object_type="document",
        object_id=document.id,
        patient_id=patient_id,
        outcome="allowed",
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
        metadata={"byte_size": len(content)},
    )
    await session.commit()
    return Response(status_code=204)


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
        "document.upload_session.finalize",
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
