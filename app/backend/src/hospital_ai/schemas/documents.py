"""Schemas cho Quản lý & Tìm kiếm Tài liệu y tế (Document Management & Vector Search APIs).

Định nghĩa cấu trúc tải lên, chi tiết trang tài liệu, trích xuất bằng chứng RAG và danh sách tài liệu.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from hospital_ai.schemas.common import ApiSchema


class DocumentRead(ApiSchema):
    """Schema biểu diễn thông tin chi tiết một tài liệu y tế đã tải lên của bệnh nhân."""
    id: UUID
    patient_id: UUID
    uploaded_by: UUID
    title: str
    document_type: str
    storage_uri: str
    mime_type: str
    status: str
    page_count: int | None = None
    ocr_error: str | None = None
    created_at: datetime


class DocumentPageRead(ApiSchema):
    """Schema biểu diễn nội dung văn bản bóc tách bằng OCR của một trang tài liệu."""
    id: UUID
    document_id: UUID
    page_number: int
    ocr_text: str
    ocr_confidence: float | None = None


class DocumentSearchRequest(BaseModel):
    """Schema yêu cầu tìm kiếm ngữ nghĩa RAG trên tài liệu của một bệnh nhân."""
    patient_id: UUID
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class EvidenceRead(BaseModel):
    """Schema biểu diễn một đoạn bằng chứng (Chunk evidence) tìm thấy phù hợp với câu hỏi RAG."""
    evidence_id: str
    document_id: UUID
    document_title: str
    page: int
    chunk_id: UUID
    score: float
    content: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentSearchResponse(BaseModel):
    """Schema phản hồi danh sách các bằng chứng tìm được từ tài liệu y tế."""
    items: list[EvidenceRead]


class DocumentListResponse(ApiSchema):
    """Schema danh sách các tài liệu y tế của bệnh nhân."""
    items: list[DocumentRead]

