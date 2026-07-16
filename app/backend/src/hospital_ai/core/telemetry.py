"""OpenTelemetry and Prometheus instrumentation for Hospital AI backend.
Thiết lập thu thập chỉ số đo lường (metrics) Prometheus và OpenTelemetry cho backend Trợ lý AI Bệnh viện.

Giúp giám sát hiệu năng LLM, thời gian truy xuất RAG, số lượng trích dẫn, và số lần bị chặn bởi guardrail.
"""

from __future__ import annotations

import logging

try:
    import openlit

    _OPENLIT_AVAILABLE = True
except ImportError:
    _OPENLIT_AVAILABLE = False

from prometheus_client import Counter, Histogram, Info

from hospital_ai.core.config import Settings

logger = logging.getLogger(__name__)


def setup_telemetry() -> None:
    """Khởi tạo OpenLit để giám sát và thu thập telemetry cho LLM (nếu gói openlit được cài đặt)."""
    if _OPENLIT_AVAILABLE:
        openlit.init(environment="production")
    else:
        logger.info("openlit not installed — LLM observability disabled")


# Define metrics
# Định nghĩa các chỉ số đo lường Prometheus
LLM_REQUEST_DURATION = Histogram(
    "llm_request_duration_seconds", "LLM request duration in seconds", ["provider", "model"]
)
LLM_TOKEN_USAGE = Counter(
    "llm_token_usage_total",
    "Total LLM tokens used",
    ["provider", "model", "direction"],  # direction: prompt/completion (hướng: prompt đầu vào hoặc completion đầu ra)
)
RAG_RETRIEVAL_DURATION = Histogram(
    "rag_retrieval_duration_seconds",
    "RAG retrieval duration in seconds",
    ["mode"],  # vector/bm25/hybrid (chế độ tìm kiếm)
)
RAG_EVIDENCE_COUNT = Histogram(
    "rag_evidence_count",
    "Number of evidence chunks retrieved per query",
    ["scope"],  # general/patient-linked (phạm vi: chung hay liên kết bệnh nhân)
)
GUARDRAIL_BLOCKS = Counter(
    "guardrail_blocks_total",
    "Total guardrail blocks",
    ["type", "reason"],  # type: input/output, reason: injection/phi_leak/etc (lý do chặn: injection, rò rỉ PHI...)
)
CHAT_REQUESTS = Counter(
    "chat_request_total",
    "Total chat requests",
    ["scope", "status"],  # scope: general/patient, status: success/error/blocked (trạng thái: thành công/lỗi/bị chặn)
)
APP_INFO = Info("hospital_ai", "Hospital AI application info")


def setup_metrics(settings: Settings) -> None:
    """Initialize application metrics.
    Khởi tạo và ghi nhận cấu hình hệ thống vào Prometheus Info metric.
    """
    APP_INFO.info(
        {
            "environment": settings.environment,
            "chat_provider": settings.chat_provider,
            "embedding_provider": settings.embedding_provider,
            "retrieval_mode": settings.retrieval_mode,
            "reranker_provider": settings.reranker_provider,
        }
    )
    logger.info("Prometheus metrics initialized")

