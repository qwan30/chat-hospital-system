import math
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence

from sqlalchemy import bindparam, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.security import PATIENT_READ_SCOPES
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage
from hospital_ai.services.permissions import active_patient_permission_exists

PERMISSION_FILTERED_RETRIEVAL_SQL = """
with allowed as (
  select 1
  from patient_permissions pp
  where pp.user_id = :user_id
    and pp.patient_id = :patient_id
    and pp.scope in :accepted_scopes
    and pp.deleted_at is null
    and (pp.expires_at is null or pp.expires_at > now())
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
  join document_pages p on p.id = c.page_id
  where exists (select 1 from allowed)
    and c.patient_id = :patient_id
    and d.status = 'indexed'
    and c.deleted_at is null
    and d.deleted_at is null
    and p.deleted_at is null
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
    metadata: Dict[str, Any]


class RetrievalService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: uuid.UUID,
        query_embedding: Sequence[float],
        top_k: int,
    ) -> List[RetrievedChunk]:
        bind = self.session.get_bind()
        if bind.dialect.name == "postgresql":
            return await self._search_postgres(
                user_id=user_id,
                patient_id=patient_id,
                query_embedding=query_embedding,
                top_k=top_k,
            )
        return await self._search_portable(
            user_id=user_id,
            patient_id=patient_id,
            query_embedding=query_embedding,
            top_k=top_k,
        )

    async def _search_postgres(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: uuid.UUID,
        query_embedding: Sequence[float],
        top_k: int,
    ) -> List[RetrievedChunk]:
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
                metadata=dict(row["metadata"] or {}),
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
    ) -> List[RetrievedChunk]:
        permission_exists = active_patient_permission_exists(
            user_id=user_id,
            patient_id=patient_id,
            accepted_scopes=PATIENT_READ_SCOPES,
        )
        stmt = (
            select(DocumentChunk, Document, DocumentPage)
            .join(Document, Document.id == DocumentChunk.document_id)
            .join(DocumentPage, DocumentPage.id == DocumentChunk.page_id)
            .where(
                permission_exists,
                DocumentChunk.patient_id == patient_id,
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
                metadata=dict(chunk.meta or {}),
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
