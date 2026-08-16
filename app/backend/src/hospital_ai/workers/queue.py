"""Worker queue helpers — Redis-backed document processing queue.

Wraps rq with retry and dead-letter support so that transient OCR/embedding
failures are retried automatically and permanently-failed jobs are moved to
a dead-letter queue for manual inspection.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from hospital_ai.core.config import Settings

logger = logging.getLogger(__name__)

# Retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_INTERVALS = [60, 300, 900]  # 1min, 5min, 15min
DEAD_LETTER_QUEUE = "document-indexing-dlq"


def enqueue_document_indexing(
    document_id: uuid.UUID,
    settings: Settings,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_intervals: Optional[list[int]] = None,
) -> str:
    """Enqueue a document for indexing with automatic retry support.

    Returns:
        "queued" — job was enqueued to Redis.
        "queue_unavailable" — Redis or rq not available; caller should fall
            back to synchronous processing.
    """
    try:
        from redis import Redis
        from rq import Queue, Retry
    except ImportError:
        logger.warning(
            "redis/rq not installed — document %s will not be queued.",
            document_id,
        )
        return "queue_unavailable"

    intervals = retry_intervals or DEFAULT_RETRY_INTERVALS[:max_retries]
    try:
        connection = Redis.from_url(settings.redis_url)
        connection.ping()  # Fail fast if Redis is unreachable
    except Exception:
        logger.warning(
            "Redis unreachable at %s — document %s will not be queued.",
            settings.redis_url,
            document_id,
        )
        return "queue_unavailable"

    queue = Queue("document-indexing", connection=connection)
    retry = Retry(max=max_retries, interval=intervals)

    queue.enqueue(
        "hospital_ai.workers.jobs.process_document_job",
        str(document_id),
        retry=retry,
        job_timeout="30m",
        result_ttl=86400,  # keep result for 24 h
        failure_ttl=604800,  # keep failure info for 7 d
        meta={"document_id": str(document_id), "max_retries": max_retries},
    )
    logger.info(
        "Document %s enqueued for indexing (max_retries=%d).",
        document_id,
        max_retries,
    )
    return "queued"


def enqueue_to_dead_letter(
    document_id: uuid.UUID,
    settings: Settings,
    error_message: str,
) -> str:
    """Move a permanently-failed document to the dead-letter queue."""
    try:
        from redis import Redis
        from rq import Queue
    except ImportError:
        return "queue_unavailable"

    try:
        connection = Redis.from_url(settings.redis_url)
        connection.ping()
    except Exception:
        return "queue_unavailable"

    dlq = Queue(DEAD_LETTER_QUEUE, connection=connection)
    dlq.enqueue(
        "hospital_ai.workers.jobs.dead_letter_handler",
        str(document_id),
        error_message,
        job_timeout="5m",
        result_ttl=604800,
        meta={
            "document_id": str(document_id),
            "original_error": error_message,
            "queue": "document-indexing",
        },
    )
    logger.warning(
        "Document %s moved to dead-letter queue: %s",
        document_id,
        error_message,
    )
    return "dead_lettered"


def get_queue_stats(settings: Settings) -> dict:
    """Return basic queue metrics for monitoring."""
    try:
        from redis import Redis
        from rq import Queue
    except ImportError:
        return {"available": False}

    try:
        connection = Redis.from_url(settings.redis_url)
        connection.ping()
    except Exception:
        return {"available": False}

    main_queue = Queue("document-indexing", connection=connection)
    dlq = Queue(DEAD_LETTER_QUEUE, connection=connection)

    return {
        "available": True,
        "pending": len(main_queue),
        "failed": main_queue.failed_job_registry.count,
        "dead_letter": len(dlq),
        "workers": main_queue.count,
    }


def enqueue_cdss_analysis(
    document_id: uuid.UUID,
    settings: Settings,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_intervals: Optional[list[int]] = None,
) -> str:
    """Enqueue a document for CDSS analysis."""
    try:
        from redis import Redis
        from rq import Queue, Retry
    except ImportError:
        return "queue_unavailable"

    try:
        connection = Redis.from_url(settings.redis_url)
        connection.ping()
    except Exception:
        return "queue_unavailable"

    queue = Queue("cdss-analysis", connection=connection)
    intervals = retry_intervals or DEFAULT_RETRY_INTERVALS[:max_retries]
    retry = Retry(max=max_retries, interval=intervals)

    queue.enqueue(
        "hospital_ai.workers.jobs.cdss_job_handler",
        str(document_id),
        retry=retry,
        job_timeout="30m",
        result_ttl=86400,
        failure_ttl=604800,
        meta={"document_id": str(document_id), "max_retries": max_retries},
    )
    logger.info("Document %s enqueued for CDSS analysis (max_retries=%d).", document_id, max_retries)
    return "queued"


def enqueue_build_generation(
    generation_id: uuid.UUID,
    settings: Optional[Settings] = None,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_intervals: Optional[list[int]] = None,
) -> str:
    """Enqueue a document generation for stage building."""
    if settings is None:
        from hospital_ai.core.config import get_settings

        settings = get_settings()

    try:
        from redis import Redis
        from rq import Queue, Retry
    except ImportError:
        return "queue_unavailable"

    try:
        connection = Redis.from_url(settings.redis_url)
        connection.ping()
    except Exception:
        return "queue_unavailable"

    queue = Queue("document-generation-build", connection=connection)
    intervals = retry_intervals or DEFAULT_RETRY_INTERVALS[:max_retries]
    retry = Retry(max=max_retries, interval=intervals)

    queue.enqueue(
        "hospital_ai.workers.generation_jobs.build_generation_job",
        str(generation_id),
        retry=retry,
        job_timeout="30m",
        result_ttl=86400,
        failure_ttl=604800,
        meta={"generation_id": str(generation_id), "max_retries": max_retries},
    )
    logger.info("Generation %s enqueued for building (max_retries=%d).", generation_id, max_retries)
    return "queued"
