"""Schemas cho Quản lý hồ sơ Bệnh nhân (Patient Management APIs).

Định nghĩa cấu trúc dữ liệu tổng quan bệnh nhân, tìm kiếm và dòng sự kiện y tế (Timeline).
"""

from datetime import date, datetime
from uuid import UUID

from hospital_ai.schemas.common import ApiSchema


class PatientRead(ApiSchema):
    """Schema cơ bản biểu diễn thông tin bệnh nhân (Mã MRN, họ tên, ngày sinh, khoa phòng)."""
    id: UUID
    mrn: str
    full_name: str
    dob: date | None = None
    department: str | None = None
    status: str


class PatientSearchResponse(ApiSchema):
    """Schema danh sách bệnh nhân trả về khi tìm kiếm."""
    items: list[PatientRead]


class PatientOverviewResponse(ApiSchema):
    """Schema tổng quan chi tiết của bệnh nhân (thông tin hành chính, số lượng chỉ số và tóm tắt AI)."""
    patient_id: UUID
    full_name: str
    mrn: str
    dob: date | None = None
    gender: str | None = None
    cccd: str | None = None
    blood_type: str | None = None
    occupation: str | None = None

    allergy_count: int
    medication_count: int
    lab_count: int
    appointment_count: int

    ai_summary: str | None = None
    last_updated: datetime | None = None


class PatientTimelineEvent(ApiSchema):
    """Schema biểu diễn một sự kiện trong dòng thời gian y tế của bệnh nhân (lần khám, xét nghiệm, đơn thuốc...)."""
    event_id: UUID
    event_type: str
    title: str
    description: str | None = None
    timestamp: datetime


class PatientTimelineResponse(ApiSchema):
    """Schema danh sách các sự kiện theo thời gian của một bệnh nhân."""
    patient_id: UUID
    events: list[PatientTimelineEvent]

