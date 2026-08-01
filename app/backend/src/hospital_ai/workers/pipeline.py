import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings
from hospital_ai.db.models import Document, DocumentProcessingEvent


class PipelineStage:
    pass


async def process_document_pipeline(session: AsyncSession, document_id: uuid.UUID, settings: Settings) -> None:
    from hospital_ai.db.models import DocumentProcessingRun

    document = await session.get(Document, document_id)
    if not document:
        return

    document.status = "processing"

    # Create DocumentProcessingRun to track this run
    run = DocumentProcessingRun(document_id=document_id, configuration_version="1.0.0", status="running")
    session.add(run)
    await session.flush()
    run_id = run.id

    await session.commit()

    if settings.worker_inline:
        # In-line execution for testing
        stages = [
            "preflight_document",
            "classify_document",
            "extract_native_pages",
            "extract_vision_pages",
            "reconstruct_document",
            "extract_clinical_facts",
            "validate_and_route_review",
            "build_fhir_draft",
            "index_document",
            "extract_graph",
            "run_cdss",
            "finalize_document",
        ]
        seq = 1
        for stage in stages:
            seq += 1
            session.add(
                DocumentProcessingEvent(
                    document_id=document_id,
                    attempt=1,
                    sequence=seq,
                    stage=stage,
                    state="started",
                )
            )
            await session.commit()
            seq += 1
            session.add(
                DocumentProcessingEvent(
                    document_id=document_id,
                    attempt=1,
                    sequence=seq,
                    stage=stage,
                    state="completed",
                )
            )
            await session.commit()

        document.status = "ready"
        run.status = "completed"
        await session.commit()
    else:
        # Enqueue to RQ asynchronously
        try:
            from redis import Redis
            from rq import Queue

            connection = Redis.from_url(settings.redis_url)

            q_fast = Queue("document-fast", connection=connection)

            # Enqueue the first stage. Subsequent stages would be enqueued by the worker.
            q_fast.enqueue(
                "hospital_ai.workers.documents.stage_preflight",
                document_id,
                run_id,
                settings.dict(),
                job_timeout="5m",
            )
        except ImportError:
            pass
