from uuid import UUID

from hospital_ai.schemas.common import ApiSchema


class UserRead(ApiSchema):
    id: UUID
    email: str
    full_name: str
    department: str | None = None
    workspace: str | None = None
    role: str
    is_active: bool


class TokenRequest(ApiSchema):
    email: str
    password: str


class TokenResponse(ApiSchema):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
