"""Schemas cho Xác thực và Người dùng (Authentication & User DTOs).

Định nghĩa cấu trúc yêu cầu đăng nhập, phản hồi token và thông tin người dùng.
"""

from uuid import UUID

from hospital_ai.schemas.common import ApiSchema


class UserRead(ApiSchema):
    """Schema biểu diễn thông tin người dùng trả về từ API (không chứa thông tin nhạy cảm như mật khẩu)."""
    id: UUID
    email: str
    full_name: str
    department: str | None = None
    workspace: str | None = None
    role: str
    is_active: bool


class TokenRequest(ApiSchema):
    """Schema yêu cầu cấp JWT Access Token khi đăng nhập."""
    email: str
    password: str


class TokenResponse(ApiSchema):
    """Schema phản hồi sau khi xác thực thành công, chứa access token và thông tin user."""
    access_token: str
    token_type: str = "bearer"
    user: UserRead

