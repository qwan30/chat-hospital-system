"""Schemas cho Đồng bộ hệ thống thông tin bệnh viện (HMS Synchronization & Import APIs).

Định nghĩa cấu trúc dữ liệu nhập tóm tắt lịch hẹn khám và phản hồi tạo tài liệu từ HMS.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import Field, root_validator

from hospital_ai.schemas.common import ApiSchema


class HmsAppointmentSummaryImport(ApiSchema):
    """Schema yêu cầu đồng bộ nhập thông tin tóm tắt lịch hẹn khám bệnh từ hệ thống HMS."""
    source_appointment_id: UUID
    patient_id: UUID
    source_patient_id: UUID
    appointment_date: date
    status: str = Field(min_length=1, max_length=64)
    department: str | None = Field(default=None, max_length=128)
    doctor_name: str | None = Field(default=None, max_length=255)
    start_time: str | None = Field(default=None, max_length=32)
    end_time: str | None = Field(default=None, max_length=32)
    reason: str | None = Field(default=None, max_length=500)
    symptoms: str | None = None
    notes: str | None = None
    vital_signs_summary: str | None = None
    follow_up_summary: str | None = None
    source_updated_at: datetime | None = None
    metadata: dict[str, object] = Field(default_factory=dict)

    @root_validator
    def validate_patient_ownership(cls, values: dict[str, object]) -> dict[str, object]:
        """Kiểm tra tính nhất quán giữa ID bệnh nhân nội bộ và ID bệnh nhân từ HMS."""
        if values.get("patient_id") != values.get("source_patient_id"):
            raise ValueError("source_patient_id must match patient_id for HMS appointment import")
        return values


class HmsAppointmentImportResponse(ApiSchema):
    """Schema phản hồi kết quả đồng bộ lịch hẹn HMS thành tài liệu trong hệ thống AI."""
    document_id: UUID
    patient_id: UUID
    source_appointment_id: UUID
    document_title: str
    source_family: str
    source_system: str
    status: str

