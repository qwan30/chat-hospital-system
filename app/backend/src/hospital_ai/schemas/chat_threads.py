from datetime import datetime
from typing import Dict, List, Literal, Optional
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
    scope: ThreadScope = "general"
    patient_id: Optional[UUID] = None

    @root_validator
    def validate_patient_scope(cls, values: Dict[str, object]) -> Dict[str, object]:
        scope = values.get("scope")
        patient_id = values.get("patient_id")

        if scope == "patient-linked" and patient_id is None:
            raise ValueError("patient-linked chat requires patient_id")
        if scope == "general" and patient_id is not None:
            raise ValueError("general chat threads must not include patient_id")

        return values


class ChatThreadCreate(PatientScopeMixin):
    title: str = Field(min_length=1, max_length=255)
    visibility: ThreadVisibility = "private"


class ChatThreadUpdate(ApiSchema):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    visibility: Optional[ThreadVisibility] = None
    status: Optional[ThreadStatus] = None


class ChatThreadRead(PatientScopeMixin):
    id: UUID
    title: str
    visibility: ThreadVisibility
    status: ThreadStatus
    owner_user_id: UUID
    created_trace_id: str
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ChatThreadParticipantCreate(ApiSchema):
    user_id: UUID
    access_level: ParticipantAccessLevel = "read"
    can_share: bool = False


class ChatThreadParticipantRead(ApiSchema):
    id: UUID
    thread_id: UUID
    user_id: UUID
    access_level: ParticipantAccessLevel
    can_share: bool
    added_by_user_id: UUID
    created_trace_id: str
    last_read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ChatMessageCreate(PatientScopeMixin):
    role: MessageRole = "user"
    content: str = Field(min_length=1)
    patient_permission_state: PatientPermissionState = "not-required"
    citations: List[EvidenceRead] = Field(default_factory=list)
    metadata: Dict[str, object] = Field(default_factory=dict, alias="meta")


class ChatMessageRead(ChatMessageCreate):
    id: UUID
    thread_id: UUID
    sender_user_id: Optional[UUID] = None
    ai_query_id: Optional[UUID] = None
    trace_id: str
    created_at: datetime


class ChatThreadDetail(ChatThreadRead):
    participants: List[ChatThreadParticipantRead] = Field(default_factory=list)
    messages: List[ChatMessageRead] = Field(default_factory=list)


class ChatThreadListResponse(ApiSchema):
    items: List[ChatThreadRead]


class ChatThreadMessageRequest(ApiSchema):
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class ChatThreadMessageResponse(ApiSchema):
    user_message: ChatMessageRead
    assistant_message: ChatMessageRead


class ChatThreadMessageListResponse(ApiSchema):
    items: List[ChatMessageRead]
