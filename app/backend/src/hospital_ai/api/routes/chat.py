from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.api.limiter import limiter
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.models import User
from hospital_ai.schemas.chat import ChatRequest, ChatResponse
from hospital_ai.services.chat import ChatService

router = APIRouter()


@router.post("", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat(
    payload: ChatRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    return await ChatService(session, settings).answer(
        user=current_user,
        patient_id=payload.patient_id or (payload.context.patient_id if payload.context else None),
        question=payload.question,
        top_k=payload.top_k,
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
        thread_id=payload.thread_id,
        pipeline=payload.pipeline,
    )
