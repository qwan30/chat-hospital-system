import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.models import User
from hospital_ai.schemas.chat_threads import (
    ChatThreadCreate,
    ChatThreadDetail,
    ChatThreadListResponse,
    ChatThreadMessageListResponse,
    ChatThreadMessageRequest,
    ChatThreadMessageResponse,
    ChatThreadRead,
    ChatThreadUpdate,
)
from hospital_ai.services.chat_threads import ChatThreadService

router = APIRouter()


@router.post("", response_model=ChatThreadRead, response_model_by_alias=False)
async def create_thread(
    payload: ChatThreadCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ChatThreadRead:
    return await ChatThreadService(session).create_thread(
        user=current_user,
        payload=payload,
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
    )


@router.get("", response_model=ChatThreadListResponse, response_model_by_alias=False)
async def list_threads(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ChatThreadListResponse:
    threads = await ChatThreadService(session).list_threads(user=current_user)
    return ChatThreadListResponse(items=threads)


@router.post(
    "/{thread_id}/messages",
    response_model=ChatThreadMessageResponse,
    response_model_by_alias=False,
)
async def ask_thread_message(
    thread_id: uuid.UUID,
    payload: ChatThreadMessageRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> ChatThreadMessageResponse:
    user_message, assistant_message = await ChatThreadService(session).ask_thread_message(
        user=current_user,
        thread_id=thread_id,
        payload=payload,
        settings=settings,
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
    )
    return ChatThreadMessageResponse(user_message=user_message, assistant_message=assistant_message)


@router.get(
    "/{thread_id}/messages",
    response_model=ChatThreadMessageListResponse,
    response_model_by_alias=False,
)
async def list_thread_messages(
    thread_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ChatThreadMessageListResponse:
    messages = await ChatThreadService(session).list_messages(
        user=current_user,
        thread_id=thread_id,
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
    )
    return ChatThreadMessageListResponse(items=messages)


@router.get("/{thread_id}", response_model=ChatThreadDetail, response_model_by_alias=False)
async def get_thread(
    thread_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ChatThreadDetail:
    return await ChatThreadService(session).get_thread(
        user=current_user,
        thread_id=thread_id,
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
    )


@router.patch("/{thread_id}", response_model=ChatThreadRead, response_model_by_alias=False)
async def update_thread(
    thread_id: uuid.UUID,
    payload: ChatThreadUpdate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ChatThreadRead:
    return await ChatThreadService(session).update_thread(
        user=current_user,
        thread_id=thread_id,
        payload=payload,
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
    )


@router.delete("/{thread_id}", response_model=ChatThreadRead, response_model_by_alias=False)
async def archive_thread(
    thread_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ChatThreadRead:
    return await ChatThreadService(session).archive_thread(
        user=current_user,
        thread_id=thread_id,
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
    )
