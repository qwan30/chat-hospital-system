from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_session
from hospital_ai.db.models import User
from hospital_ai.schemas.document_uploads import UploadFinalizeResult, UploadSessionCreate, UploadSessionRead
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
    return await UploadSessionService.from_request(session, request).create(
        actor=current_user, payload=payload, idempotency_key=idempotency_key
    )

@router.post("/{document_id}/uploads/{upload_id}/finalize", response_model=UploadFinalizeResult, status_code=200)
async def finalize_upload_session(
    document_id: uuid.UUID,
    upload_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UploadFinalizeResult:
    return await UploadSessionService.from_request(session, request).finalize(
        document_id=document_id, upload_id=upload_id, actor=current_user
    )
