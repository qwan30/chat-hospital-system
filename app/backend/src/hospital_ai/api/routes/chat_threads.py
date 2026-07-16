"""Chat threads management API routes.
Các endpoint API quản lý các luồng hội thoại y tế (thêm/sửa/xóa thread, tin nhắn và người tham gia).
"""

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
    ChatThreadParticipantCreate,
    ChatThreadParticipantListResponse,
    ChatThreadParticipantRead,
    ChatThreadParticipantUpdate,
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
    """Create a new clinical chat thread.
    Tạo mới một luồng trò chuyện hỏi đáp y khoa lâm sàng.
    """
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
    """List all accessible chat threads for the current user.
    Liệt kê tất cả các luồng trò chuyện mà người dùng hiện tại có quyền truy cập.
    """
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
    """Post a new clinical query message to a specific thread and generate an AI response.
    Gửi câu hỏi mới vào luồng hội thoại và tạo câu trả lời của AI dựa trên ngữ cảnh luồng.
    """
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
    """List chronological messages within a specific chat thread.
    Lấy danh sách toàn bộ các tin nhắn trong luồng trò chuyện theo thứ tự thời gian.
    """
    messages = await ChatThreadService(session).list_messages(
        user=current_user,
        thread_id=thread_id,
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
    )
    return ChatThreadMessageListResponse(items=messages)


@router.get(
    "/{thread_id}/participants",
    response_model=ChatThreadParticipantListResponse,
    response_model_by_alias=False,
)
async def list_thread_participants(
    thread_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ChatThreadParticipantListResponse:
    """List all users participating in a chat thread.
    Liệt kê danh sách tất cả các thành viên tham gia trong luồng trò chuyện.
    """
    participants = await ChatThreadService(session).list_participants(
        user=current_user,
        thread_id=thread_id,
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
    )
    return ChatThreadParticipantListResponse(items=participants)


@router.post(
    "/{thread_id}/participants",
    response_model=ChatThreadParticipantRead,
    response_model_by_alias=False,
)
async def add_thread_participant(
    thread_id: uuid.UUID,
    payload: ChatThreadParticipantCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ChatThreadParticipantRead:
    """Add a new participant (e.g., doctor, nurse) to the chat thread.
    Thêm một thành viên mới (bác sĩ, điều dưỡng) vào luồng trò chuyện.
    """
    return await ChatThreadService(session).add_participant(
        user=current_user,
        thread_id=thread_id,
        payload=payload,
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
    )


@router.patch(
    "/{thread_id}/participants/{participant_id}",
    response_model=ChatThreadParticipantRead,
    response_model_by_alias=False,
)
async def update_thread_participant(
    thread_id: uuid.UUID,
    participant_id: uuid.UUID,
    payload: ChatThreadParticipantUpdate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ChatThreadParticipantRead:
    """Update participant role or permissions inside the thread.
    Cập nhật vai trò hoặc quyền hạn của thành viên trong luồng hội thoại.
    """
    return await ChatThreadService(session).update_participant(
        user=current_user,
        thread_id=thread_id,
        participant_id=participant_id,
        payload=payload,
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
    )


@router.delete(
    "/{thread_id}/participants/{participant_id}",
    response_model=ChatThreadParticipantRead,
    response_model_by_alias=False,
)
async def remove_thread_participant(
    thread_id: uuid.UUID,
    participant_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ChatThreadParticipantRead:
    """Remove a participant from the chat thread.
    Xóa một thành viên khỏi luồng hội thoại.
    """
    return await ChatThreadService(session).remove_participant(
        user=current_user,
        thread_id=thread_id,
        participant_id=participant_id,
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
    )


@router.get("/{thread_id}", response_model=ChatThreadDetail, response_model_by_alias=False)
async def get_thread(
    thread_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ChatThreadDetail:
    """Retrieve detailed metadata and status of a specific thread.
    Lấy thông tin chi tiết và trạng thái của một luồng trò chuyện cụ thể.
    """
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
    """Update title or metadata of a chat thread.
    Cập nhật tiêu đề hoặc thông tin metadata của luồng trò chuyện.
    """
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
    """Archive (soft-delete or close) a chat thread.
    Lưu trữ (xóa mềm hoặc đóng) một luồng trò chuyện.
    """
    return await ChatThreadService(session).archive_thread(
        user=current_user,
        thread_id=thread_id,
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
    )
