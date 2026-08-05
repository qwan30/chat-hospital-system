from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.errors import ConflictError, NotFoundError
from hospital_ai.db.models import Document
from hospital_ai.db.clinical_documents import (
    DocumentDraftHead,
    DocumentIndexGeneration,
    DocumentPageRevision,
    DocumentRevisionEvent,
    DocumentRevisionPage,
    DocumentRevisionSet,
)
from hospital_ai.services.audit import AuditService


@dataclass(frozen=True)
class SavePageCommand:
    text: str
    parent_revision_id: uuid.UUID
    lock_version: int
    actor_id: uuid.UUID
    edit_reason: str = ""


@dataclass(frozen=True)
class DraftMutationResult:
    page_revision_id: uuid.UUID
    lock_version: int
    page_number: int = 0
    text: str = ""
    status: str = "human_draft"


@dataclass(frozen=True)
class SubmitCommand:
    actor_id: uuid.UUID
    lock_version: int | None = None


@dataclass(frozen=True)
class RevisionSetResult:
    revision_set_id: uuid.UUID
    document_id: uuid.UUID
    revision_number: int
    status: str
    created_by_user_id: uuid.UUID
    created_at: datetime | None = None
    submitted_at: datetime | None = None
    approved_by_user_id: uuid.UUID | None = None
    approved_at: datetime | None = None


@dataclass(frozen=True)
class ApproveRevisionCommand:
    actor_id: uuid.UUID
    demo_mode: bool = False


@dataclass(frozen=True)
class RejectCommand:
    actor_id: uuid.UUID
    reason: str = ""


@dataclass(frozen=True)
class RestoreCommand:
    revision_id: uuid.UUID
    actor_id: uuid.UUID
    lock_version: int | None = None
    reason: str = ""


@dataclass(frozen=True)
class GenerationAccepted:
    generation_id: uuid.UUID
    state: str


def enqueue_build_generation_job(generation_id: uuid.UUID) -> None:
    from hospital_ai.workers.queue import enqueue_build_generation
    enqueue_build_generation(generation_id)


class RevisionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _lock_draft_head(self, document_id: uuid.UUID) -> DocumentDraftHead:
        head = await self.session.get(DocumentDraftHead, document_id, with_for_update=True)
        if not head:
            # Fallback without lock if in transaction that doesn't support or if missing
            head = await self.session.get(DocumentDraftHead, document_id)
            if not head:
                raise NotFoundError("Draft head not found for document.")
        return head

    async def _require_selected_parent(
        self, document_id: uuid.UUID, page_number: int, parent_revision_id: uuid.UUID, head: DocumentDraftHead
    ) -> DocumentPageRevision:
        parent = await self.session.get(DocumentPageRevision, parent_revision_id)
        if not parent or parent.document_id != document_id or parent.page_number != page_number:
            raise NotFoundError("Parent revision not found or mismatch.")
        return parent

    async def _next_page_revision_number(self, document_id: uuid.UUID, page_number: int) -> int:
        stmt = select(func.max(DocumentPageRevision.revision_number)).where(
            DocumentPageRevision.document_id == document_id,
            DocumentPageRevision.page_number == page_number,
        )
        current = await self.session.scalar(stmt)
        return (current or 0) + 1

    async def _next_revision_set_number(self, document_id: uuid.UUID) -> int:
        stmt = select(func.max(DocumentRevisionSet.revision_number)).where(
            DocumentRevisionSet.document_id == document_id
        )
        current = await self.session.scalar(stmt)
        return (current or 0) + 1

    async def _mark_geometry_after_edit(self, parent_id: uuid.UUID, revision_id: uuid.UUID, text: str) -> None:
        pass

    async def _revision_set_hash(self, revision_set_id: uuid.UUID) -> str:
        return hashlib.sha256(str(revision_set_id).encode("utf-8")).hexdigest()

    async def _append_event(
        self,
        document_id: uuid.UUID,
        actor_id: uuid.UUID,
        action: str,
        changed_ids: list[uuid.UUID],
        reason: Optional[str] = None,
    ) -> None:
        event = DocumentRevisionEvent(
            document_id=document_id,
            actor_user_id=actor_id,
            action=action,
            trace_id="0",
            changed_page_ids=[str(u) for u in changed_ids],
            reason=reason,
        )
        self.session.add(event)

    async def save_page(self, document_id: uuid.UUID, page_number: int, command: SavePageCommand) -> DraftMutationResult:
        head = await self._lock_draft_head(document_id)
        if head.lock_version != command.lock_version:
            await AuditService(self.session).record(
                actor_user_id=command.actor_id,
                action="document_revision.page.save",
                object_type="document",
                object_id=document_id,
                outcome="failed",
                trace_id="0",
            )
            raise ConflictError("Draft changed; compare the latest revision before retrying.")
        parent = await self._require_selected_parent(document_id, page_number, command.parent_revision_id, head)
        content_sha256 = hashlib.sha256(command.text.encode("utf-8")).hexdigest()
        revision = DocumentPageRevision(
            document_id=document_id,
            page_number=page_number,
            parent_revision_id=parent.id,
            extraction_run_id=parent.extraction_run_id,
            revision_number=await self._next_page_revision_number(document_id, page_number),
            revision_type="human_edit",
            raw_text_snapshot=parent.raw_text_snapshot,
            corrected_text=command.text,
            confidence=parent.confidence,
            status="human_draft",
            created_by_user_id=command.actor_id,
            edit_reason=command.edit_reason,
            content_sha256=content_sha256,
            version=1,
        )
        self.session.add(revision)
        await self.session.flush()
        head.selected_pages = {**head.selected_pages, str(page_number): str(revision.id)}
        head.lock_version += 1
        head.updated_by_user_id = command.actor_id
        await self._mark_geometry_after_edit(parent.id, revision.id, command.text)
        await self._append_event(document_id, command.actor_id, "page_saved", [revision.id], reason=command.edit_reason)
        await AuditService(self.session).record(
            actor_user_id=command.actor_id,
            action="document_revision.page.save",
            object_type="document",
            object_id=document_id,
            outcome="allowed",
            trace_id="0",
        )
        await self.session.commit()
        return DraftMutationResult(revision.id, head.lock_version, page_number, command.text, revision.status)

    async def submit(self, document_id: uuid.UUID, command: SubmitCommand) -> RevisionSetResult:
        head = await self._lock_draft_head(document_id)
        if command.lock_version is not None and head.lock_version != command.lock_version:
            raise ConflictError("Draft changed during submit.")
        rev_number = await self._next_revision_set_number(document_id)
        now_ts = datetime.now(UTC)
        rev_set = DocumentRevisionSet(
            document_id=document_id,
            revision_number=rev_number,
            status="submitted",
            created_by_user_id=command.actor_id,
            submitted_at=now_ts,
            created_at=now_ts,
        )
        self.session.add(rev_set)
        await self.session.flush()
        for p_num, rev_id in head.selected_pages.items():
            rp = DocumentRevisionPage(
                revision_set_id=rev_set.id,
                page_number=int(p_num),
                page_revision_id=uuid.UUID(str(rev_id)),
            )
            self.session.add(rp)
        await self._append_event(document_id, command.actor_id, "draft_submitted", [], reason="Submit")
        await AuditService(self.session).record(
            actor_user_id=command.actor_id,
            action="document_revision.submit",
            object_type="document",
            object_id=document_id,
            outcome="allowed",
            trace_id="0",
        )
        await self.session.commit()
        return RevisionSetResult(
            revision_set_id=rev_set.id,
            document_id=document_id,
            revision_number=rev_set.revision_number,
            status=rev_set.status,
            created_by_user_id=rev_set.created_by_user_id,
            created_at=rev_set.created_at,
            submitted_at=rev_set.submitted_at,
            approved_by_user_id=rev_set.approved_by_user_id,
            approved_at=rev_set.approved_at,
        )

    async def _lock_submitted_set(self, revision_set_id: uuid.UUID) -> DocumentRevisionSet:
        rev_set = await self.session.get(DocumentRevisionSet, revision_set_id, with_for_update=True)
        if not rev_set:
            rev_set = await self.session.get(DocumentRevisionSet, revision_set_id)
            if not rev_set:
                raise NotFoundError("Revision set not found.")
        return rev_set

    async def _lock_document(self, document_id: uuid.UUID) -> Document:
        doc = await self.session.get(Document, document_id, with_for_update=True)
        if not doc:
            doc = await self.session.get(Document, document_id)
            if not doc:
                raise NotFoundError("Document not found.")
        return doc

    async def approve(self, revision_set_id: uuid.UUID, command: ApproveRevisionCommand) -> GenerationAccepted:
        revision_set = await self._lock_submitted_set(revision_set_id)
        document = await self._lock_document(revision_set.document_id)
        if not command.demo_mode:
            if revision_set.created_by_user_id == command.actor_id:
                await AuditService(self.session).record(
                    actor_user_id=command.actor_id,
                    action="document_revision.approve",
                    object_type="document",
                    object_id=document.id,
                    outcome="failed",
                    trace_id="0",
                )
                raise ConflictError("The editor cannot approve this production revision set.")
        revision_set.status = "approved"
        revision_set.approved_by_user_id = command.actor_id
        now_ts = datetime.now(UTC)
        revision_set.approved_at = now_ts
        document.approved_revision_set_id = revision_set.id
        generation = DocumentIndexGeneration(
            document_id=document.id,
            revision_set_id=revision_set.id,
            state="building",
            revision_set_sha256=await self._revision_set_hash(revision_set.id),
        )
        self.session.add(generation)
        await self._append_event(document.id, command.actor_id, "revision_set_approved", [])
        await AuditService(self.session).record(
            actor_user_id=command.actor_id,
            action="document_revision.approve",
            object_type="document",
            object_id=document.id,
            outcome="allowed",
            trace_id="0",
        )
        await self.session.commit()
        enqueue_build_generation_job(generation.id)
        return GenerationAccepted(generation.id, "building")

    async def reject(self, revision_set_id: uuid.UUID, command: RejectCommand) -> RevisionSetResult:
        revision_set = await self._lock_submitted_set(revision_set_id)
        revision_set.status = "rejected"
        await self._append_event(revision_set.document_id, command.actor_id, "revision_set_rejected", [], reason=command.reason)
        await AuditService(self.session).record(
            actor_user_id=command.actor_id,
            action="document_revision.reject",
            object_type="document",
            object_id=revision_set.document_id,
            outcome="allowed",
            trace_id="0",
        )
        await self.session.commit()
        return RevisionSetResult(
            revision_set_id=revision_set.id,
            document_id=revision_set.document_id,
            revision_number=revision_set.revision_number,
            status=revision_set.status,
            created_by_user_id=revision_set.created_by_user_id,
            created_at=revision_set.created_at,
            submitted_at=revision_set.submitted_at,
            approved_by_user_id=revision_set.approved_by_user_id,
            approved_at=revision_set.approved_at,
        )

    async def restore(self, document_id: uuid.UUID, page_number: int, command: RestoreCommand) -> DraftMutationResult:
        head = await self._lock_draft_head(document_id)
        if command.lock_version is not None and head.lock_version != command.lock_version:
            raise ConflictError("Draft changed during restore.")
        target = await self.session.get(DocumentPageRevision, command.revision_id)
        if not target:
            raise NotFoundError("Target revision not found.")
        revision = DocumentPageRevision(
            document_id=document_id,
            page_number=page_number,
            parent_revision_id=target.id,
            extraction_run_id=target.extraction_run_id,
            revision_number=await self._next_page_revision_number(document_id, page_number),
            revision_type="restored",
            raw_text_snapshot=target.raw_text_snapshot,
            corrected_text=target.corrected_text,
            confidence=target.confidence,
            status="restored",
            created_by_user_id=command.actor_id,
            edit_reason=command.reason,
            content_sha256=target.content_sha256,
            version=1,
        )
        self.session.add(revision)
        await self.session.flush()
        head.selected_pages = {**head.selected_pages, str(page_number): str(revision.id)}
        head.lock_version += 1
        head.updated_by_user_id = command.actor_id
        await self._append_event(document_id, command.actor_id, "revision_restored", [revision.id], reason=command.reason)
        await AuditService(self.session).record(
            actor_user_id=command.actor_id,
            action="document_revision.restore",
            object_type="document",
            object_id=document_id,
            outcome="allowed",
            trace_id="0",
        )
        await self.session.commit()
        return DraftMutationResult(revision.id, head.lock_version, page_number, target.corrected_text, revision.status)
