from datetime import date, datetime
from typing import Optional
from uuid import UUID

from hospital_ai.schemas.common import ApiSchema


class PatientRead(ApiSchema):
    id: UUID
    mrn: str
    full_name: str
    dob: Optional[date] = None
    department: Optional[str] = None
    status: str


class PatientSearchResponse(ApiSchema):
    items: list[PatientRead]


class PatientOverviewResponse(ApiSchema):
    patient_id: UUID
    full_name: str
    mrn: str
    dob: Optional[date] = None
    gender: Optional[str] = None
    cccd: Optional[str] = None
    blood_type: Optional[str] = None
    occupation: Optional[str] = None

    allergy_count: int
    medication_count: int
    lab_count: int
    appointment_count: int

    ai_summary: Optional[str] = None
    last_updated: Optional[datetime] = None


class PatientTimelineEvent(ApiSchema):
    event_id: UUID
    event_type: str
    title: str
    description: Optional[str] = None
    timestamp: datetime


class PatientTimelineResponse(ApiSchema):
    patient_id: UUID
    events: list[PatientTimelineEvent]


class PatientMedicationItem(ApiSchema):
    drug_name: str
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    started: Optional[str] = None
    prescriber: Optional[str] = None
    source_document_id: Optional[UUID] = None
    source_document_title: Optional[str] = None


class PatientMedicationResponse(ApiSchema):
    patient_id: UUID
    medications: list[PatientMedicationItem]


class PatientLabItem(ApiSchema):
    analyte: str
    value: Optional[str] = None
    reference_range: Optional[str] = None
    flag: Optional[str] = None  # H, L, or normal
    collected: Optional[str] = None
    source_document_id: Optional[UUID] = None
    source_document_title: Optional[str] = None


class PatientLabResponse(ApiSchema):
    patient_id: UUID
    labs: list[PatientLabItem]
