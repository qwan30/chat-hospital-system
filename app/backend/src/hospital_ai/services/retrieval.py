import math
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from sqlalchemy import and_, bindparam, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.security import PATIENT_READ_SCOPES, ROLE_PERMISSIONS
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage, User
from hospital_ai.services.permissions import (
    ACTIVE_PATIENT_PERMISSION_SQL,
    active_patient_permission_exists,
)

PERMISSION_FILTERED_RETRIEVAL_SQL = f"""
with allowed as (
{ACTIVE_PATIENT_PERMISSION_SQL}
),
ranked_chunks as (
  select
    c.id as chunk_id,
    c.document_id,
    c.page_id,
    p.page_number,
    d.title,
    c.content,
    c.metadata,
    1 - (c.embedding <=> CAST(:query_embedding AS vector)) as score
  from document_chunks c
  join documents d on d.id = c.document_id
  join document_pages p on p.id = c.page_id and p.document_id = c.document_id
  where exists (select 1 from allowed)
    and c.patient_id = :patient_id
    and d.patient_id = :patient_id
    and d.status = 'indexed'
    and c.deleted_at is null
    and d.deleted_at is null
    and p.deleted_at is null
    and c.embedding is not null
  order by c.embedding <=> CAST(:query_embedding AS vector)
  limit :top_k
)
select * from ranked_chunks
"""


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


class RetrievalService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.blocked_chunk_count = 0

    async def _apply_role_filters(self, chunks: list[RetrievedChunk], user_id: uuid.UUID) -> list[RetrievedChunk]:
        if not chunks:
            return chunks

        user = await self.session.get(User, user_id)
        if not user:
            return chunks

        role_perms = ROLE_PERMISSIONS.get(user.role, {})
        can_access_full_notes = role_perms.get("can_access_full_notes", True)
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

            if chunk_tags and chunk_tags.intersection(allowed_scopes):
                allowed_chunks.append(c)
            elif doc_type in allowed_scopes:
                allowed_chunks.append(c)
            else:
                self.blocked_chunk_count += 1

        return allowed_chunks

    async def search(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: uuid.UUID,
        query_embedding: Sequence[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
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
        return await self._apply_role_filters(chunks, user_id)

    async def hybrid_search(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: uuid.UUID,
        query_embedding: Sequence[float],
        query_text: str,
        top_k: int,
        retrieval_mode: str = "hybrid",
    ) -> list[RetrievedChunk]:
        """Execute hybrid search combining vector and BM25 retrieval.

        Args:
            user_id: Authenticated user's ID.
            patient_id: Patient scope filter.
            query_embedding: Vector embedding of the query.
            query_text: Raw query text for BM25 matching.
            top_k: Maximum results to return.
            retrieval_mode: "vector", "bm25", or "hybrid".

        Returns:
            Merged and de-duplicated chunks sorted by relevance.
        """
        if retrieval_mode == "vector":
            return await self.search(
                user_id=user_id,
                patient_id=patient_id,
                query_embedding=query_embedding,
                top_k=top_k,
            )

        if retrieval_mode == "bm25":
            return await self._bm25_search(
                user_id=user_id,
                patient_id=patient_id,
                query_text=query_text,
                top_k=top_k,
            )

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
            query_text=query_text,
            top_k=fetch_k,
        )

        fused = reciprocal_rank_fusion(
            vector_results,
            bm25_results,
            top_k=top_k,
        )

        return fused

    async def get_chunks_by_ids(
        self,
        chunk_ids: list[uuid.UUID],
        *,
        user_id: uuid.UUID,
        patient_id: uuid.UUID,
    ) -> list[RetrievedChunk]:
        """Fetch specific chunks by ID, applying permission checks.

        Used by graph RAG to retrieve evidence discovered through
        entity relationship traversal.
        """
        if not chunk_ids:
            return []

        # Verify permission using PermissionService
        from hospital_ai.services.permissions import PermissionService

        has_access = await PermissionService(self.session).has_patient_scope(
            user_id=user_id,
            patient_id=patient_id,
            accepted_scopes=PATIENT_READ_SCOPES,
        )
        if not has_access:
            return []

        result = await self.session.execute(
            select(
                DocumentChunk.id,
                DocumentChunk.document_id,
                DocumentChunk.content,
                DocumentChunk.meta,
                DocumentPage.page_number,
                Document.title,
            )
            .join(Document, Document.id == DocumentChunk.document_id)
            .join(DocumentPage, DocumentPage.id == DocumentChunk.page_id)
            .where(
                DocumentChunk.id.in_(chunk_ids),
                DocumentChunk.patient_id == patient_id,
                Document.status == "indexed",
                DocumentChunk.deleted_at.is_(None),
                Document.deleted_at.is_(None),
            )
        )

        chunks = []
        for idx, row in enumerate(result.all(), start=1):
            chunks.append(
                RetrievedChunk(
                    evidence_id=f"G{idx}",
                    document_id=row.document_id,
                    document_title=row.title,
                    page=row.page_number,
                    chunk_id=row.id,
                    score=0.3,  # lower score for graph-discovered evidence
                    content=row.content,
                    metadata=row[3] if row[3] else {},
                )
            )
        return await self._apply_role_filters(chunks, user_id)

    async def _bm25_search(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: uuid.UUID,
        query_text: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        """BM25 full-text search using tsvector (PostgreSQL) or Python fallback."""
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
        patient_id: uuid.UUID,
        query_text: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        """PostgreSQL BM25 search using tsvector + GIN index."""
        import logging

        sql = text(f"""
            with allowed as (
            {ACTIVE_PATIENT_PERMISSION_SQL}
            )
            select
                c.id as chunk_id,
                c.document_id,
                p.page_number,
                d.title,
                c.content,
                c.metadata,
                ts_rank_cd(c.search_vector, plainto_tsquery('english', :query_text)) as rank
            from document_chunks c
            join documents d on d.id = c.document_id
            join document_pages p on p.id = c.page_id and p.document_id = c.document_id
            where exists (select 1 from allowed)
              and c.patient_id = :patient_id
              and d.patient_id = :patient_id
              and d.status = 'indexed'
              and c.deleted_at is null
              and d.deleted_at is null
              and p.deleted_at is null
              and c.search_vector @@ plainto_tsquery('english', :query_text)
            order by rank desc
            limit :top_k
        """).bindparams(bindparam("accepted_scopes", expanding=True))

        try:
            result = await self.session.execute(
                sql,
                {
                    "user_id": user_id,
                    "patient_id": patient_id,
                    "accepted_scopes": tuple(sorted(PATIENT_READ_SCOPES)),
                    "query_text": query_text,
                    "top_k": top_k,
                },
            )
            rows = result.mappings().all()
        except Exception as exc:
            logging.getLogger(__name__).warning("BM25 PostgreSQL search failed (search_vector may not exist): %s", exc)
            return []

        if not rows:
            return []

        max_rank = float(rows[0]["rank"]) if rows[0]["rank"] else 1.0
        return [
            RetrievedChunk(
                evidence_id=f"E{index}",
                document_id=row["document_id"],
                document_title=row["title"],
                page=row["page_number"],
                chunk_id=row["chunk_id"],
                score=round(float(row["rank"]) / max(max_rank, 0.001), 4),
                content=row["content"],
                metadata={
                    **(dict(row["metadata"] or {})),
                    "retrieval_method": "bm25",
                },
            )
            for index, row in enumerate(rows, start=1)
        ]

    async def _bm25_search_portable(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: uuid.UUID,
        query_text: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        """Portable BM25 search using Python-side scoring for SQLite tests."""
        from hospital_ai.services.bm25 import BM25Scorer

        permission_exists = active_patient_permission_exists(
            user_id=user_id,
            patient_id=patient_id,
            accepted_scopes=PATIENT_READ_SCOPES,
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
                permission_exists,
                DocumentChunk.patient_id == patient_id,
                Document.patient_id == patient_id,
                Document.status == "indexed",
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
                metadata=dict(chunk.meta or {}),
            )
            for index, (chunk, document, page) in enumerate(result.all(), start=1)
        ]

        scorer = BM25Scorer()
        return scorer.score(query_text, all_chunks, top_k=top_k)

    async def _search_postgres(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: uuid.UUID,
        query_embedding: Sequence[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        result = await self.session.execute(
            text(PERMISSION_FILTERED_RETRIEVAL_SQL).bindparams(
                bindparam("accepted_scopes", expanding=True),
            ),
            {
                "user_id": user_id,
                "patient_id": patient_id,
                "accepted_scopes": tuple(sorted(PATIENT_READ_SCOPES)),
                "query_embedding": format_pgvector(query_embedding),
                "top_k": top_k,
            },
        )
        rows = result.mappings().all()
        return [
            RetrievedChunk(
                evidence_id=f"E{index}",
                document_id=row["document_id"],
                document_title=row["title"],
                page=row["page_number"],
                chunk_id=row["chunk_id"],
                score=float(row["score"]),
                content=row["content"],
                metadata={**(dict(row["metadata"] or {})), "retrieval_method": "vector"},
            )
            for index, row in enumerate(rows, start=1)
        ]

    async def _search_portable(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: uuid.UUID,
        query_embedding: Sequence[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        permission_exists = active_patient_permission_exists(
            user_id=user_id,
            patient_id=patient_id,
            accepted_scopes=PATIENT_READ_SCOPES,
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
                permission_exists,
                DocumentChunk.patient_id == patient_id,
                Document.patient_id == patient_id,
                Document.status == "indexed",
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
                metadata={**(dict(chunk.meta or {})), "retrieval_method": "vector"},
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
