"""Isolated evaluation adapter for clinical timelines and supersession auditing."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from hospital_ai.db.models import Base, Document, User
from hospital_ai.evaluation.adapter_foundation import EvaluationCaseContext, EvidenceResolutionError
from hospital_ai.evaluation.benchmark import EvalCaseV2
from hospital_ai.evaluation.product_retrieval_adapter import ProductRetrievalAdapter
from hospital_ai.evaluation.runner import CaseObservation
from hospital_ai.services.clinical_timeline import ClinicalTimelineService


class ProductTimelineAdapter:
    """Evaluate patient timeline events, chronological sorting, and supersession states."""

    def __init__(self, source_root: Path) -> None:
        self._retrieval_adapter = ProductRetrievalAdapter(source_root)

    async def evaluate(
        self, case: EvalCaseV2, context: EvaluationCaseContext, filters: Optional[dict[str, Any]] = None
    ) -> CaseObservation:
        if case.patient_id not in context.actor.allowed_patient_ids:
            raise EvidenceResolutionError("evaluation actor is not authorized for the requested patient timeline")

        locators = self._retrieval_adapter._unique_locators(
            case.allowed_evidence + case.forbidden_evidence + case.absence_checked_evidence
        )
        artifacts = tuple((locator, context.evidence_resolver.artifact_for(locator)) for locator in locators)
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        try:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            factory = async_sessionmaker(engine, expire_on_commit=False)
            async with factory() as session:
                await self._retrieval_adapter._materialize(
                    session,
                    context.actor.actor_id,
                    context.actor.role,
                    context.actor.allowed_patient_ids,
                    artifacts,
                )
                user = await session.get(User, context.actor.actor_id)
                if user is None:
                    raise EvidenceResolutionError("evaluation actor was not materialized")

                docs = list(
                    (await session.execute(select(Document).where(Document.patient_id == case.patient_id))).scalars()
                )
                timeline_service = ClinicalTimelineService(session)
                events = []
                for doc in docs:
                    res = await timeline_service.document_timeline(doc, user, filters or {})
                    events.extend(res.get("events", []))

                superseded_count = sum(
                    1
                    for ev in events
                    if getattr(ev, "superseded", False) or bool(getattr(ev, "supersession_lineage", ()))
                )

                return CaseObservation(
                    timeline_events=tuple(events),
                    superseded_retrieval_count=superseded_count,
                )
        finally:
            await engine.dispose()
