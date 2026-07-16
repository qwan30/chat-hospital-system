"""Schemas cho Nhật ký kiểm toán (Audit Log APIs).

Định nghĩa cấu trúc dữ liệu trả về khi truy vấn danh sách hoặc chi tiết log kiểm toán.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from hospital_ai.schemas.common import ApiSchema


class AuditLogRead(ApiSchema):
    """Schema biểu diễn thông tin chi tiết của một bản ghi nhật ký kiểm toán."""
    id: UUID
    actor_user_id: UUID | None = None
    action: str
    object_type: str
    object_id: UUID | None = None
    patient_id: UUID | None = None
    outcome: str
    trace_id: str
    ip_address: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict, alias="meta")
    created_at: datetime


class AuditLogList(ApiSchema):
    """Schema danh sách các bản ghi nhật ký kiểm toán trả về cho client."""
    items: list[AuditLogRead]

