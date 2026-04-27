import asyncio
import uuid
from typing import Dict

from sqlalchemy import delete
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
        document.status = _failure_status(previous_status, "ocr_failed")
        document.ocr_error = str(exc)
        await session.commit()
        return

    try:
        chunks = ChunkingService().chunk_pages(pages)
        embeddings = await EmbeddingService(settings).embed_many(chunk.content for chunk in chunks)
    except Exception as exc:
        document.status = _failure_status(previous_status, "index_failed")
        document.ocr_error = str(exc)
        await session.commit()
        return

    page_rows: Dict[int, DocumentPage] = {}
    try:
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
        await session.commit()
    except Exception as exc:
        await session.rollback()
        document = await session.get(Document, document_id)
        if document is None:
            return
        document.status = _failure_status(previous_status, "index_failed")
        document.ocr_error = str(exc)
        await session.commit()


def _failure_status(previous_status: str, failed_status: str) -> str:
    if previous_status == "indexed":
        return previous_status
    return failed_status


def process_document_job(document_id: str) -> None:
    async def _run() -> None:
        settings = get_settings()
        session_factory = get_session_factory()
        async with session_factory() as session:
            await process_document(session, uuid.UUID(document_id), settings)

    asyncio.run(_run())
