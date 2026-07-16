"""Feedback and metrics summary API routes.
Các endpoint API xử lý gửi phản hồi/đánh giá (thumbs up/down) và thống kê chỉ số hiệu quả sử dụng.

POST /api/v1/feedback/queries/{query_id}/feedback   — submit rating
GET  /api/v1/feedback/metrics/summary               — aggregated metrics
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.routes.auth import get_current_user
from hospital_ai.db.models import AiQuery, AuditLog, User
from hospital_ai.db.session import get_session
from hospital_ai.services.metrics import MetricsService, UserFeedback

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────


class FeedbackRequest(BaseModel):
    rating: int = Field(..., ge=-1, le=1, description="Thumbs down (-1), neutral (0), or thumbs up (1)")
    comment: str | None = Field(None, max_length=2000)


class FeedbackResponse(BaseModel):
    id: UUID
    query_id: UUID
    rating: int
    comment: str | None = None


class MetricsSummaryResponse(BaseModel):
    total_queries: int
    avg_latency_ms: float
    total_time_saved_sec: int
    total_cost_saved: float
    helpful_rate: float
    no_evidence_rate: float = 0.0
    audit_deny_count: int = 0


# ── Routes ───────────────────────────────────────────────────────────────


@router.post(
    "/queries/{query_id}/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_feedback(
    query_id: UUID,
    body: FeedbackRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FeedbackResponse:
    """Submit user feedback (thumbs up/down) on a query response.
    Gửi đánh giá và phản hồi của người dùng (thích/không thích, bình luận) đối với một câu trả lời từ AI.
    """
    # Verify the query exists and belongs to the user
    result = await session.execute(select(AiQuery).where(AiQuery.id == query_id))
    query = result.scalar_one_or_none()
    if query is None:
        raise HTTPException(status_code=404, detail="Query not found.")
    if query.user_id != user.id:
        raise HTTPException(status_code=403, detail="Cannot submit feedback for another user's query.")

    # Check for duplicate feedback
    existing = await session.execute(
        select(UserFeedback).where(
            UserFeedback.query_id == query_id,
            UserFeedback.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Feedback already submitted for this query.")

    feedback = UserFeedback(
        query_id=query_id,
        user_id=user.id,
        rating=body.rating,
        comment=body.comment,
    )
    session.add(feedback)
    await session.commit()
    await session.refresh(feedback)

    return FeedbackResponse(
        id=feedback.id,
        query_id=feedback.query_id,
        rating=feedback.rating,
        comment=feedback.comment,
    )


@router.get("/metrics/summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MetricsSummaryResponse:
    """Get aggregated impact metrics. Available to all authenticated users.
    Lấy thống kê tổng hợp các chỉ số tác động (tiết kiệm thời gian, chi phí, tỷ lệ hữu ích).
    Cho phép mọi tài khoản đăng nhập truy cập.
    """
    summary = await MetricsService(session).get_summary()
    denied_result = await session.execute(select(func.count(AuditLog.id)).where(AuditLog.outcome == "denied"))
    return MetricsSummaryResponse(
        total_queries=summary.total_queries,
        avg_latency_ms=summary.avg_latency_ms,
        total_time_saved_sec=summary.total_time_saved_sec,
        total_cost_saved=summary.total_cost_saved,
        helpful_rate=summary.helpful_rate,
        no_evidence_rate=summary.no_evidence_rate,
        audit_deny_count=int(denied_result.scalar() or 0),
    )
