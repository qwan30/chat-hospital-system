from __future__ import annotations

import math
import time
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import and_, bindparam, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.security import ROLE_PERMISSIONS
from hospital_ai.core.telemetry import RAG_EVIDENCE_COUNT, RAG_RETRIEVAL_DURATION
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage, User
from hospital_ai.evaluation.observer import EvaluationObserver
from hospital_ai.services.evidence_scope import ActiveEvidenceScope


@dataclass
class RetrievedChunk:
    evidence_id: str
    document_id: uuid.UUID
    document_title: str
    page: int
    chunk_id: uuid.UUID
    score: float
    content: str
    metadata: dict[str, Any]
    patient_id: Optional[uuid.UUID] = None
    generation_id: Optional[uuid.UUID] = None
    revision_set_id: Optional[uuid.UUID] = None
    page_revision_id: Optional[uuid.UUID] = None
    active_index_generation_id: Optional[uuid.UUID] = None
    approval_state: Optional[str] = None
    retrieval_method: Optional[str] = None
    source_hash: Optional[str] = None
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    bounding_boxes: Optional[list[Any]] = None

    def with_score_and_metadata(self, score: float, metadata: dict[str, Any]) -> RetrievedChunk:
        return RetrievedChunk(
            evidence_id=self.evidence_id,
            document_id=self.document_id,
            document_title=self.document_title,
            page=self.page,
            chunk_id=self.chunk_id,
            score=score,
            content=self.content,
            metadata=metadata,
            patient_id=self.patient_id,
            generation_id=self.generation_id,
            revision_set_id=self.revision_set_id,
            page_revision_id=self.page_revision_id,
            active_index_generation_id=self.active_index_generation_id,
            approval_state=self.approval_state,
            retrieval_method=metadata.get("retrieval_method", self.retrieval_method),
            source_hash=self.source_hash,
            start_offset=self.start_offset,
            end_offset=self.end_offset,
            bounding_boxes=self.bounding_boxes,
        )


def aligned_boxes_only(boxes: Any) -> Any:
    if isinstance(boxes, dict) and "aligned" in boxes:
        return boxes["aligned"]
    return boxes


def _scope_matches(scope: str, value: str) -> bool:
    """Compare authorization values without granting substring access."""
    return scope.strip().casefold() == value.strip().casefold()


class RetrievalService:
    def __init__(self, session: AsyncSession, evaluation_observer: Optional[EvaluationObserver] = None) -> None:
        self.session = session
        self.blocked_chunk_count = 0
        self.evaluation_observer = evaluation_observer

    async def _apply_role_filters(self, chunks: list[RetrievedChunk], user_id: uuid.UUID) -> list[RetrievedChunk]:
        if not chunks:
            return chunks

        user = await self.session.get(User, user_id)
        if not user:
            return []

        role_perms = ROLE_PERMISSIONS.get(user.role, {})
        can_access_full_notes = role_perms.get("can_access_full_notes", False)
        if can_access_full_notes:
            return chunks

        allowed_scopes = role_perms.get("allowed_scopes", set())

        doc_ids = list({c.document_id for c in chunks})
        result = await self.session.execute(select(Document.id, Document.document_type).where(Document.id.in_(doc_ids)))
        doc_types = {row.id: row.document_type for row in result.all()}

        allowed_chunks = []
        for c in chunks:
            doc_type = doc_types.get(c.document_id)
            chunk_tags = set(c.metadata.get("access_tags", []))

            if chunk_tags:
                if any(_scope_matches(scope, tag) for scope in allowed_scopes for tag in chunk_tags):
                    allowed_chunks.append(c)
                else:
                    self.blocked_chunk_count += 1
            elif (
                doc_type and any(_scope_matches(scope, doc_type) for scope in allowed_scopes)
            ) or "read" in allowed_scopes:
                allowed_chunks.append(c)
            else:
                self.blocked_chunk_count += 1

        return allowed_chunks

    async def search(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: Optional[uuid.UUID],
        query_embedding: Sequence[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        if patient_id is None:
            return []

        start_time = time.perf_counter()
        bind = self.session.get_bind()
        if bind.dialect.name == "postgresql":
            chunks = await self._search_postgres(
                user_id=user_id,
                patient_id=patient_id,
                query_embedding=query_embedding,
                top_k=top_k,
            )
        else:
            chunks = await self._search_portable(
                user_id=user_id,
                patient_id=patient_id,
                query_embedding=query_embedding,
                top_k=top_k,
            )
        if self.evaluation_observer is not None:
            self.evaluation_observer.record_candidates(chunks)
        results = await self._apply_role_filters(chunks, user_id)
        if self.evaluation_observer is not None:
            self.evaluation_observer.record_authorized_candidates(results)

        duration = time.perf_counter() - start_time
        RAG_RETRIEVAL_DURATION.labels(mode="vector").observe(duration)
        RAG_EVIDENCE_COUNT.labels(scope="patient-linked" if patient_id else "general").observe(len(results))

        return results

    async def hybrid_search(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: Optional[uuid.UUID],
        query_embedding: Sequence[float],
        query_text: str = "",
        query: str = "",
        top_k: int,
        retrieval_mode: str = "hybrid",
        mode: str = "",
    ) -> list[RetrievedChunk]:
        """Execute hybrid search combining vector and BM25 retrieval.

        Args:
            user_id: Authenticated user's ID.
            patient_id: Patient scope filter.
            query_embedding: Vector embedding of the query.
            query_text: Raw query text for BM25 matching.
            query: Alias for query_text.
            top_k: Maximum results to return.
            retrieval_mode: "vector", "bm25", or "hybrid".
            mode: Alias for retrieval_mode.

        Returns:
            Merged and de-duplicated chunks sorted by relevance.
        """
        actual_query = query_text or query
        actual_mode = mode or retrieval_mode
        if patient_id is None:
            return []

        start_time = time.perf_counter()

        if actual_mode == "vector":
            results = await self.search(
                user_id=user_id,
                patient_id=patient_id,
                query_embedding=query_embedding,
                top_k=top_k,
            )
            # metrics already recorded in search()
            return results

        if actual_mode == "bm25":
            results = await self._bm25_search(
                user_id=user_id,
                patient_id=patient_id,
                query_text=actual_query,
                top_k=top_k,
            )
            if self.evaluation_observer is not None:
                self.evaluation_observer.record_candidates(results)
            results = await self._apply_role_filters(results, user_id)
            if self.evaluation_observer is not None:
                self.evaluation_observer.record_authorized_candidates(results)

            duration = time.perf_counter() - start_time
            RAG_RETRIEVAL_DURATION.labels(mode="bm25").observe(duration)
            RAG_EVIDENCE_COUNT.labels(scope="patient-linked" if patient_id else "general").observe(len(results))

            return results

        # Hybrid mode: run both and fuse with RRF
        from hospital_ai.services.bm25 import reciprocal_rank_fusion

        # Fetch more candidates than top_k for each method, then fuse
        fetch_k = min(top_k * 2, 20)

        vector_results = await self.search(
            user_id=user_id,
            patient_id=patient_id,
            query_embedding=query_embedding,
            top_k=fetch_k,
        )

        bm25_results = await self._bm25_search(
            user_id=user_id,
            patient_id=patient_id,
            query_text=actual_query,
            top_k=fetch_k,
        )

        fused = reciprocal_rank_fusion(
            vector_results,
            bm25_results,
            top_k=top_k,
        )

        fused = await self._apply_role_filters(fused, user_id)
        if self.evaluation_observer is not None:
            self.evaluation_observer.record_authorized_candidates(fused)

        duration = time.perf_counter() - start_time
        RAG_RETRIEVAL_DURATION.labels(mode="hybrid").observe(duration)
        RAG_EVIDENCE_COUNT.labels(scope="patient-linked" if patient_id else "general").observe(len(fused))

        return fused

    async def get_chunks_by_ids(
        self,
        chunk_ids: list[uuid.UUID],
        *,
        user_id: uuid.UUID,
        patient_id: Optional[uuid.UUID],
    ) -> list[RetrievedChunk]:
        """Fetch specific chunks by ID, applying permission checks.

        Used by graph RAG to retrieve evidence discovered through
        entity relationship traversal.
        """
        if not chunk_ids or patient_id is None:
            return []

        allowed = ActiveEvidenceScope(self.session).authorized_chunk_ids(
            user_id=user_id,
            patient_id=patient_id,
        )

        result = await self.session.execute(
            select(DocumentChunk, Document, DocumentPage)
            .join(Document, Document.id == DocumentChunk.document_id)
            .join(
                DocumentPage,
                and_(
                    DocumentPage.id == DocumentChunk.page_id,
                    DocumentPage.document_id == DocumentChunk.document_id,
                ),
            )
            .where(
                DocumentChunk.id.in_(chunk_ids),
                DocumentChunk.id.in_(allowed),
                Document.status.in_(("ready", "ready_with_warnings")),
                DocumentChunk.deleted_at.is_(None),
                Document.deleted_at.is_(None),
                DocumentPage.deleted_at.is_(None),
            )
        )

        chunks = []
        for idx, (chunk, document, page) in enumerate(result.all(), start=1):
            chunks.append(
                RetrievedChunk(
                    evidence_id=f"G{idx}",
                    document_id=document.id,
                    document_title=document.title,
                    page=page.page_number,
                    chunk_id=chunk.id,
                    score=0.3,  # lower score for graph-discovered evidence
                    content=chunk.content,
                    metadata={
                        **(dict(chunk.meta or {})),
                        "retrieval_method": "graph_traversal",
                        "generation_id": str(chunk.generation_id) if chunk.generation_id else None,
                        "revision_set_id": str(chunk.revision_set_id) if chunk.revision_set_id else None,
                        "page_revision_id": str(chunk.page_revision_id) if chunk.page_revision_id else None,
                        "start_offset": chunk.text_start_offset,
                        "end_offset": chunk.text_end_offset,
                        "bounding_boxes": aligned_boxes_only(chunk.bounding_boxes),
                        "source_text_sha256": chunk.source_text_sha256,
                        "approval_state": chunk.approval_state,
                    },
                    patient_id=chunk.patient_id,
                    generation_id=chunk.generation_id,
                    revision_set_id=chunk.revision_set_id,
                    page_revision_id=chunk.page_revision_id,
                    active_index_generation_id=document.active_index_generation_id,
                    approval_state=chunk.approval_state,
                    retrieval_method="graph_traversal",
                    source_hash=chunk.source_text_sha256,
                    start_offset=chunk.text_start_offset,
                    end_offset=chunk.text_end_offset,
                    bounding_boxes=aligned_boxes_only(chunk.bounding_boxes),
                )
            )
        return await self._apply_role_filters(chunks, user_id)

    async def _bm25_search(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: Optional[uuid.UUID],
        query_text: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        """BM25 full-text search using tsvector (PostgreSQL) or Python fallback."""
        if patient_id is None:
            return []

        bind = self.session.get_bind()
        if bind.dialect.name == "postgresql":
            chunks = await self._bm25_search_postgres(
                user_id=user_id,
                patient_id=patient_id,
                query_text=query_text,
                top_k=top_k,
            )
        else:
            chunks = await self._bm25_search_portable(
                user_id=user_id,
                patient_id=patient_id,
                query_text=query_text,
                top_k=top_k,
            )
        return await self._apply_role_filters(chunks, user_id)

    async def _bm25_search_postgres(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: Optional[uuid.UUID],
        query_text: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        """PostgreSQL BM25 search using tsvector + GIN index."""
        import logging

        if patient_id is None:
            return []

        allowed = ActiveEvidenceScope(self.session).authorized_chunk_ids(
            user_id=user_id,
            patient_id=patient_id,
        )

        rank_expr = func.ts_rank_cd(
            text("document_chunks.search_vector"), func.plainto_tsquery("english", query_text)
        ).label("rank")

        stmt = (
            select(DocumentChunk, Document, DocumentPage, rank_expr)
            .join(Document, Document.id == DocumentChunk.document_id)
            .join(
                DocumentPage,
                and_(
                    DocumentPage.id == DocumentChunk.page_id,
                    DocumentPage.document_id == DocumentChunk.document_id,
                ),
            )
            .where(
                DocumentChunk.id.in_(allowed),
                Document.status.in_(("ready", "ready_with_warnings")),
                DocumentChunk.deleted_at.is_(None),
                Document.deleted_at.is_(None),
                DocumentPage.deleted_at.is_(None),
                text("document_chunks.search_vector @@ plainto_tsquery('english', :query_text)"),
            )
            .order_by(text("rank DESC"))
            .limit(top_k)
        )

        params = {
            "query_text": query_text,
        }

        try:
            result = await self.session.execute(stmt, params)
        except Exception as exc:
            logging.getLogger(__name__).exception("BM25 PostgreSQL search failed")
            from hospital_ai.core.errors import ExternalServiceError

            raise ExternalServiceError("PostgreSQL full-text search is unavailable.") from exc

        rows = result.all()
        if not rows:
            return []

        max_rank = float(rows[0][3]) if rows[0][3] else 1.0
        return [
            RetrievedChunk(
                evidence_id=f"E{index}",
                document_id=document.id,
                document_title=document.title,
                page=page.page_number,
                chunk_id=chunk.id,
                score=round(float(rank) / max(max_rank, 0.001), 4),
                content=chunk.content,
                metadata={
                    **(dict(chunk.meta or {})),
                    "retrieval_method": "bm25",
                    "generation_id": str(chunk.generation_id) if chunk.generation_id else None,
                    "revision_set_id": str(chunk.revision_set_id) if chunk.revision_set_id else None,
                    "page_revision_id": str(chunk.page_revision_id) if chunk.page_revision_id else None,
                    "start_offset": chunk.text_start_offset,
                    "end_offset": chunk.text_end_offset,
                    "bounding_boxes": aligned_boxes_only(chunk.bounding_boxes),
                    "source_text_sha256": chunk.source_text_sha256,
                    "approval_state": chunk.approval_state,
                },
                patient_id=chunk.patient_id,
                generation_id=chunk.generation_id,
                revision_set_id=chunk.revision_set_id,
                page_revision_id=chunk.page_revision_id,
                active_index_generation_id=document.active_index_generation_id,
                approval_state=chunk.approval_state,
                retrieval_method="bm25",
                source_hash=chunk.source_text_sha256,
                start_offset=chunk.text_start_offset,
                end_offset=chunk.text_end_offset,
                bounding_boxes=aligned_boxes_only(chunk.bounding_boxes),
            )
            for index, (chunk, document, page, rank) in enumerate(rows, start=1)
        ]

    async def _bm25_search_portable(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: Optional[uuid.UUID],
        query_text: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        """Portable BM25 search using Python-side scoring for SQLite tests."""
        from hospital_ai.services.bm25 import BM25Scorer

        if patient_id is None:
            return []

        allowed = ActiveEvidenceScope(self.session).authorized_chunk_ids(
            user_id=user_id,
            patient_id=patient_id,
        )

        stmt = (
            select(DocumentChunk, Document, DocumentPage)
            .join(Document, Document.id == DocumentChunk.document_id)
            .join(
                DocumentPage,
                and_(
                    DocumentPage.id == DocumentChunk.page_id,
                    DocumentPage.document_id == DocumentChunk.document_id,
                ),
            )
            .where(
                DocumentChunk.id.in_(allowed),
                Document.status.in_(("ready", "ready_with_warnings")),
                DocumentChunk.deleted_at.is_(None),
                Document.deleted_at.is_(None),
                DocumentPage.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        all_chunks = [
            RetrievedChunk(
                evidence_id=f"E{index}",
                document_id=document.id,
                document_title=document.title,
                page=page.page_number,
                chunk_id=chunk.id,
                score=0.0,
                content=chunk.content,
                metadata={
                    **(dict(chunk.meta or {})),
                    "retrieval_method": "bm25",
                    "generation_id": str(chunk.generation_id) if chunk.generation_id else None,
                    "revision_set_id": str(chunk.revision_set_id) if chunk.revision_set_id else None,
                    "page_revision_id": str(chunk.page_revision_id) if chunk.page_revision_id else None,
                    "start_offset": chunk.text_start_offset,
                    "end_offset": chunk.text_end_offset,
                    "bounding_boxes": aligned_boxes_only(chunk.bounding_boxes),
                    "source_text_sha256": chunk.source_text_sha256,
                    "approval_state": chunk.approval_state,
                },
                patient_id=chunk.patient_id,
                generation_id=chunk.generation_id,
                revision_set_id=chunk.revision_set_id,
                page_revision_id=chunk.page_revision_id,
                active_index_generation_id=document.active_index_generation_id,
                approval_state=chunk.approval_state,
                retrieval_method="bm25",
                source_hash=chunk.source_text_sha256,
                start_offset=chunk.text_start_offset,
                end_offset=chunk.text_end_offset,
                bounding_boxes=aligned_boxes_only(chunk.bounding_boxes),
            )
            for index, (chunk, document, page) in enumerate(result.all(), start=1)
        ]

        scorer = BM25Scorer()
        return scorer.score(query_text, all_chunks, top_k=top_k)

    async def _search_postgres(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: Optional[uuid.UUID],
        query_embedding: Sequence[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        if patient_id is None:
            return []

        allowed = ActiveEvidenceScope(self.session).authorized_chunk_ids(
            user_id=user_id,
            patient_id=patient_id,
        )

        query_embedding_param = bindparam("query_embedding", type_=DocumentChunk.embedding.type)
        distance_expr = DocumentChunk.embedding.op("<=>")(query_embedding_param)
        score_expr = (1 - distance_expr).label("score")

        stmt = (
            select(DocumentChunk, Document, DocumentPage, score_expr)
            .join(Document, Document.id == DocumentChunk.document_id)
            .join(
                DocumentPage,
                and_(
                    DocumentPage.id == DocumentChunk.page_id,
                    DocumentPage.document_id == DocumentChunk.document_id,
                ),
            )
            .where(
                DocumentChunk.id.in_(allowed),
                Document.status.in_(("ready", "ready_with_warnings")),
                DocumentChunk.deleted_at.is_(None),
                Document.deleted_at.is_(None),
                DocumentPage.deleted_at.is_(None),
                DocumentChunk.embedding.is_not(None),
            )
            .order_by(distance_expr)
            .limit(top_k)
        )

        params = {"query_embedding": list(query_embedding)}
        result = await self.session.execute(stmt, params)

        return [
            RetrievedChunk(
                evidence_id=f"E{index}",
                document_id=document.id,
                document_title=document.title,
                page=page.page_number,
                chunk_id=chunk.id,
                score=float(score),
                content=chunk.content,
                metadata={
                    **(dict(chunk.meta or {})),
                    "retrieval_method": "vector",
                    "generation_id": str(chunk.generation_id) if chunk.generation_id else None,
                    "revision_set_id": str(chunk.revision_set_id) if chunk.revision_set_id else None,
                    "page_revision_id": str(chunk.page_revision_id) if chunk.page_revision_id else None,
                    "start_offset": chunk.text_start_offset,
                    "end_offset": chunk.text_end_offset,
                    "bounding_boxes": aligned_boxes_only(chunk.bounding_boxes),
                    "source_text_sha256": chunk.source_text_sha256,
                    "approval_state": chunk.approval_state,
                },
                patient_id=chunk.patient_id,
                generation_id=chunk.generation_id,
                revision_set_id=chunk.revision_set_id,
                page_revision_id=chunk.page_revision_id,
                active_index_generation_id=document.active_index_generation_id,
                approval_state=chunk.approval_state,
                retrieval_method="vector",
                source_hash=chunk.source_text_sha256,
                start_offset=chunk.text_start_offset,
                end_offset=chunk.text_end_offset,
                bounding_boxes=aligned_boxes_only(chunk.bounding_boxes),
            )
            for index, (chunk, document, page, score) in enumerate(result.all(), start=1)
        ]

    async def _search_portable(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: Optional[uuid.UUID],
        query_embedding: Sequence[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        if patient_id is None:
            return []

        allowed = ActiveEvidenceScope(self.session).authorized_chunk_ids(
            user_id=user_id,
            patient_id=patient_id,
        )
        stmt = (
            select(DocumentChunk, Document, DocumentPage)
            .join(Document, Document.id == DocumentChunk.document_id)
            .join(
                DocumentPage,
                and_(
                    DocumentPage.id == DocumentChunk.page_id,
                    DocumentPage.document_id == DocumentChunk.document_id,
                ),
            )
            .where(
                DocumentChunk.id.in_(allowed),
                Document.status.in_(("ready", "ready_with_warnings")),
                DocumentChunk.deleted_at.is_(None),
                Document.deleted_at.is_(None),
                DocumentPage.deleted_at.is_(None),
                DocumentChunk.embedding.is_not(None),
            )
        )
        result = await self.session.execute(stmt)
        scored = []
        for chunk, document, page in result.all():
            score = cosine_similarity(query_embedding, chunk.embedding or [])
            scored.append((score, chunk, document, page))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            RetrievedChunk(
                evidence_id=f"E{index}",
                document_id=document.id,
                document_title=document.title,
                page=page.page_number,
                chunk_id=chunk.id,
                score=float(score),
                content=chunk.content,
                metadata={
                    **(dict(chunk.meta or {})),
                    "retrieval_method": "vector",
                    "generation_id": str(chunk.generation_id) if chunk.generation_id else None,
                    "revision_set_id": str(chunk.revision_set_id) if chunk.revision_set_id else None,
                    "page_revision_id": str(chunk.page_revision_id) if chunk.page_revision_id else None,
                    "start_offset": chunk.text_start_offset,
                    "end_offset": chunk.text_end_offset,
                    "bounding_boxes": aligned_boxes_only(chunk.bounding_boxes),
                    "source_text_sha256": chunk.source_text_sha256,
                    "approval_state": chunk.approval_state,
                },
                patient_id=chunk.patient_id,
                generation_id=chunk.generation_id,
                revision_set_id=chunk.revision_set_id,
                page_revision_id=chunk.page_revision_id,
                active_index_generation_id=document.active_index_generation_id,
                approval_state=chunk.approval_state,
                retrieval_method="vector",
                source_hash=chunk.source_text_sha256,
                start_offset=chunk.text_start_offset,
                end_offset=chunk.text_end_offset,
                bounding_boxes=aligned_boxes_only(chunk.bounding_boxes),
            )
            for index, (score, chunk, document, page) in enumerate(scored[:top_k], start=1)
        ]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0
    size = min(len(a), len(b))
    dot = sum(float(a[index]) * float(b[index]) for index in range(size))
    norm_a = math.sqrt(sum(float(value) * float(value) for value in a[:size]))
    norm_b = math.sqrt(sum(float(value) * float(value) for value in b[:size]))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def format_pgvector(values: Iterable[float]) -> str:
    return "[" + ",".join(f"{float(value):.8f}" for value in values) + "]"
