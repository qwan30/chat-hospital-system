from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from hospital_ai.schemas.common import ApiSchema


class DocumentRead(ApiSchema):
    id: UUID
    patient_id: UUID
    uploaded_by: UUID
    title: str
    document_type: str
    storage_uri: str
    mime_type: str
    status: str
    page_count: Optional[int] = None
    ocr_error: Optional[str] = None
    created_at: datetime


class DocumentProcessingEventRead(ApiSchema):
    id: UUID
    attempt: int
    sequence: int
    stage: str
    state: str
    progress_current: Optional[int] = None
    progress_total: Optional[int] = None
    error_code: Optional[str] = None
    created_at: datetime


class DocumentDetailRead(DocumentRead):
    processing_events: list[DocumentProcessingEventRead] = Field(default_factory=list)


class DocumentPageRead(ApiSchema):
    id: UUID
    document_id: UUID
    page_number: int
    ocr_text: str
    ocr_confidence: Optional[float] = None


class DocumentSearchRequest(BaseModel):
    patient_id: UUID
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class EvidenceRead(BaseModel):
    evidence_id: str
    document_id: Optional[UUID] = None
    document_title: str
    page: int
    chunk_id: Optional[UUID] = None
    score: float
    content: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    generation_id: Optional[UUID] = None
    revision_set_id: Optional[UUID] = None
    page_revision_id: Optional[UUID] = None
    approval_state: Optional[str] = None
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    bounding_boxes: Optional[list[Any]] = None


class DocumentSearchResponse(BaseModel):
    items: list[EvidenceRead]


class DocumentListResponse(ApiSchema):
    items: list[DocumentRead]
