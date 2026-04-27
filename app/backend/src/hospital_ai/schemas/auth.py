from typing import Optional
from uuid import UUID

from hospital_ai.schemas.common import ApiSchema


class UserRead(ApiSchema):
    id: UUID
    email: str
    full_name: str
    department: Optional[str] = None
    role: str
    is_active: bool
