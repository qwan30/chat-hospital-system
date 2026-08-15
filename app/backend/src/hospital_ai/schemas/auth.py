from typing import Literal, Optional
from uuid import UUID

from pydantic import ConfigDict

from hospital_ai.schemas.common import ApiSchema


class UserRead(ApiSchema):
    id: UUID
    email: str
    full_name: str
    department: Optional[str] = None
    workspace: Optional[str] = None
    role: str
    is_active: bool


class TokenRequest(ApiSchema):
    email: str
    password: str


class TokenResponse(ApiSchema):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


DemoRole = Literal["cardiologist", "hospitalist", "rn", "pharmacist", "front_desk", "admin", "security"]


class DemoLoginRequest(ApiSchema):
    role: DemoRole

    model_config = ConfigDict(extra="forbid")


class DemoStatusResponse(ApiSchema):
    enabled: bool
