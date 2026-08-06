from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.db.clinical_documents import ClinicalTimelineEvent
from hospital_ai.db.models import Document, User
from hospital_ai.services.evidence_scope import ActiveEvidenceScope


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
        filters = filters or {}
        allowed_chunk_ids = await ActiveEvidenceScope(self.session).authorized_chunk_id_set(
            user_id=current_user.id,
            patient_id=document.patient_id,
            document_ids=(document.id,),
        )
        if not allowed_chunk_ids:
            return {"events": []}

        result = await self.session.execute(
            select(ClinicalTimelineEvent).where(ClinicalTimelineEvent.patient_id == document.patient_id)
        )
        events = []
        min_confidence = filters.get("min_confidence", 0.0)
        date_from = filters.get("date_from")
        date_to = filters.get("date_to")

        for event in result.scalars().all():
            source = event.source_evidence or {}
            if str(source.get("document_id")) != str(document.id):
                continue

            evidence_values = source.get("chunk_ids") or source.get("evidence_ids") or []
            if not evidence_values:
                evidence_values = [source.get("chunk_id") or source.get("evidence_id")]
            evidence_ids = {uuid.UUID(str(value)) for value in evidence_values if _is_uuid(value)}

            authorized_evidence_ids = {chunk_id for chunk_id in evidence_ids if chunk_id in allowed_chunk_ids}
            if not authorized_evidence_ids:
                continue
            if event.confidence is not None and float(event.confidence) < min_confidence:
                continue
            if date_from is not None and event.clinical_date.date() < date_from:
                continue
            if date_to is not None and event.clinical_date.date() > date_to:
                continue

            events.append(
                {
                    "event_id": str(event.id),
                    "event_type": event.event_type,
                    "clinical_date": event.clinical_date.isoformat(),
                    "recorded_date": event.recorded_date.isoformat(),
                    "evidence_ids": sorted(str(value) for value in authorized_evidence_ids),
                    "confidence": float(event.confidence) if event.confidence is not None else None,
                    "reviewer_state": event.reviewer_state,
                    "conflict_state": event.conflict_state or "none",
                    "supersession_lineage": list(event.supersession_lineage or []),
                }
            )

        events.sort(key=lambda event: (event["clinical_date"], event["event_id"]))
        return {"events": events}


def _is_uuid(value: object) -> bool:
    try:
        uuid.UUID(str(value))
    except (ValueError, AttributeError):
        return False
    return True
