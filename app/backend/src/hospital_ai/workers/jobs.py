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

    await session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    await session.execute(delete(DocumentPage).where(DocumentPage.document_id == document_id))
    document.status = "ocr_processing"
    document.ocr_error = None
    await session.commit()

    try:
        pages = OcrService().extract_pages(storage_uri=document.storage_uri, mime_type=document.mime_type)
    except Exception as exc:
        document.status = "ocr_failed"
        document.ocr_error = str(exc)
        await session.commit()
        return

    page_rows: Dict[int, DocumentPage] = {}
    for page in pages:
        page_row = DocumentPage(
            document_id=document.id,
            page_number=page.page_number,
            ocr_text=page.text,
            ocr_confidence=page.confidence,
        )
        session.add(page_row)
        page_rows[page.page_number] = page_row

    document.status = "ocr_completed"
    document.page_count = len(page_rows)
    await session.flush()
    await session.commit()

    document = await session.get(Document, document_id)
    if document is None:
        return
    document.status = "indexing"
    await session.commit()

    try:
        chunks = ChunkingService().chunk_pages(pages)
        embeddings = await EmbeddingService(settings).embed_many(chunk.content for chunk in chunks)
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
        await session.commit()
    except Exception as exc:
        document.status = "index_failed"
        document.ocr_error = str(exc)
        await session.commit()


def process_document_job(document_id: str) -> None:
    async def _run() -> None:
        settings = get_settings()
        session_factory = get_session_factory()
        async with session_factory() as session:
            await process_document(session, uuid.UUID(document_id), settings)

    asyncio.run(_run())
