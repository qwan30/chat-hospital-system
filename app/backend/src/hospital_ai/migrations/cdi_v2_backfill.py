from __future__ import annotations

import hashlib
import logging
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.db.clinical_documents import (
    DocumentDraftHead,
    DocumentIndexGeneration,
    DocumentPageRevision,
    DocumentRevisionPage,
    DocumentRevisionSet,
)
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage
from hospital_ai.services.graph_rag import GraphEntity

logger = logging.getLogger(__name__)


@dataclass
class BackfillPolicy:
    autoapprove_synthetic: bool = False

    def may_autoapprove(self, document: Document) -> bool:
        return bool(document.is_synthetic) and self.autoapprove_synthetic


class BackfillBlocked(Exception):
    def __init__(self, failure_codes: list[str]) -> None:
        super().__init__(f"Backfill blocked due to failures: {failure_codes}")
        self.failure_codes = failure_codes


@dataclass
class LineageVerificationResult:
    passed: bool
    failure_codes: list[str] = field(default_factory=list)


@dataclass
class BackfillResult:
    machine_revision_ids: list[uuid.UUID]
    draft_head_id: Optional[uuid.UUID]
    submitted_set_id: Optional[uuid.UUID]
    generation_id: Optional[uuid.UUID]
    status: str = "completed"

    @classmethod
    def from_rows(
        cls,
        page_revisions: list[DocumentPageRevision],
        head: Optional[DocumentDraftHead],
        submitted: Optional[DocumentRevisionSet],
        generation: Optional[DocumentIndexGeneration],
    ) -> BackfillResult:
        return cls(
            machine_revision_ids=[r.id for r in page_revisions],
            draft_head_id=head.document_id if head else None,
            submitted_set_id=submitted.id if submitted else None,
            generation_id=generation.id if generation else None,
        )


class CdiV2Backfill:
    def __init__(self, session: AsyncSession, policy: Optional[BackfillPolicy] = None) -> None:
        self.session = session
        self.policy = policy or BackfillPolicy()

    async def _lock_document(self, document_id: uuid.UUID) -> Document:
        doc = await self.session.get(Document, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")
        return doc

    async def verify_legacy_lineage(self, document_id: uuid.UUID) -> LineageVerificationResult:
        doc = await self.session.get(Document, document_id)
        if not doc:
            return LineageVerificationResult(passed=False, failure_codes=["document_not_found"])

        failure_codes: set[str] = set()
        if not doc.indexed_source_sha256:
            failure_codes.add("missing_source_sha")

        res_pages = await self.session.execute(select(DocumentPage).where(DocumentPage.document_id == document_id))
        pages = list(res_pages.scalars().all())
        page_ids = {p.id for p in pages}

        res_chunks = await self.session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id))
        chunks = list(res_chunks.scalars().all())
        chunk_ids = {c.id for c in chunks}

        for chunk in chunks:
            if chunk.patient_id != doc.patient_id:
                failure_codes.add("wrong_patient_chunk")
            if chunk.page_id not in page_ids:
                failure_codes.add("orphan_chunk")

        res_entities = await self.session.execute(
            select(GraphEntity).where(GraphEntity.source_document_id == document_id)
        )
        entities = list(res_entities.scalars().all())
        for entity in entities:
            if entity.source_chunk_id not in chunk_ids:
                failure_codes.add("graph_entity_mismatch")

        sorted_codes = sorted(failure_codes)
        return LineageVerificationResult(passed=len(sorted_codes) == 0, failure_codes=sorted_codes)

    async def _machine_v1_from_document_pages(self, document: Document) -> list[DocumentPageRevision]:
        res = await self.session.execute(
            select(DocumentPageRevision)
            .where(
                DocumentPageRevision.document_id == document.id,
                DocumentPageRevision.revision_type == "machine_ocr",
            )
            .order_by(DocumentPageRevision.page_number)
        )
        existing = list(res.scalars().all())
        if existing:
            return existing

        res_pages = await self.session.execute(
            select(DocumentPage).where(DocumentPage.document_id == document.id).order_by(DocumentPage.page_number)
        )
        pages = list(res_pages.scalars().all())

        new_revs: list[DocumentPageRevision] = []
        for page in pages:
            content_text = page.ocr_text or ""
            content_sha = hashlib.sha256(content_text.encode("utf-8")).hexdigest()
            status = "approved" if self.policy.may_autoapprove(document) else "submitted"
            rev = DocumentPageRevision(
                id=uuid.uuid4(),
                document_id=document.id,
                page_number=page.page_number,
                revision_number=1,
                revision_type="machine_ocr",
                raw_text_snapshot=content_text,
                corrected_text=content_text,
                confidence=page.ocr_confidence or 1.0,
                status=status,
                created_by_user_id=document.uploaded_by,
                created_at=datetime.now(UTC),
                approved_by_user_id=document.uploaded_by if status == "approved" else None,
                approved_at=datetime.now(UTC) if status == "approved" else None,
                content_sha256=content_sha,
                version=1,
            )
            self.session.add(rev)
            new_revs.append(rev)

        if new_revs:
            await self.session.flush()
        return new_revs

    async def _upsert_draft_head(
        self, document: Document, page_revisions: list[DocumentPageRevision]
    ) -> DocumentDraftHead:
        head = await self.session.get(DocumentDraftHead, document.id)
        if head:
            return head

        page_map = {str(r.page_number): str(r.id) for r in page_revisions}
        head = DocumentDraftHead(
            document_id=document.id,
            selected_pages=page_map,
            lock_version=1,
            updated_by_user_id=document.uploaded_by,
        )
        self.session.add(head)
        await self.session.flush()
        return head

    async def _upsert_submitted_revision_set(self, document: Document, head: DocumentDraftHead) -> DocumentRevisionSet:
        res = await self.session.execute(
            select(DocumentRevisionSet)
            .where(DocumentRevisionSet.document_id == document.id)
            .order_by(DocumentRevisionSet.revision_number)
        )
        existing_sets = list(res.scalars().all())
        if existing_sets:
            return existing_sets[0]

        status = "approved" if self.policy.may_autoapprove(document) else "submitted"
        rev_set = DocumentRevisionSet(
            id=uuid.uuid4(),
            document_id=document.id,
            revision_number=1,
            status=status,
            created_by_user_id=document.uploaded_by,
            submitted_at=datetime.now(UTC),
            approved_by_user_id=document.uploaded_by if status == "approved" else None,
            approved_at=datetime.now(UTC) if status == "approved" else None,
        )
        self.session.add(rev_set)
        await self.session.flush()

        for p_num_str, rev_id_str in head.selected_pages.items():
            rev_page = DocumentRevisionPage(
                revision_set_id=rev_set.id,
                page_number=int(p_num_str),
                page_revision_id=uuid.UUID(rev_id_str),
            )
            self.session.add(rev_page)
        await self.session.flush()
        return rev_set

    async def _attach_verified_legacy_generation(
        self, document: Document, submitted: DocumentRevisionSet
    ) -> DocumentIndexGeneration:
        res = await self.session.execute(
            select(DocumentIndexGeneration)
            .where(DocumentIndexGeneration.document_id == document.id)
            .order_by(DocumentIndexGeneration.created_at)
        )
        existing_gens = list(res.scalars().all())
        if existing_gens:
            gen = existing_gens[0]
        else:
            sha256 = document.indexed_source_sha256 or hashlib.sha256(str(document.id).encode("utf-8")).hexdigest()
            gen = DocumentIndexGeneration(
                id=uuid.uuid4(),
                document_id=document.id,
                revision_set_id=submitted.id,
                state="active",
                revision_set_sha256=sha256,
                generation_sha256=sha256,
                created_at=datetime.now(UTC),
                started_at=datetime.now(UTC),
                activated_at=datetime.now(UTC),
            )
            self.session.add(gen)
            await self.session.flush()

            res_chunks = await self.session.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == document.id)
            )
            for chunk in res_chunks.scalars().all():
                chunk.generation_id = gen.id
                chunk.revision_set_id = submitted.id
            await self.session.flush()

        document.approved_revision_set_id = submitted.id
        document.active_index_generation_id = gen.id
        await self.session.flush()
        return gen

    async def _record_checkpoint(self, document_id: uuid.UUID, phase: str) -> None:
        logger.debug("Backfill checkpoint: doc=%s phase=%s", document_id, phase)

    async def run_document(self, document_id: uuid.UUID) -> BackfillResult:
        document = await self._lock_document(document_id)
        page_revisions = await self._machine_v1_from_document_pages(document)
        await self._record_checkpoint(document.id, "machine_revisions")
        head = await self._upsert_draft_head(document, page_revisions)
        await self._record_checkpoint(document.id, "draft_heads")
        submitted = await self._upsert_submitted_revision_set(document, head)
        await self._record_checkpoint(document.id, "submitted_sets")
        generation = None
        if self.policy.may_autoapprove(document):
            lineage = await self.verify_legacy_lineage(document.id)
            if not lineage.passed:
                raise BackfillBlocked(lineage.failure_codes)
            generation = await self._attach_verified_legacy_generation(document, submitted)
            await self._record_checkpoint(document.id, "legacy_generations")
        await self._record_checkpoint(document.id, "complete")
        await self.session.commit()
        return BackfillResult.from_rows(page_revisions, head, submitted, generation)

    async def compute_parity_report(self, document_ids: Optional[list[uuid.UUID]] = None) -> dict[str, Any]:
        query = select(Document)
        if document_ids:
            query = query.where(Document.id.in_(document_ids))
        res = await self.session.execute(query)
        docs = list(res.scalars().all())

        wrong_patient_count = 0
        superseded_generation_count = 0
        docs_output: list[dict[str, Any]] = []

        for doc in docs:
            lineage = await self.verify_legacy_lineage(doc.id)
            if "wrong_patient_chunk" in lineage.failure_codes:
                wrong_patient_count += 1
            if doc.active_index_generation_id is not None:
                gen = await self.session.get(DocumentIndexGeneration, doc.active_index_generation_id)
                if not gen or gen.state != "active":
                    superseded_generation_count += 1

            docs_output.append(
                {
                    "document_id": str(doc.id),
                    "source_sha256": doc.indexed_source_sha256,
                    "approved_revision_set_id": str(doc.approved_revision_set_id)
                    if doc.approved_revision_set_id
                    else None,
                    "active_index_generation_id": str(doc.active_index_generation_id)
                    if doc.active_index_generation_id
                    else None,
                    "passed_lineage": lineage.passed,
                    "failure_codes": lineage.failure_codes,
                }
            )

        try:
            git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            git_sha = "unknown"

        status = "passed" if (wrong_patient_count == 0 and superseded_generation_count == 0) else "failed"
        return {
            "status": status,
            "wrong_patient_count": wrong_patient_count,
            "superseded_generation_count": superseded_generation_count,
            "git_sha": git_sha,
            "documents": docs_output,
        }
