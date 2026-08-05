from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.errors import ConflictError
from hospital_ai.db.models import Document
from hospital_ai.db.clinical_documents import (
    DocumentIndexGeneration,
    DocumentRevisionSet,
    GenerationStageResult,
)


GENERATION_STAGES = (
    "ocr_normalization",
    "facts",
    "chunks",
    "embeddings",
    "lexical_index",
    "graph",
    "timeline",
)


@dataclass
class ActivationResult:
    active_generation_id: uuid.UUID
    approved_revision_set_id: uuid.UUID


class GenerationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _require_complete_build(self, generation_id: uuid.UUID) -> DocumentIndexGeneration:
        gen = await self.session.get(DocumentIndexGeneration, generation_id)
        if not gen:
            raise ValueError(f"Generation {generation_id} not found")
        return gen

    async def _lock_document(self, document_id: uuid.UUID) -> Document:
        doc = await self.session.get(Document, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")
        return doc

    async def activate(
        self, generation_id: uuid.UUID, expected_active_generation_id: uuid.UUID | None = None
    ) -> ActivationResult:
        generation = await self._require_complete_build(generation_id)
        document = await self._lock_document(generation.document_id)
        if document.active_index_generation_id != expected_active_generation_id:
            raise ConflictError("Serving generation changed while this build was running.")

        previous = None
        if document.active_index_generation_id:
            previous = await self.session.get(DocumentIndexGeneration, document.active_index_generation_id)

        document.active_index_generation_id = generation.id
        document.approved_revision_set_id = generation.revision_set_id
        generation.state = "active"
        generation.activated_at = datetime.now(UTC)

        if previous is not None:
            previous.state = "superseded"
            previous.superseded_at = datetime.now(UTC)
            if previous.revision_set_id != generation.revision_set_id:
                prev_set = await self.session.get(DocumentRevisionSet, previous.revision_set_id)
                if prev_set and prev_set.status == "approved":
                    prev_set.status = "superseded"

        document.status = "ready"
        document.index_generation += 1
        await self.session.commit()
        return ActivationResult(active_generation_id=generation.id, approved_revision_set_id=generation.revision_set_id)

    async def fail(self, generation_id: uuid.UUID, error_code: str, error_detail: str = "") -> None:
        gen = await self.session.get(DocumentIndexGeneration, generation_id)
        if gen:
            gen.state = "failed"
            gen.failed_at = datetime.now(UTC)
            gen.failure_code = error_code
            gen.failure_detail = error_detail
            await self.session.commit()

    async def rollback(
        self,
        *,
        document_id: uuid.UUID,
        target_generation_id: uuid.UUID,
        actor_id: uuid.UUID,
        expected_active_generation_id: uuid.UUID | None = None,
        reason: str = "",
    ) -> ActivationResult:
        document = await self._lock_document(document_id)
        if expected_active_generation_id is not None and document.active_index_generation_id != expected_active_generation_id:
            raise ConflictError("Stale active pointer for rollback.")

        target = await self.session.get(DocumentIndexGeneration, target_generation_id)
        if not target or target.document_id != document_id:
            raise ConflictError("Invalid target generation.")
        if document.active_index_generation_id == target_generation_id:
            raise ConflictError("Cannot rollback to currently active generation.")

        previous = None
        if document.active_index_generation_id:
            previous = await self.session.get(DocumentIndexGeneration, document.active_index_generation_id)

        document.active_index_generation_id = target.id
        document.approved_revision_set_id = target.revision_set_id
        target.state = "active"
        target.activated_at = datetime.now(UTC)

        if previous is not None:
            previous.state = "superseded"
            previous.superseded_at = datetime.now(UTC)
            if previous.revision_set_id != target.revision_set_id:
                prev_set = await self.session.get(DocumentRevisionSet, previous.revision_set_id)
                if prev_set:
                    prev_set.status = "superseded"

        t_set = await self.session.get(DocumentRevisionSet, target.revision_set_id)
        if t_set:
            t_set.status = "approved"

        document.status = "ready"
        document.index_generation += 1
        await self.session.commit()
        return ActivationResult(active_generation_id=target.id, approved_revision_set_id=target.revision_set_id)

    async def retry(self, document_id: uuid.UUID, generation_id: uuid.UUID, actor_id: uuid.UUID) -> DocumentIndexGeneration:
        orig = await self.session.get(DocumentIndexGeneration, generation_id)
        if not orig or orig.document_id != document_id:
            raise ValueError("Generation not found or mismatched document")
        new_gen = DocumentIndexGeneration(
            document_id=document_id,
            revision_set_id=orig.revision_set_id,
            retry_of_generation_id=orig.id,
            state="building",
            revision_set_sha256=orig.revision_set_sha256,
        )
        self.session.add(new_gen)
        await self.session.commit()
        await self.session.refresh(new_gen)
        return new_gen
