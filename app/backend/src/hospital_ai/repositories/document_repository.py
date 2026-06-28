import uuid
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.db.models import Document, DocumentChunk, DocumentPage


class DocumentRepository:
    """Repository layer encapsulating database access patterns for Document entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, document_id: uuid.UUID) -> Optional[Document]:
        stmt = select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_patient_id(self, patient_id: uuid.UUID) -> Sequence[Document]:
        stmt = select(Document).where(Document.patient_id == patient_id, Document.deleted_at.is_(None)).order_by(Document.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_chunks_for_document(self, document_id: uuid.UUID) -> None:
        stmt = select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        result = await self.session.execute(stmt)
        chunks = result.scalars().all()
        for chunk in chunks:
            await self.session.delete(chunk)
