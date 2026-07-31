from datetime import datetime
from typing import Literal, Optional, Any
from pydantic import BaseModel
from .base import ApiSchema

class TimelineEventBase(ApiSchema):
    event_id: str
    timestamp: datetime
    type: Literal["chat", "document", "audit"]
    title: str
    body: str
    patient_id: Optional[str] = None
    metadata: dict[str, Any] = {}

class GlobalTimelineResponse(ApiSchema):
    events: list[TimelineEventBase]
    total_count: int
