from __future__ import annotations
from typing import Optional

import uuid
from collections.abc import Collection

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.security import PATIENT_READ_SCOPES
from hospital_ai.db.clinical_documents import (
    DocumentIndexGeneration,
    DocumentPageRevision,
    DocumentRevisionSet,
)
from hospital_ai.db.models import Document, DocumentChunk
from hospital_ai.services.permissions import active_patient_permission_exists

ACTIVE_GENERATION_JOINS_SQL = """
  join document_index_generations g on g.id = c.generation_id
  join document_revision_sets rs on rs.id = c.revision_set_id
""".strip()

ACTIVE_GENERATION_WHERE_SQL = """
    and d.active_index_generation_id = c.generation_id
    and g.state = 'active'
    and g.revision_set_id = c.revision_set_id
    and rs.status = 'approved'
""".strip()


class ActiveEvidenceScope:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def authorized_chunk_ids(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: uuid.UUID,
        document_ids: Optional[Collection[uuid.UUID]] = None,
    ):
        stmt = (
            select(DocumentChunk.id)
            .join(Document, Document.id == DocumentChunk.document_id)
            .join(DocumentIndexGeneration, DocumentIndexGeneration.id == DocumentChunk.generation_id)
            .join(DocumentRevisionSet, DocumentRevisionSet.id == DocumentChunk.revision_set_id)
            .join(DocumentPageRevision, DocumentPageRevision.id == DocumentChunk.page_revision_id)
            .where(
                Document.patient_id == patient_id,
                DocumentChunk.patient_id == patient_id,
                Document.active_index_generation_id == DocumentChunk.generation_id,
                DocumentIndexGeneration.state == "active",
                DocumentIndexGeneration.revision_set_id == DocumentChunk.revision_set_id,
                DocumentRevisionSet.status == "approved",
                Document.deleted_at.is_(None),
                DocumentChunk.deleted_at.is_(None),
                active_patient_permission_exists(
                    user_id=user_id,
                    patient_id=Document.patient_id,
                    accepted_scopes=PATIENT_READ_SCOPES,
                ),
            )
        )
        if document_ids is not None:
            stmt = stmt.where(Document.id.in_(tuple(document_ids)))
        return stmt.scalar_subquery()
