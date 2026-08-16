from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.errors import ConflictError, NotFoundError
from hospital_ai.db.clinical_documents import (
    DocumentDraftHead,
    DocumentIndexGeneration,
    DocumentPageRevision,
    DocumentRevisionEvent,
    DocumentRevisionPage,
    DocumentRevisionSet,
    OcrBlock,
    OcrLine,
    OcrSpan,
)
from hospital_ai.db.models import Document
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
    lock_version: Optional[int] = None


@dataclass(frozen=True)
class RevisionSetResult:
    revision_set_id: uuid.UUID
    document_id: uuid.UUID
    revision_number: int
    status: str
    created_by_user_id: uuid.UUID
    created_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    approved_by_user_id: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None


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
    lock_version: Optional[int] = None
    reason: str = ""


@dataclass(frozen=True)
class GenerationAccepted:
    generation_id: uuid.UUID
    state: str


def enqueue_build_generation_job(generation_id: uuid.UUID) -> None:
    from hospital_ai.workers.queue import enqueue_build_generation

    enqueue_build_generation(generation_id)


class RevisionService:
    def __init__(self, session: AsyncSession, settings: Optional[Settings] = None) -> None:
        self.session = session
        self.settings = settings or get_settings()

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
        selected_id = head.selected_pages.get(str(page_number))
        if selected_id != str(parent_revision_id):
            raise ConflictError("Parent revision must be the current draft head for this page.")
        parent = await self.session.get(DocumentPageRevision, parent_revision_id)
        if not parent or parent.document_id != document_id or parent.page_number != page_number:
            raise NotFoundError("Parent revision not found or mismatch.")
        if parent.status not in {"machine_draft", "human_draft"}:
            raise ConflictError("Only a machine or human draft can be edited.")
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
        parent = await self.session.get(DocumentPageRevision, parent_id)
        if not parent:
            raise NotFoundError("Parent revision not found.")
        alignment_status = "aligned" if parent.corrected_text == text else "stale"

        blocks = list(
            await self.session.scalars(
                select(OcrBlock)
                .where(OcrBlock.page_revision_id == parent_id)
                .order_by(OcrBlock.reading_order, OcrBlock.id)
            )
        )
        block_ids: dict[uuid.UUID, uuid.UUID] = {}
        for block in blocks:
            cloned_id = uuid.uuid4()
            block_ids[block.id] = cloned_id
            self.session.add(
                OcrBlock(
                    id=cloned_id,
                    page_revision_id=revision_id,
                    text_start_offset=block.text_start_offset,
                    text_end_offset=block.text_end_offset,
                    polygon=dict(block.polygon) if block.polygon else None,
                    confidence=block.confidence,
                    reading_order=block.reading_order,
                    alignment_status=alignment_status,
                )
            )

        lines = list(
            await self.session.scalars(
                select(OcrLine).where(OcrLine.page_revision_id == parent_id).order_by(OcrLine.reading_order, OcrLine.id)
            )
        )
        line_ids: dict[uuid.UUID, uuid.UUID] = {}
        for line in lines:
            cloned_block_id = block_ids.get(line.block_id)
            if cloned_block_id is None:
                raise ConflictError("OCR geometry lineage is incomplete.")
            cloned_id = uuid.uuid4()
            line_ids[line.id] = cloned_id
            self.session.add(
                OcrLine(
                    id=cloned_id,
                    block_id=cloned_block_id,
                    page_revision_id=revision_id,
                    text_start_offset=line.text_start_offset,
                    text_end_offset=line.text_end_offset,
                    polygon=dict(line.polygon) if line.polygon else None,
                    confidence=line.confidence,
                    reading_order=line.reading_order,
                    alignment_status=alignment_status,
                )
            )

        spans = list(
            await self.session.scalars(
                select(OcrSpan).where(OcrSpan.page_revision_id == parent_id).order_by(OcrSpan.reading_order, OcrSpan.id)
            )
        )
        for span in spans:
            cloned_line_id = line_ids.get(span.line_id)
            if cloned_line_id is None:
                raise ConflictError("OCR geometry lineage is incomplete.")
            self.session.add(
                OcrSpan(
                    id=uuid.uuid4(),
                    line_id=cloned_line_id,
                    page_revision_id=revision_id,
                    text_start_offset=span.text_start_offset,
                    text_end_offset=span.text_end_offset,
                    polygon=dict(span.polygon) if span.polygon else None,
                    confidence=span.confidence,
                    reading_order=span.reading_order,
                    alignment_status=alignment_status,
                    normalized_text=span.normalized_text,
                    source_engine_metadata=(dict(span.source_engine_metadata) if span.source_engine_metadata else None),
                )
            )
        await self.session.flush()

    async def _geometry_alignment_state(self, page_revision_id: uuid.UUID) -> str:
        statuses: list[str] = []
        for model in (OcrBlock, OcrLine, OcrSpan):
            statuses.extend(
                list(
                    await self.session.scalars(
                        select(model.alignment_status).where(model.page_revision_id == page_revision_id)
                    )
                )
            )
        if "stale" in statuses:
            return "stale"
        if "partially_aligned" in statuses:
            return "partially_aligned"
        return "aligned"

    async def _revision_set_hash(self, revision_set_id: uuid.UUID) -> str:
        revision_set = await self.session.get(DocumentRevisionSet, revision_set_id)
        if not revision_set:
            raise NotFoundError("Revision set not found.")
        result = await self.session.execute(
            select(DocumentRevisionPage, DocumentPageRevision)
            .join(DocumentPageRevision, DocumentPageRevision.id == DocumentRevisionPage.page_revision_id)
            .where(DocumentRevisionPage.revision_set_id == revision_set_id)
            .order_by(DocumentRevisionPage.page_number)
        )
        pages = []
        for revision_page, page_revision in result.all():
            pages.append(
                {
                    "page_number": revision_page.page_number,
                    "page_revision_id": str(page_revision.id),
                    "content_sha256": page_revision.content_sha256,
                    "geometry_alignment_state": await self._geometry_alignment_state(page_revision.id),
                }
            )
        payload = {
            "schema_version": "cdi-v2-revision-set-v1",
            "document_id": str(revision_set.document_id),
            "pages": pages,
        }
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

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

    async def save_page(
        self, document_id: uuid.UUID, page_number: int, command: SavePageCommand, *, commit: bool = True
    ) -> DraftMutationResult:
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
        if commit:
            await self.session.commit()
        return DraftMutationResult(revision.id, head.lock_version, page_number, command.text, revision.status)

    async def submit(self, document_id: uuid.UUID, command: SubmitCommand, *, commit: bool = True) -> RevisionSetResult:
        head = await self._lock_draft_head(document_id)
        if command.lock_version is not None and head.lock_version != command.lock_version:
            raise ConflictError("Draft changed during submit.")
        if not head.selected_pages:
            raise ConflictError("Cannot submit a draft without selected pages.")
        document = await self._lock_document(document_id)
        selected_items = sorted(head.selected_pages.items(), key=lambda item: int(item[0]))
        if document.page_count is not None and [int(page) for page, _ in selected_items] != list(
            range(1, document.page_count + 1)
        ):
            raise ConflictError("Draft must select exactly one current revision for every document page.")
        for page_number, revision_id in selected_items:
            page_revision = await self.session.get(DocumentPageRevision, uuid.UUID(str(revision_id)))
            if (
                not page_revision
                or page_revision.document_id != document_id
                or page_revision.page_number != int(page_number)
            ):
                raise ConflictError("Draft head contains an invalid page revision.")
            if page_revision.status not in {"machine_draft", "human_draft"}:
                raise ConflictError("Only machine or human drafts can be submitted.")
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
        for p_num, rev_id in selected_items:
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
        if commit:
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
        if rev_set.status != "submitted":
            raise ConflictError("Only a submitted revision set can be reviewed.")
        return rev_set

    async def _lock_document(self, document_id: uuid.UUID) -> Document:
        doc = await self.session.get(Document, document_id, with_for_update=True)
        if not doc:
            doc = await self.session.get(Document, document_id)
            if not doc:
                raise NotFoundError("Document not found.")
        return doc

    async def approve(
        self,
        revision_set_id: uuid.UUID,
        command: ApproveRevisionCommand,
        *,
        commit: bool = True,
        enqueue: bool = True,
    ) -> GenerationAccepted:
        revision_set = await self._lock_submitted_set(revision_set_id)
        document = await self._lock_document(revision_set.document_id)
        self_approval_allowed = (
            self.settings.demo_mode and self.settings.allow_self_approval_for_synthetic_data and document.is_synthetic
        )
        if revision_set.created_by_user_id == command.actor_id and not self_approval_allowed:
            await AuditService(self.session).record(
                actor_user_id=command.actor_id,
                action="document_revision.approve",
                object_type="document",
                object_id=document.id,
                outcome="failed",
                trace_id="0",
            )
            raise ConflictError("Self-approval is not permitted for this revision set.")
        revision_set.status = "build_authorized"
        revision_set.approved_by_user_id = command.actor_id
        now_ts = datetime.now(UTC)
        revision_set.approved_at = now_ts
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
        if commit:
            await self.session.commit()
        if enqueue:
            enqueue_build_generation_job(generation.id)
        return GenerationAccepted(generation.id, "building")

    async def reject(
        self, revision_set_id: uuid.UUID, command: RejectCommand, *, commit: bool = True
    ) -> RevisionSetResult:
        revision_set = await self._lock_submitted_set(revision_set_id)
        revision_set.status = "rejected"
        await self._append_event(
            revision_set.document_id, command.actor_id, "revision_set_rejected", [], reason=command.reason
        )
        await AuditService(self.session).record(
            actor_user_id=command.actor_id,
            action="document_revision.reject",
            object_type="document",
            object_id=revision_set.document_id,
            outcome="allowed",
            trace_id="0",
        )
        if commit:
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

    async def restore(
        self,
        document_id: uuid.UUID,
        page_number: int,
        command: RestoreCommand,
        *,
        commit: bool = True,
    ) -> DraftMutationResult:
        head = await self._lock_draft_head(document_id)
        if command.lock_version is not None and head.lock_version != command.lock_version:
            raise ConflictError("Draft changed during restore.")
        target = await self.session.get(DocumentPageRevision, command.revision_id)
        if not target or target.document_id != document_id or target.page_number != page_number:
            raise NotFoundError("Target revision not found or mismatch.")
        selected_parent_str = head.selected_pages.get(str(page_number))
        parent_rev_id = uuid.UUID(str(selected_parent_str)) if selected_parent_str else target.id
        revision = DocumentPageRevision(
            document_id=document_id,
            page_number=page_number,
            parent_revision_id=parent_rev_id,
            extraction_run_id=target.extraction_run_id,
            revision_number=await self._next_page_revision_number(document_id, page_number),
            revision_type="human_edit",
            raw_text_snapshot=target.raw_text_snapshot,
            corrected_text=target.corrected_text,
            confidence=target.confidence,
            status="human_draft",
            created_by_user_id=command.actor_id,
            edit_reason=command.reason,
            content_sha256=target.content_sha256,
            version=1,
        )
        self.session.add(revision)
        await self.session.flush()
        await self._mark_geometry_after_edit(target.id, revision.id, target.corrected_text)
        head.selected_pages = {**head.selected_pages, str(page_number): str(revision.id)}
        head.lock_version += 1
        head.updated_by_user_id = command.actor_id
        await self._append_event(
            document_id, command.actor_id, "revision_restored", [revision.id], reason=command.reason
        )
        await AuditService(self.session).record(
            actor_user_id=command.actor_id,
            action="document_revision.restore",
            object_type="document",
            object_id=document_id,
            outcome="allowed",
            trace_id="0",
        )
        if commit:
            await self.session.commit()
        return DraftMutationResult(revision.id, head.lock_version, page_number, target.corrected_text, revision.status)

    async def compute_revision_set_hash(self, revision_set_id: uuid.UUID) -> str:
        """Compute the canonical content and geometry hash for a revision set."""
        return await self._revision_set_hash(revision_set_id)

    async def serialize_exact_evidence(self, document_id: uuid.UUID, page_revision_id: uuid.UUID) -> dict:
        """Serialize exact OCR geometry evidence for a page revision, rejecting stale geometry."""
        revision = await self.session.get(DocumentPageRevision, page_revision_id)
        if not revision or revision.document_id != document_id:
            raise NotFoundError("Revision not found or mismatch.")

        alignment_state = await self._geometry_alignment_state(page_revision_id)
        if alignment_state == "stale":
            raise ConflictError("Stale geometry cannot be serialized as exact evidence.")

        spans_result = await self.session.execute(
            select(OcrSpan)
            .where(OcrSpan.page_revision_id == page_revision_id)
            .order_by(OcrSpan.reading_order, OcrSpan.text_start_offset)
        )
        spans = spans_result.scalars().all()
        if any(span.alignment_status == "stale" for span in spans):
            raise ConflictError("Stale geometry cannot be serialized as exact evidence.")

        span_list = [
            {
                "span_id": str(span.id),
                "text_start_offset": span.text_start_offset,
                "text_end_offset": span.text_end_offset,
                "polygon": span.polygon,
                "confidence": span.confidence,
                "reading_order": span.reading_order,
                "alignment_status": span.alignment_status,
            }
            for span in spans
        ]

        return {
            "page_revision_id": str(revision.id),
            "document_id": str(revision.document_id),
            "page_number": revision.page_number,
            "content_sha256": revision.content_sha256,
            "alignment_state": alignment_state,
            "spans": span_list,
        }
