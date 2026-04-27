import asyncio
import hashlib
import uuid
from pathlib import Path
from typing import Dict, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings, get_settings
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage
from hospital_ai.db.session import get_session_factory
from hospital_ai.services.chunking import ChunkingService
from hospital_ai.services.embeddings import EmbeddingService
from hospital_ai.services.ocr import OcrService


async def process_document(
    session: AsyncSession,
    document_id: uuid.UUID,
    settings: Settings,
) -> None:
    document = await session.get(Document, document_id)
    if document is None:
        return

    previous_status = document.status
    start_generation = document.index_generation
    source_sha256 = _source_sha256(document.storage_uri)
    preserve_existing_index = previous_status == "indexed" and (
        source_sha256 is None or document.indexed_source_sha256 == source_sha256
    )
    document.ocr_error = None
    if previous_status != "indexed":
        document.status = "ocr_processing"
    await session.commit()

    try:
        pages = OcrService().extract_pages(
            storage_uri=document.storage_uri,
            mime_type=document.mime_type,
        )
    except Exception as exc:
        await _mark_failed_if_current(
            session,
            document_id,
            start_generation,
            preserve_existing_index,
            "ocr_failed",
            str(exc),
        )
        return

    try:
        chunks = ChunkingService().chunk_pages(pages)
        embeddings = await EmbeddingService(settings).embed_many(chunk.content for chunk in chunks)
    except Exception as exc:
        await _mark_failed_if_current(
            session,
            document_id,
            start_generation,
            preserve_existing_index,
            "index_failed",
            str(exc),
        )
        return

    page_rows: Dict[int, DocumentPage] = {}
    try:
        document = await _locked_current_document(session, document_id)
        if document is None or document.index_generation != start_generation:
            await session.rollback()
            return

        document.status = "indexing"
        await session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
        await session.execute(delete(DocumentPage).where(DocumentPage.document_id == document_id))

        for page in pages:
            page_row = DocumentPage(
                document_id=document.id,
                page_number=page.page_number,
                ocr_text=page.text,
                ocr_confidence=page.confidence,
            )
            session.add(page_row)
            page_rows[page.page_number] = page_row

        document.page_count = len(page_rows)
        await session.flush()

        for chunk, embedding in zip(chunks, embeddings):
            page_row = page_rows[chunk.page_number]
            session.add(
                DocumentChunk(
                    document_id=document.id,
                    page_id=page_row.id,
                    patient_id=document.patient_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    embedding=embedding,
                    meta={
                        "page_number": chunk.page_number,
                        "start_offset": chunk.start_offset,
                        "end_offset": chunk.end_offset,
                    },
                )
            )
        document.status = "indexed"
        document.ocr_error = None
        document.index_generation = start_generation + 1
        document.indexed_source_sha256 = source_sha256
        await session.commit()
    except Exception as exc:
        await session.rollback()
        await _mark_failed_if_current(
            session,
            document_id,
            start_generation,
            preserve_existing_index,
            "index_failed",
            str(exc),
        )


def _source_sha256(storage_uri: str) -> Optional[str]:
    try:
        return hashlib.sha256(Path(storage_uri).read_bytes()).hexdigest()
    except OSError:
        return None


def _failure_status(preserve_existing_index: bool, failed_status: str) -> str:
    if preserve_existing_index:
        return "indexed"
    return failed_status


async def _locked_current_document(
    session: AsyncSession,
    document_id: uuid.UUID,
) -> Optional[Document]:
    result = await session.execute(
        select(Document)
        .where(Document.id == document_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    return result.scalar_one_or_none()


async def _mark_failed_if_current(
    session: AsyncSession,
    document_id: uuid.UUID,
    start_generation: int,
    preserve_existing_index: bool,
    failed_status: str,
    error: str,
) -> None:
    document = await _locked_current_document(session, document_id)
    if document is None or document.index_generation != start_generation:
        await session.rollback()
        return

    document.status = _failure_status(preserve_existing_index, failed_status)
    document.ocr_error = error
    await session.commit()


def process_document_job(document_id: str) -> None:
    async def _run() -> None:
        settings = get_settings()
        session_factory = get_session_factory()
        async with session_factory() as session:
            await process_document(session, uuid.UUID(document_id), settings)

    asyncio.run(_run())
