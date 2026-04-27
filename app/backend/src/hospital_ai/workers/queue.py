import uuid

from hospital_ai.core.config import Settings


def enqueue_document_indexing(document_id: uuid.UUID, settings: Settings) -> str:
    try:
        from redis import Redis
        from rq import Queue
    except Exception:
        return "queue_unavailable"

    connection = Redis.from_url(settings.redis_url)
    queue = Queue("document-indexing", connection=connection)
    queue.enqueue("hospital_ai.workers.jobs.process_document_job", str(document_id))
    return "queued"
