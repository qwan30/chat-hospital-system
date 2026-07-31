import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from .common import ApiSchema


class TimelineEventBase(ApiSchema):
    event_id: str
    timestamp: datetime
    type: Literal["chat", "document", "audit"]
    title: str
    body: str
    patient_id: Optional[uuid.UUID] = None
    metadata: dict[str, Any] = {}

class GlobalTimelineResponse(ApiSchema):
    events: list[TimelineEventBase]
    total_count: int
