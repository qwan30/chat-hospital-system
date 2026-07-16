from datetime import date
from uuid import UUID

from hospital_ai.schemas.common import ApiSchema


class SearchPatient(ApiSchema):
    id: UUID
    full_name: str
    mrn: str
    dob: date | None = None
    department: str | None = None
    status: str


class SearchDocument(ApiSchema):
    id: UUID
    title: str
    document_type: str
    patient_id: UUID


class SearchThread(ApiSchema):
    id: UUID
    title: str | None = None
    patient_id: UUID


class GlobalSearchResponse(ApiSchema):
    patients: list[SearchPatient]
    documents: list[SearchDocument]
    threads: list[SearchThread]
