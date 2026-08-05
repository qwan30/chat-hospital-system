from __future__ import annotations
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.db.models import Document, User


@dataclass(frozen=True)
class TimelineEventProjection:
    event_type: str
    clinical_date: Optional[date]
    recorded_at: datetime
    evidence_ids: tuple[uuid.UUID, ...]
    confidence: float
    reviewer_state: str
    conflict_state: Literal["none", "date_conflict", "value_conflict"]
    supersession_lineage: tuple[uuid.UUID, ...]


class ClinicalTimelineService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def document_timeline(self, document: Document, current_user: User, filters: dict) -> dict:
        return {"events": []}
