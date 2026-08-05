"""Tests for impact metrics service.

Covers:
- TimingBreakdown data structure
- MetricsService.record_query_metrics() creation and calculation
- Baseline time estimates and cost savings
- MetricsService.get_summary() aggregation
- MetricsSummary with feedback integration
- Edge cases: empty metrics, zero latency
"""
from __future__ import annotations

import uuid

import pytest

from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import AiQuery, User
from hospital_ai.services.metrics import (
    BASELINE_MANUAL_SECONDS,
    DEFAULT_HOURLY_COST,
    MetricsService,
    MetricsSummary,
    TimingBreakdown,
    UserFeedback,
)

# ── Unit: TimingBreakdown ────────────────────────────────────────────


def test_timing_breakdown_defaults():
    t = TimingBreakdown()
    assert t.total_ms == 0
    assert t.retrieval_ms == 0
    assert t.generation_ms == 0
    assert t.embedding_ms == 0


def test_timing_breakdown_custom():
    t = TimingBreakdown(total_ms=1500, retrieval_ms=300, generation_ms=800, embedding_ms=100)
    assert t.total_ms == 1500
    assert t.retrieval_ms == 300


# ── Unit: baseline constants ─────────────────────────────────────────


def test_baseline_manual_seconds_patient_summary():
    assert BASELINE_MANUAL_SECONDS["patient_summary"] == 750


def test_baseline_manual_seconds_general():
    assert BASELINE_MANUAL_SECONDS["general"] == 300


def test_default_hourly_cost():
    assert DEFAULT_HOURLY_COST == 20.0


# ── Integration: record_query_metrics ────────────────────────────────


@pytest.mark.asyncio
async def test_record_query_metrics_creates_event(session_and_settings):
    session, settings = session_and_settings
    await session.get(User, DOCTOR_ID)

    # Create an AI query to reference
    ai_query = AiQuery(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        question="What is the diagnosis?",
        status="completed",
        model="stub",
    )
    session.add(ai_query)
    await session.flush()

    timing = TimingBreakdown(total_ms=2000, retrieval_ms=500, generation_ms=1200, embedding_ms=100)
    svc = MetricsService(session)
    event = await svc.record_query_metrics(
        query_id=ai_query.id,
        user_id=DOCTOR_ID,
        task_type="simple",
        timing=timing,
        documents_retrieved=3,
        citations_count=2,
    )
    await session.commit()

    assert event.query_id == ai_query.id
    assert event.user_id == DOCTOR_ID
    assert event.task_type == "simple"
    assert event.query_latency_ms == 2000
    assert event.retrieval_latency_ms == 500
    assert event.generation_latency_ms == 1200
    assert event.documents_retrieved == 3
    assert event.citations_count == 2


@pytest.mark.asyncio
async def test_record_query_metrics_time_saved_calculation(session_and_settings):
    session, settings = session_and_settings

    ai_query = AiQuery(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        question="Summarize patient record",
        status="completed",
        model="stub",
    )
    session.add(ai_query)
    await session.flush()

    timing = TimingBreakdown(total_ms=3000)  # 3 seconds
    svc = MetricsService(session)
    event = await svc.record_query_metrics(
        query_id=ai_query.id,
        user_id=DOCTOR_ID,
        task_type="patient_summary",
        timing=timing,
    )
    await session.commit()

    # patient_summary baseline = 750 sec, actual = 3 sec → saved = 747 sec
    assert event.baseline_manual_time_sec == 750
    assert event.actual_ai_time_sec == 3
    assert event.estimated_time_saved_sec == 747
    expected_cost = (747 / 3600) * DEFAULT_HOURLY_COST
    assert abs(float(event.estimated_cost_saved) - round(expected_cost, 2)) < 0.01


@pytest.mark.asyncio
async def test_record_query_metrics_general_task_type(session_and_settings):
    session, settings = session_and_settings

    ai_query = AiQuery(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        question="Custom question",
        status="completed",
        model="stub",
    )
    session.add(ai_query)
    await session.flush()

    timing = TimingBreakdown(total_ms=1000)
    svc = MetricsService(session)
    event = await svc.record_query_metrics(
        query_id=ai_query.id,
        user_id=DOCTOR_ID,
        task_type="unknown_task",
        timing=timing,
    )
    await session.commit()

    # Unknown task defaults to "general" baseline = 300 sec
    assert event.baseline_manual_time_sec == 300


@pytest.mark.asyncio
async def test_record_query_metrics_with_thread(session_and_settings):
    session, settings = session_and_settings

    ai_query = AiQuery(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        question="Thread question",
        status="completed",
        model="stub",
    )
    session.add(ai_query)
    await session.flush()

    thread_id = uuid.uuid4()
    timing = TimingBreakdown(total_ms=1000)
    svc = MetricsService(session)
    event = await svc.record_query_metrics(
        query_id=ai_query.id,
        user_id=DOCTOR_ID,
        task_type="simple",
        timing=timing,
        thread_id=thread_id,
    )
    await session.commit()

    assert event.shared_thread_id == thread_id


# ── Integration: get_summary ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_summary_empty(session_and_settings):
    session, settings = session_and_settings
    summary = await MetricsService(session).get_summary()
    assert isinstance(summary, MetricsSummary)
    assert summary.total_queries == 0
    assert summary.avg_latency_ms == 0.0
    assert summary.total_time_saved_sec == 0
    assert summary.total_cost_saved == 0.0
    assert summary.helpful_rate == 0.0


@pytest.mark.asyncio
async def test_get_summary_with_events(session_and_settings):
    session, settings = session_and_settings

    # Create two metric events
    for i in range(2):
        ai_query = AiQuery(
            user_id=DOCTOR_ID,
            patient_id=PATIENT_ALICE_ID,
            question=f"Question {i}",
            status="completed",
            model="stub",
        )
        session.add(ai_query)
        await session.flush()

        timing = TimingBreakdown(total_ms=2000)
        await MetricsService(session).record_query_metrics(
            query_id=ai_query.id,
            user_id=DOCTOR_ID,
            task_type="simple",
            timing=timing,
            documents_retrieved=3,
        )
    await session.commit()

    summary = await MetricsService(session).get_summary()
    assert summary.total_queries == 2
    assert summary.avg_latency_ms == 2000.0
    assert summary.total_time_saved_sec > 0


@pytest.mark.asyncio
async def test_get_summary_with_feedback(session_and_settings):
    session, settings = session_and_settings

    ai_query = AiQuery(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        question="Feedback test",
        status="completed",
        model="stub",
    )
    session.add(ai_query)
    await session.flush()

    # Record metric
    timing = TimingBreakdown(total_ms=1000)
    await MetricsService(session).record_query_metrics(
        query_id=ai_query.id,
        user_id=DOCTOR_ID,
        task_type="simple",
        timing=timing,
    )

    # Add positive feedback
    session.add(
        UserFeedback(
            query_id=ai_query.id,
            user_id=DOCTOR_ID,
            rating=1,
            comment="Helpful answer",
        )
    )
    await session.commit()

    summary = await MetricsService(session).get_summary()
    assert summary.helpful_rate == 1.0  # 1 positive out of 1 total


@pytest.mark.asyncio
async def test_get_summary_mixed_feedback(session_and_settings):
    session, settings = session_and_settings

    # Create two queries with different feedback
    for i, rating in enumerate([1, -1]):
        ai_query = AiQuery(
            user_id=DOCTOR_ID,
            patient_id=PATIENT_ALICE_ID,
            question=f"Feedback question {i}",
            status="completed",
            model="stub",
        )
        session.add(ai_query)
        await session.flush()

        timing = TimingBreakdown(total_ms=1000)
        await MetricsService(session).record_query_metrics(
            query_id=ai_query.id,
            user_id=DOCTOR_ID,
            task_type="simple",
            timing=timing,
        )
        session.add(
            UserFeedback(
                query_id=ai_query.id,
                user_id=DOCTOR_ID,
                rating=rating,
            )
        )
    await session.commit()

    summary = await MetricsService(session).get_summary()
    assert summary.helpful_rate == 0.5  # 1 positive out of 2 total


# ── MetricEvent fields ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_metric_event_zero_latency(session_and_settings):
    """Edge case: sub-second queries shouldn't produce negative time saved."""
    session, settings = session_and_settings

    ai_query = AiQuery(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        question="Fast question",
        status="completed",
        model="stub",
    )
    session.add(ai_query)
    await session.flush()

    timing = TimingBreakdown(total_ms=50)  # 50ms → actual_sec = max(1, 0) = 1
    svc = MetricsService(session)
    event = await svc.record_query_metrics(
        query_id=ai_query.id,
        user_id=DOCTOR_ID,
        task_type="simple",
        timing=timing,
    )
    await session.commit()

    assert event.actual_ai_time_sec >= 1
    assert event.estimated_time_saved_sec >= 0
