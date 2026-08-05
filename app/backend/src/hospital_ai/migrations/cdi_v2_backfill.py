from __future__ import annotations

import hashlib
import json
import logging
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.security import new_trace_id
from hospital_ai.db.clinical_documents import (
    DocumentDraftHead,
    DocumentIndexGeneration,
    DocumentPageRevision,
    DocumentRevisionPage,
    DocumentRevisionSet,
)
from hospital_ai.db.clinical_graph import LegacyGraphEntity, LegacyGraphRelation
from hospital_ai.db.models import AuditLog, Document, DocumentChunk, DocumentPage

logger = logging.getLogger(__name__)
CHECKPOINT_ACTION = "cdi_v2_backfill.checkpoint"


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
    def __init__(
        self,
        session: AsyncSession,
        policy: Optional[BackfillPolicy] = None,
        *,
        dry_run: bool = False,
    ) -> None:
        self.session = session
        self.policy = policy or BackfillPolicy()
        self.dry_run = dry_run

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

    async def _completed_phases(self, document_id: uuid.UUID) -> set[str]:
        result = await self.session.execute(
            select(AuditLog).where(
                AuditLog.action == CHECKPOINT_ACTION,
                AuditLog.object_id == document_id,
            )
        )
        return {
            str(row.meta.get("phase"))
            for row in result.scalars().all()
            if isinstance(row.meta, dict) and row.meta.get("phase")
        }

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
            select(LegacyGraphEntity).where(LegacyGraphEntity.source_document_id == document_id)
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
        completed = await self._completed_phases(document_id)
        if phase in completed:
            return
        self.session.add(
            AuditLog(
                actor_user_id=None,
                action=CHECKPOINT_ACTION,
                object_type="document_backfill",
                object_id=document_id,
                outcome="allowed",
                trace_id=new_trace_id(),
                meta={"phase": phase, "schema_version": 1},
            )
        )
        await self.session.flush()

    async def _commit_phase(self) -> None:
        if not self.dry_run:
            await self.session.commit()

    async def _existing_generation(self, document_id: uuid.UUID) -> Optional[DocumentIndexGeneration]:
        return await self.session.scalar(
            select(DocumentIndexGeneration)
            .where(DocumentIndexGeneration.document_id == document_id)
            .order_by(DocumentIndexGeneration.created_at)
        )

    async def run_document(self, document_id: uuid.UUID) -> BackfillResult:
        document = await self._lock_document(document_id)
        completed = await self._completed_phases(document.id)

        if "machine_revisions" not in completed:
            page_revisions = await self._machine_v1_from_document_pages(document)
            await self._record_checkpoint(document.id, "machine_revisions")
            completed.add("machine_revisions")
            await self._commit_phase()
        else:
            page_revisions = list(
                (
                    await self.session.scalars(
                        select(DocumentPageRevision)
                        .where(
                            DocumentPageRevision.document_id == document.id,
                            DocumentPageRevision.revision_type == "machine_ocr",
                        )
                        .order_by(DocumentPageRevision.page_number)
                    )
                ).all()
            )
            if not page_revisions:
                raise ValueError("Backfill checkpoint exists but machine revisions are missing")

        if "draft_heads" not in completed:
            head = await self._upsert_draft_head(document, page_revisions)
            await self._record_checkpoint(document.id, "draft_heads")
            completed.add("draft_heads")
            await self._commit_phase()
        else:
            head = await self.session.get(DocumentDraftHead, document.id)
            if head is None:
                raise ValueError("Backfill checkpoint exists but draft head is missing")

        if "submitted_sets" not in completed:
            submitted = await self._upsert_submitted_revision_set(document, head)
            await self._record_checkpoint(document.id, "submitted_sets")
            completed.add("submitted_sets")
            await self._commit_phase()
        else:
            submitted = await self.session.scalar(
                select(DocumentRevisionSet)
                .where(DocumentRevisionSet.document_id == document.id)
                .order_by(DocumentRevisionSet.revision_number)
            )
            if submitted is None:
                raise ValueError("Backfill checkpoint exists but submitted revision set is missing")

        generation = None
        if self.policy.may_autoapprove(document):
            if "legacy_generations" not in completed:
                lineage = await self.verify_legacy_lineage(document.id)
                if not lineage.passed:
                    raise BackfillBlocked(lineage.failure_codes)
                generation = await self._attach_verified_legacy_generation(document, submitted)
                await self._record_checkpoint(document.id, "legacy_generations")
                completed.add("legacy_generations")
                await self._commit_phase()
            else:
                generation = await self._existing_generation(document.id)
                if generation is None:
                    raise ValueError("Backfill checkpoint exists but legacy generation is missing")
        await self._record_checkpoint(document.id, "complete")
        await self._commit_phase()
        result = BackfillResult.from_rows(page_revisions, head, submitted, generation)
        if self.dry_run:
            await self.session.rollback()
        return result

    async def compute_parity_report(self, document_ids: Optional[list[uuid.UUID]] = None) -> dict[str, Any]:
        query = select(Document)
        if document_ids:
            query = query.where(Document.id.in_(document_ids))
        res = await self.session.execute(query)
        docs = list(res.scalars().all())

        wrong_patient_count = 0
        superseded_generation_count = 0
        lineage_failure_count = 0
        docs_output: list[dict[str, Any]] = []

        try:
            git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            git_sha = "unknown"

        for doc in docs:
            lineage = await self.verify_legacy_lineage(doc.id)
            if not lineage.passed:
                lineage_failure_count += 1
            if "wrong_patient_chunk" in lineage.failure_codes:
                wrong_patient_count += 1
            if doc.active_index_generation_id is not None:
                gen = await self.session.get(DocumentIndexGeneration, doc.active_index_generation_id)
                if not gen or gen.state != "active":
                    superseded_generation_count += 1

            pages = list(
                (await self.session.scalars(select(DocumentPage).where(DocumentPage.document_id == doc.id))).all()
            )
            page_by_id = {page.id: page for page in pages}
            chunks = list(
                (await self.session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))).all()
            )
            revisions = list(
                (
                    await self.session.scalars(
                        select(DocumentPageRevision).where(DocumentPageRevision.document_id == doc.id)
                    )
                ).all()
            )
            revision_sets = list(
                (
                    await self.session.scalars(
                        select(DocumentRevisionSet).where(DocumentRevisionSet.document_id == doc.id)
                    )
                ).all()
            )
            revision_set_by_id = {revision_set.id: revision_set for revision_set in revision_sets}
            generations = list(
                (
                    await self.session.scalars(
                        select(DocumentIndexGeneration).where(DocumentIndexGeneration.document_id == doc.id)
                    )
                ).all()
            )
            generation_by_id = {generation.id: generation for generation in generations}
            chunk_ids = [chunk.id for chunk in chunks]
            entities = list(
                (
                    await self.session.scalars(
                        select(LegacyGraphEntity).where(LegacyGraphEntity.source_document_id == doc.id)
                    )
                ).all()
            )
            relations = []
            if chunk_ids:
                relations = list(
                    (
                        await self.session.scalars(
                            select(LegacyGraphRelation).where(LegacyGraphRelation.source_chunk_id.in_(chunk_ids))
                        )
                    ).all()
                )

            lexical_vector_ids: list[dict[str, Any]] = []
            citation_locators: list[dict[str, Any]] = []
            authorization_outcomes: list[dict[str, Any]] = []
            for chunk in chunks:
                page = page_by_id.get(chunk.page_id)
                generation = generation_by_id.get(chunk.generation_id)
                revision_set = revision_set_by_id.get(chunk.revision_set_id)
                patient_match = chunk.patient_id == doc.patient_id
                generation_active = bool(
                    generation and doc.active_index_generation_id == generation.id and generation.state == "active"
                )
                revision_approved = bool(revision_set and revision_set.status == "approved")
                document_active = bool(doc.deleted_at is None and doc.status in {"ready", "ready_with_warnings"})
                included = bool(
                    document_active
                    and patient_match
                    and page
                    and page.deleted_at is None
                    and chunk.deleted_at is None
                    and generation_active
                    and revision_approved
                )
                lexical_vector_ids.append(
                    {
                        "chunk_id": str(chunk.id),
                        "lexical_row_id": str(chunk.id),
                        "vector_row_id": str(chunk.id) if chunk.embedding is not None else None,
                        "rank": None,
                        "rank_available": False,
                    }
                )
                citation_locators.append(
                    {
                        "chunk_id": str(chunk.id),
                        "document_id": str(doc.id),
                        "page_number": page.page_number if page else None,
                        "start_offset": chunk.text_start_offset,
                        "end_offset": chunk.text_end_offset,
                    }
                )
                authorization_outcomes.append(
                    {
                        "chunk_id": str(chunk.id),
                        "document_active": document_active,
                        "patient_match": patient_match,
                        "generation_active": generation_active,
                        "revision_approved": revision_approved,
                        "included": included,
                    }
                )

            docs_output.append(
                {
                    "document_id": str(doc.id),
                    "source_hashes": {
                        "document_sha256": doc.indexed_source_sha256,
                        "revision_sha256": {str(revision.id): revision.content_sha256 for revision in revisions},
                        "generation_sha256": {
                            str(generation.id): {
                                "revision_set_sha256": generation.revision_set_sha256,
                                "generation_sha256": generation.generation_sha256,
                            }
                            for generation in generations
                        },
                    },
                    "approved_revision_set_id": str(doc.approved_revision_set_id)
                    if doc.approved_revision_set_id
                    else None,
                    "active_index_generation_id": str(doc.active_index_generation_id)
                    if doc.active_index_generation_id
                    else None,
                    "passed_lineage": lineage.passed,
                    "failure_codes": lineage.failure_codes,
                    "lexical_vector_ids": lexical_vector_ids,
                    "citation_locators": citation_locators,
                    "graph_provenance": {
                        "entities": [
                            {
                                "entity_id": str(entity.id),
                                "source_chunk_id": str(entity.source_chunk_id),
                                "name": entity.name,
                                "entity_type": entity.entity_type,
                                "confidence": entity.confidence,
                            }
                            for entity in entities
                        ],
                        "relations": [
                            {
                                "relation_id": str(relation.id),
                                "source_chunk_id": str(relation.source_chunk_id),
                                "source_entity_id": str(relation.source_entity_id),
                                "target_entity_id": str(relation.target_entity_id),
                                "relation_type": relation.relation_type,
                                "weight": relation.weight,
                            }
                            for relation in relations
                        ],
                    },
                    "authorization_outcomes": authorization_outcomes,
                }
            )

        report: dict[str, Any] = {
            "artifact_version": "cdi-v2-parity-v1",
            "status": "failed",
            "wrong_patient_count": wrong_patient_count,
            "superseded_generation_count": superseded_generation_count,
            "lineage_failure_count": lineage_failure_count,
            "git_sha": git_sha,
            "documents": docs_output,
        }
        report["status"] = "passed" if lineage_failure_count == 0 and superseded_generation_count == 0 else "failed"
        canonical = json.dumps(report, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        report["artifact_sha256"] = hashlib.sha256(canonical).hexdigest()
        return report
