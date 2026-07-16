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
    document_id: UUID
    document_title: str
    page: int
    chunk_id: UUID
    score: float
    content: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentSearchResponse(BaseModel):
    items: list[EvidenceRead]


class DocumentListResponse(ApiSchema):
    items: list[DocumentRead]
