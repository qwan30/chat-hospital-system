from datetime import date
from typing import List, Optional
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
    items: List[PatientRead]
