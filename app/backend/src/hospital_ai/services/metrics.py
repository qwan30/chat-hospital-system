"""Impact metrics capture and analysis service.

Records timing breakdowns, calculates time/cost savings, and
provides summary aggregations for the metrics dashboard.
"""

from __future__ import annotations

from typing import Optional

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from hospital_ai.db.models import Base

# ── ORM Model ───────────────────────────────────────────────────────────


class MetricEvent(Base):
    """Captures per-query impact metrics for dashboard analysis."""

    __tablename__ = "metric_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    query_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ai_queries.id"), nullable=True, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    baseline_manual_time_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_ai_time_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_time_saved_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost_saved: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    documents_retrieved: Mapped[int | None] = mapped_column(Integer, nullable=True)
    citations_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    query_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retrieval_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    generation_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shared_thread_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UserFeedback(Base):
    """User rating and comment on an AI query response."""

    __tablename__ = "user_feedback"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    query_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ai_queries.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # -1, 0, 1
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


# ── Baseline assumptions from doc 10 §8 ────────────────────────────────

BASELINE_MANUAL_SECONDS = {
    "patient_summary": 750,  # 10-15 min → avg 12.5 min = 750 sec
    "document_lookup": 450,  # 5-10 min → avg 7.5 min = 450 sec
    "medication_check": 240,  # 3-5 min → avg 4 min = 240 sec
    "lab_lookup": 450,  # 5-10 min → avg 7.5 min = 450 sec
    "general": 300,  # default 5 min
}

DEFAULT_HOURLY_COST = 20.0  # $/hour from doc 10 §9


@dataclass
class TimingBreakdown:
    """Timing data captured during a query pipeline run."""

    total_ms: int = 0
    retrieval_ms: int = 0
    generation_ms: int = 0
    embedding_ms: int = 0


@dataclass
class MetricsSummary:
    """Aggregated metrics for dashboard display."""

    total_queries: int = 0
    avg_latency_ms: float = 0.0
    total_time_saved_sec: int = 0
    total_cost_saved: float = 0.0
    helpful_rate: float = 0.0  # fraction of positive feedback
    no_evidence_rate: float = 0.0


class MetricsService:
    """Records and aggregates impact metrics."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_query_metrics(
        self,
        *,
        query_id: uuid.UUID,
        user_id: uuid.UUID,
        task_type: str,
        timing: TimingBreakdown,
        documents_retrieved: int = 0,
        citations_count: int = 0,
        thread_id: uuid.UUID | None = None,
    ) -> MetricEvent:
        """Record impact metrics for a completed query."""
        baseline_sec = BASELINE_MANUAL_SECONDS.get(task_type, BASELINE_MANUAL_SECONDS["general"])
        actual_sec = max(1, timing.total_ms // 1000)
        time_saved_sec = max(0, baseline_sec - actual_sec)
        cost_saved = (time_saved_sec / 3600) * DEFAULT_HOURLY_COST

        event = MetricEvent(
            query_id=query_id,
            user_id=user_id,
            task_type=task_type,
            baseline_manual_time_sec=baseline_sec,
            actual_ai_time_sec=actual_sec,
            estimated_time_saved_sec=time_saved_sec,
            estimated_cost_saved=round(cost_saved, 2),
            documents_retrieved=documents_retrieved,
            citations_count=citations_count,
            query_latency_ms=timing.total_ms,
            retrieval_latency_ms=timing.retrieval_ms,
            generation_latency_ms=timing.generation_ms,
            shared_thread_id=thread_id,
        )
        self.session.add(event)
        return event

    async def get_summary(self) -> MetricsSummary:
        """Aggregate metrics across all recorded events."""
        # Total queries and avg latency
        result = await self.session.execute(
            select(
                func.count(MetricEvent.id),
                func.avg(MetricEvent.query_latency_ms),
                func.sum(MetricEvent.estimated_time_saved_sec),
                func.sum(MetricEvent.estimated_cost_saved),
            )
        )
        row = result.one()
        total_queries = row[0] or 0
        avg_latency = float(row[1]) if row[1] else 0.0
        total_saved = int(row[2]) if row[2] else 0
        total_cost = float(row[3]) if row[3] else 0.0

        # Feedback rate
        from sqlalchemy import case

        fb_result = await self.session.execute(
            select(
                func.count(UserFeedback.id),
                func.sum(case((UserFeedback.rating > 0, 1), else_=0)),
            )
        )
        fb_row = fb_result.one()
        total_feedback = fb_row[0] or 0
        positive_count = int(fb_row[1]) if fb_row[1] else 0
        helpful_rate = positive_count / total_feedback if total_feedback > 0 else 0.0

        return MetricsSummary(
            total_queries=total_queries,
            avg_latency_ms=round(avg_latency, 1),
            total_time_saved_sec=total_saved,
            total_cost_saved=round(total_cost, 2),
            helpful_rate=round(helpful_rate, 3),
        )
