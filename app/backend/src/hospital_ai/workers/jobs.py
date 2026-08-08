import asyncio
import logging
import uuid
from typing import Literal, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings, get_settings
from hospital_ai.db.models import Document, DocumentChunk, DocumentProcessingEvent
from hospital_ai.db.session import get_session_factory
from hospital_ai.services.storage import StorageService, get_storage_service


async def process_document(session: AsyncSession, document_id: uuid.UUID, settings: Settings) -> None:
    from hospital_ai.workers.extraction_jobs import extract_document

    await extract_document(session, document_id, settings)


async def _populate_tsvectors(session: AsyncSession, document_id: uuid.UUID) -> None:
    """Populate tsvector column for newly indexed chunks (PostgreSQL only).

    Uses to_tsvector('english', content) to generate the search_vector.
    Silently skips on non-PostgreSQL dialects.
    """
    from sqlalchemy import text as sql_text

    bind = session.get_bind()
    if bind.dialect.name != "postgresql":
        return

    try:
        await session.execute(
            sql_text("""
                UPDATE document_chunks
                SET search_vector = to_tsvector('english', content)
                WHERE document_id = :doc_id
                  AND search_vector IS NULL
            """),
            {"doc_id": document_id},
        )
    except Exception:
        # search_vector column may not exist yet (pre-migration)
        import logging

        logging.getLogger(__name__).debug(
            "tsvector population skipped for document %s (column may not exist)", document_id
        )


async def _index_graph_entities(session: AsyncSession, document: Document) -> None:
    """Extract medical entities and relations from document chunks for graph RAG.

    Silently skips on failure to avoid blocking the main indexing pipeline.
    """

    logger = logging.getLogger(__name__)
    try:
        from hospital_ai.services.graph_rag import index_chunk_entities

        result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document.id))
        chunks = list(result.scalars().all())

        total_entities = 0
        total_relations = 0
        for chunk in chunks:
            entities, relations = await index_chunk_entities(
                session, chunk_id=chunk.id, document_id=document.id, content=chunk.content
            )
            total_entities += len(entities)
            total_relations += len(relations)

        logger.info(
            "Graph RAG indexed %d entities, %d relations for document %s", total_entities, total_relations, document.id
        )
    except Exception:
        logger.debug("Graph entity indexing skipped for document %s", document.id, exc_info=True)


def _source_sha256(
    settings: Settings,
    storage_uri: str,
    storage_service: Optional[StorageService] = None,
) -> Optional[str]:
    if storage_uri == "pending" or storage_uri.startswith("local://") or storage_uri.startswith("hms://"):
        return None
    try:
        service = storage_service or get_storage_service(settings)
        return service.source_sha256(storage_uri)
    except (FileNotFoundError, OSError, ValueError):
        return None


def _failure_status(preserve_existing_index: bool, failed_status: str) -> str:
    if preserve_existing_index:
        return "ready_with_warnings"
    return failed_status


async def _locked_current_document(session: AsyncSession, document_id: uuid.UUID) -> Optional[Document]:
    result = await session.execute(
        select(Document).where(Document.id == document_id).with_for_update().execution_options(populate_existing=True)
    )
    return result.scalar_one_or_none()


async def _next_processing_attempt(session: AsyncSession, document_id: uuid.UUID) -> int:
    max_attempt = await session.scalar(
        select(func.max(DocumentProcessingEvent.attempt)).where(DocumentProcessingEvent.document_id == document_id)
    )
    return int(max_attempt or 0) + 1


async def _record_processing_event(
    session: AsyncSession,
    document_id: uuid.UUID,
    attempt: int,
    stage: str,
    state: str,
    *,
    progress_current: Optional[int] = None,
    progress_total: Optional[int] = None,
    error_code: Optional[str] = None,
) -> None:
    max_sequence = await session.scalar(
        select(func.max(DocumentProcessingEvent.sequence)).where(
            DocumentProcessingEvent.document_id == document_id,
            DocumentProcessingEvent.attempt == attempt,
        )
    )
    session.add(
        DocumentProcessingEvent(
            document_id=document_id,
            attempt=attempt,
            sequence=int(max_sequence or 0) + 1,
            stage=stage,
            state=state,
            progress_current=progress_current,
            progress_total=progress_total,
            error_code=error_code,
        )
    )


async def _mark_failed_if_current(
    session: AsyncSession,
    document_id: uuid.UUID,
    start_generation: int,
    preserve_existing_index: bool,
    failed_status: str,
    failure_stage: Literal["ocr", "index"],
    attempt: int,
) -> None:
    document = await _locked_current_document(session, document_id)
    if document is None or document.index_generation != start_generation:
        await session.rollback()
        return

    document.status = _failure_status(preserve_existing_index, failed_status)
    error_code = "OCR_FAILED" if failure_stage == "ocr" else "INDEX_FAILED"
    document.ocr_error = (
        "OCR processing failed. Please retry the document."
        if error_code == "OCR_FAILED"
        else "Indexing failed. Please retry the document."
    )
    await _record_processing_event(
        session,
        document_id,
        attempt,
        failure_stage,
        "failed",
        error_code=error_code,
    )
    await session.commit()


def process_document_job(document_id: str) -> None:
    """Entry point called by rq workers.

    On final failure (after all retries exhausted), the document is moved
    to the dead-letter queue for manual inspection.
    """

    logger = logging.getLogger(__name__)
    logger.info("Starting document processing job for %s", document_id)

    async def _run() -> None:
        settings = get_settings()
        session_factory = get_session_factory()
        async with session_factory() as session:
            try:
                await process_document(session, uuid.UUID(document_id), settings)
                logger.info("Document %s processed successfully.", document_id)
            except Exception as exc:
                logger.exception("Document %s processing failed: %s", document_id, exc)
                from rq import get_current_job

                job = get_current_job()
                if job is None or not job.should_retry:
                    try:
                        from hospital_ai.workers.queue import enqueue_to_dead_letter

                        enqueue_to_dead_letter(uuid.UUID(document_id), settings, str(exc))
                    except Exception:
                        logger.error("Failed to move document %s to dead-letter queue.", document_id)
                raise  # Re-raise so rq marks the job as failed

    asyncio.run(_run())


def dead_letter_handler(document_id: str, error_message: str) -> None:
    """Handler for dead-letter queue items.

    Logs the failure for monitoring.  A future admin dashboard or
    alerting hook can subscribe to this queue for notifications.
    """

    logger = logging.getLogger(__name__)
    logger.error("DEAD-LETTER: Document %s permanently failed: %s", document_id, error_message)


def cdss_job_handler(document_id: str) -> None:
    """Entry point called by rq workers for CDSS analysis."""

    logger = logging.getLogger(__name__)
    logger.info("Starting CDSS analysis job for %s", document_id)

    async def _run() -> None:
        from hospital_ai.db.session import get_session_factory
        from hospital_ai.workers.cdss import run_cdss_analysis

        session_factory = get_session_factory()
        async with session_factory() as session:
            try:
                await run_cdss_analysis(session, uuid.UUID(document_id))
                logger.info("CDSS analysis processed successfully for %s.", document_id)
            except Exception as exc:
                logger.exception("Document %s CDSS analysis failed: %s", document_id, exc)
                raise  # Re-raise so rq marks the job as failed

    asyncio.run(_run())
