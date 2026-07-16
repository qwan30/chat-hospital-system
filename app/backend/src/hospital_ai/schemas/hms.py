from datetime import date, datetime
from uuid import UUID

from pydantic import Field, root_validator

from hospital_ai.schemas.common import ApiSchema


class HmsAppointmentSummaryImport(ApiSchema):
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
        if values.get("patient_id") != values.get("source_patient_id"):
            raise ValueError("source_patient_id must match patient_id for HMS appointment import")
        return values


class HmsAppointmentImportResponse(ApiSchema):
    document_id: UUID
    patient_id: UUID
    source_appointment_id: UUID
    document_title: str
    source_family: str
    source_system: str
    status: str
