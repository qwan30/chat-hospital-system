from __future__ import annotations
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings
from hospital_ai.db.models import Document, DocumentProcessingEvent


class PipelineStage:
    pass


async def process_document_pipeline(session: AsyncSession, document_id: uuid.UUID, settings: Settings) -> None:
    from hospital_ai.workers.extraction_jobs import extract_document

    await extract_document(session, document_id, settings)
