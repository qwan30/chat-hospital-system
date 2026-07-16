"""Schemas cho Quản lý các Luồng/Cuộc trò chuyện (Chat Threads APIs & DTOs).

Định nghĩa cấu trúc tạo/sửa đổi thread, phân quyền thành viên tham gia (hội chẩn) và gửi tin nhắn trong thread.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, root_validator

from hospital_ai.schemas.common import ApiSchema
from hospital_ai.schemas.documents import EvidenceRead

ThreadScope = Literal["general", "patient-linked"]
ThreadVisibility = Literal["private", "shared"]
ThreadStatus = Literal["active", "archived"]
ParticipantAccessLevel = Literal["owner", "write", "read"]
MessageRole = Literal["user", "assistant", "system"]
PatientPermissionState = Literal["not-required", "pending", "allowed", "denied"]


class PatientScopeMixin(ApiSchema):
    """Lớp mixin kiểm tra tính hợp lệ của phạm vi cuộc trò chuyện (`general` hoặc `patient-linked`)."""
    scope: ThreadScope = "general"
    patient_id: UUID | None = None

    @root_validator
    def validate_patient_scope(cls, values: dict[str, object]) -> dict[str, object]:
        """Đảm bảo thread `patient-linked` phải có `patient_id` và ngược lại `general` không được có."""
        scope = values.get("scope")
        patient_id = values.get("patient_id")

        if scope == "patient-linked" and patient_id is None:
            raise ValueError("patient-linked chat requires patient_id")
        if scope == "general" and patient_id is not None:
            raise ValueError("general chat threads must not include patient_id")

        return values


class ChatThreadCreate(PatientScopeMixin):
    """Schema yêu cầu tạo mới một cuộc trò chuyện."""
    title: str = Field(min_length=1, max_length=255)
    visibility: ThreadVisibility = "private"


class ChatThreadUpdate(ApiSchema):
    """Schema yêu cầu cập nhật tiêu đề, quyền riêng tư hoặc trạng thái của thread."""
    title: str | None = Field(default=None, min_length=1, max_length=255)
    visibility: ThreadVisibility | None = None
    status: ThreadStatus | None = None


class ChatThreadRead(PatientScopeMixin):
    """Schema thông tin cơ bản của một cuộc trò chuyện trả về từ API."""
    id: UUID
    title: str
    visibility: ThreadVisibility
    status: ThreadStatus
    owner_user_id: UUID
    created_trace_id: str
    last_message_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ChatThreadParticipantCreate(ApiSchema):
    """Schema yêu cầu thêm một bác sĩ/nhân viên y tế vào thread (chia sẻ hội chẩn)."""
    user_id: UUID
    access_level: ParticipantAccessLevel = "read"
    can_share: bool = False


class ChatThreadParticipantUpdate(ApiSchema):
    """Schema yêu cầu cập nhật quyền hạn của một thành viên trong thread."""
    access_level: ParticipantAccessLevel | None = None
    can_share: bool | None = None


class ChatThreadParticipantRead(ApiSchema):
    """Schema thông tin chi tiết một thành viên tham gia trong thread."""
    id: UUID
    thread_id: UUID
    user_id: UUID
    access_level: ParticipantAccessLevel
    can_share: bool
    added_by_user_id: UUID
    created_trace_id: str
    last_read_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ChatMessageCreate(PatientScopeMixin):
    """Schema yêu cầu tạo mới một tin nhắn trong thread."""
    role: MessageRole = "user"
    content: str = Field(min_length=1)
    patient_permission_state: PatientPermissionState = "not-required"
    citations: list[EvidenceRead] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict, alias="meta")


class ChatMessageRead(ChatMessageCreate):
    """Schema thông tin chi tiết của một tin nhắn hội thoại trả về từ API."""
    id: UUID
    thread_id: UUID
    sender_user_id: UUID | None = None
    ai_query_id: UUID | None = None
    trace_id: str
    created_at: datetime


class ChatThreadDetail(ChatThreadRead):
    """Schema thông tin đầy đủ của một cuộc trò chuyện bao gồm danh sách thành viên và các tin nhắn."""
    participants: list[ChatThreadParticipantRead] = Field(default_factory=list)
    messages: list[ChatMessageRead] = Field(default_factory=list)


class ChatThreadListResponse(ApiSchema):
    """Schema danh sách các cuộc trò chuyện."""
    items: list[ChatThreadRead]


class ChatThreadParticipantListResponse(ApiSchema):
    """Schema danh sách các thành viên tham gia cuộc trò chuyện."""
    items: list[ChatThreadParticipantRead]


class ChatThreadMessageRequest(ApiSchema):
    """Schema gửi câu hỏi trong một cuộc trò chuyện cụ thể."""
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class ChatThreadMessageResponse(ApiSchema):
    """Schema phản hồi cặp tin nhắn vừa tạo (câu hỏi của user và câu trả lời của AI)."""
    user_message: ChatMessageRead
    assistant_message: ChatMessageRead


class ChatThreadMessageListResponse(ApiSchema):
    """Schema danh sách lịch sử tin nhắn của một cuộc trò chuyện."""
    items: list[ChatMessageRead]
