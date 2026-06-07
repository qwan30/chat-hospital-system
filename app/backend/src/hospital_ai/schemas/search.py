from datetime import date
from typing import List, Optional
from uuid import UUID
from hospital_ai.schemas.common import ApiSchema


class SearchPatient(ApiSchema):
    id: UUID
    full_name: str
    mrn: str
    dob: Optional[date] = None
    department: Optional[str] = None
    status: str


class SearchDocument(ApiSchema):
    id: UUID
    title: str
    document_type: str
    patient_id: UUID


class SearchThread(ApiSchema):
    id: UUID
    title: Optional[str] = None
    patient_id: UUID


class GlobalSearchResponse(ApiSchema):
    patients: List[SearchPatient]
    documents: List[SearchDocument]
    threads: List[SearchThread]
