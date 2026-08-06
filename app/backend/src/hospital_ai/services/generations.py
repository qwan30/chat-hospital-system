from __future__ import annotations

import hashlib
import string
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.errors import ConflictError
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.clinical_documents import (
    DocumentIndexGeneration,
    DocumentPageRevision,
    DocumentRevisionSet,
    GenerationStageResult,
)
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage
from hospital_ai.services.audit import AuditService

GENERATION_STAGES = (
    "ocr_normalization",
    "facts",
    "chunks",
    "embeddings",
    "lexical_index",
    "graph",
    "timeline",
)


def calculate_generation_hash(stage_hashes: Iterable[str]) -> str:
    return hashlib.sha256("".join(stage_hashes).encode("utf-8")).hexdigest()


def _is_sha256(value: Optional[str]) -> bool:
    return bool(value) and len(value) == 64 and all(char in string.hexdigits for char in value)


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

        if gen.state != "building":
            raise ConflictError("Only a building generation can be activated.")

        result = await self.session.execute(
            select(GenerationStageResult).where(GenerationStageResult.generation_id == generation_id)
        )
        stage_rows = {row.stage: row for row in result.scalars().all()}
        if set(stage_rows) != set(GENERATION_STAGES):
            raise ConflictError("Generation is incomplete: required stages are missing.")
        if any(row.status != "completed" or not _is_sha256(row.output_sha256) for row in stage_rows.values()):
            raise ConflictError("Generation is incomplete: every stage must complete with an output hash.")

        stage_hashes: list[str] = []
        for stage in GENERATION_STAGES:
            output_sha256 = stage_rows[stage].output_sha256
            if output_sha256 is None:
                raise ConflictError("Generation is incomplete: a stage output hash is missing.")
            stage_hashes.append(output_sha256)
        expected_hash = calculate_generation_hash(stage_hashes)
        if gen.generation_sha256 != expected_hash:
            raise ConflictError("Generation hash does not match its completed stage outputs.")
        return gen

    async def _lock_document(self, document_id: uuid.UUID) -> Document:
        result = await self.session.execute(
            select(Document)
            .where(Document.id == document_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError(f"Document {document_id} not found")
        return doc

    async def activate(
        self, generation_id: uuid.UUID, expected_active_generation_id: Optional[uuid.UUID] = None, *, commit: bool = True
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
        revision_set = await self.session.get(DocumentRevisionSet, generation.revision_set_id)
        if not revision_set or revision_set.document_id != document.id:
            raise ConflictError("Generation revision set does not belong to the document.")
        if revision_set.status not in {"build_authorized", "approved"}:
            raise ConflictError("Generation revision set is not authorized for activation.")
        revision_set.status = "approved"

        if previous is not None:
            previous.state = "superseded"
            previous.superseded_at = datetime.now(UTC)
            if previous.revision_set_id != generation.revision_set_id:
                prev_set = await self.session.get(DocumentRevisionSet, previous.revision_set_id)
                if prev_set and prev_set.status in {"approved", "build_authorized"}:
                    prev_set.status = "superseded"

        document.status = "ready"
        document.index_generation += 1
        await self._project_legacy_pages(generation.id)
        await AuditService(self.session).record(
            actor_user_id=None,
            action="document_generation.activate",
            object_type="document_index_generation",
            object_id=generation.id,
            patient_id=document.patient_id,
            outcome="allowed",
            trace_id=new_trace_id(),
            metadata={
                "document_id": str(document.id),
                "revision_set_id": str(generation.revision_set_id),
            },
        )
        if commit:
            await self.session.commit()
        else:
            await self.session.flush()
        return ActivationResult(active_generation_id=generation.id, approved_revision_set_id=generation.revision_set_id)

    async def _project_legacy_pages(self, generation_id: uuid.UUID) -> None:
        result = await self.session.execute(
            select(DocumentChunk.page_id, DocumentChunk.page_revision_id)
            .where(
                DocumentChunk.generation_id == generation_id,
                DocumentChunk.page_revision_id.is_not(None),
            )
            .distinct()
        )
        for page_id, page_revision_id in result.all():
            page = await self.session.get(DocumentPage, page_id)
            page_revision = await self.session.get(DocumentPageRevision, page_revision_id)
            if page is not None and page_revision is not None:
                page.ocr_text = page_revision.corrected_text
                page.ocr_confidence = page_revision.confidence

    async def fail(self, generation_id: uuid.UUID, error_code: str, error_detail: str = "", *, commit: bool = True) -> None:
        gen = await self.session.get(DocumentIndexGeneration, generation_id)
        if gen:
            gen.state = "failed"
            gen.failed_at = datetime.now(UTC)
            gen.failure_code = error_code
            gen.failure_detail = error_detail
            if commit:
                await self.session.commit()
            else:
                await self.session.flush()

    async def rollback(
        self,
        *,
        document_id: uuid.UUID,
        target_generation_id: uuid.UUID,
        actor_id: uuid.UUID,
        expected_active_generation_id: Optional[uuid.UUID] = None,
        reason: str = "",
        commit: bool = True,
    ) -> ActivationResult:
        if expected_active_generation_id is None:
            raise ConflictError("Rollback requires the expected active generation pointer.")
        if actor_id is None:
            raise ValueError("Rollback requires an actor.")
        if len(reason.strip()) < 3:
            raise ValueError("Rollback requires a reason.")

        document = await self._lock_document(document_id)
        if document.active_index_generation_id != expected_active_generation_id:
            raise ConflictError("Stale active pointer for rollback.")

        target = await self.session.get(DocumentIndexGeneration, target_generation_id)
        if not target or target.document_id != document_id:
            raise ConflictError("Invalid target generation.")
        if target.state not in {"active", "superseded"}:
            raise ConflictError("Rollback target is not a completed generation.")
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
        await self._project_legacy_pages(target.id)
        await AuditService(self.session).record(
            actor_user_id=actor_id,
            action="document_generation.rollback",
            object_type="document_index_generation",
            object_id=target.id,
            patient_id=document.patient_id,
            outcome="allowed",
            trace_id=new_trace_id(),
            metadata={
                "document_id": str(document.id),
                "displaced_generation_id": str(previous.id) if previous else None,
                "reason": reason.strip(),
            },
        )
        if commit:
            await self.session.commit()
        return ActivationResult(active_generation_id=target.id, approved_revision_set_id=target.revision_set_id)

    async def retry(
        self, document_id: uuid.UUID, generation_id: uuid.UUID, actor_id: uuid.UUID, *, commit: bool = True
    ) -> DocumentIndexGeneration:
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
        await self.session.flush()
        if commit:
            await self.session.commit()
            await self.session.refresh(new_gen)
        return new_gen
