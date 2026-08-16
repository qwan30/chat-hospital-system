from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import Field, validator

from hospital_ai.schemas.common import ApiSchema


class AuditLogRead(ApiSchema):
    id: UUID
    actor_user_id: Optional[UUID] = None
    action: str
    object_type: str
    object_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None
    outcome: str
    trace_id: str
    ip_address: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict, alias="meta")
    created_at: datetime

    @validator("metadata", pre=True, always=True)
    def redact_sensitive_keys(cls, v: Any) -> Any:
        if not isinstance(v, dict):
            return v
        sensitive_keys = {"access_token", "password", "raw_prompt_phi"}
        return {
            k: ("***REDACTED***" if k in sensitive_keys else val)
            for k, val in v.items()
        }


class AuditLogList(ApiSchema):
    items: list[AuditLogRead]
