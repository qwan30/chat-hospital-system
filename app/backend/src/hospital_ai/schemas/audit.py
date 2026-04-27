from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field

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
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="meta")
    created_at: datetime


class AuditLogList(ApiSchema):
    items: List[AuditLogRead]
