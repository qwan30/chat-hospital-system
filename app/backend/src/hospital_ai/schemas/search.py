"""Schemas cho Tìm kiếm toàn cục (Global Search API).

Định nghĩa cấu trúc kết quả tìm kiếm đa đối tượng (bệnh nhân, tài liệu, cuộc hội thoại).
"""

from datetime import date
from uuid import UUID

from hospital_ai.schemas.common import ApiSchema


class SearchPatient(ApiSchema):
    """Schema kết quả tìm kiếm thông tin tóm tắt của bệnh nhân theo tên hoặc MRN."""
    id: UUID
    full_name: str
    mrn: str
    dob: date | None = None
    department: str | None = None
    status: str


class SearchDocument(ApiSchema):
    """Schema kết quả tìm kiếm tài liệu y tế khớp với từ khóa tìm kiếm."""
    id: UUID
    title: str
    document_type: str
    patient_id: UUID


class SearchThread(ApiSchema):
    """Schema kết quả tìm kiếm cuộc hội thoại đã diễn ra."""
    id: UUID
    title: str | None = None
    patient_id: UUID


class GlobalSearchResponse(ApiSchema):
    """Schema phản hồi tổng hợp của tính năng tìm kiếm toàn cục (Global Search)."""
    patients: list[SearchPatient]
    documents: list[SearchDocument]
    threads: list[SearchThread]

