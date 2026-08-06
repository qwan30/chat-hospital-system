from __future__ import annotations

from datetime import UTC, date, datetime, time
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.db.clinical_documents import DocumentPageRevision
from hospital_ai.db.clinical_graph import GraphEntity, GraphMention, GraphRelationAssertion, GraphRelationEvidence
from hospital_ai.db.models import Document, DocumentChunk, User
from hospital_ai.schemas.document_graph import DocumentGraphRead
from hospital_ai.services.evidence_scope import ActiveEvidenceScope


class GraphFilters(BaseModel):
    node_limit: Literal[25, 50, 100] = 50
    edge_limit: Literal[50, 100, 250] = 100
    hop_depth: int = Field(2, ge=1, le=3)
    entity_types: tuple[str, ...] = ()
    relation_types: tuple[str, ...] = ()
    min_confidence: float = Field(0.0, ge=0.0, le=1.0)
    document_scope: tuple[UUID, ...] = ()
    approved_revision_set_id: Optional[UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    layout: Literal["force", "timeline", "hierarchical"] = "force"
    include_superseded: bool = False


class GraphQueryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def document_graph(self, document: Document, current_user: User, filters: GraphFilters) -> DocumentGraphRead:
        from sqlalchemy import and_, select

        scope = ActiveEvidenceScope(self.session)
        document_ids = filters.document_scope or (document.id,)
        allowed_chunk_ids = scope.authorized_chunk_ids(
            user_id=current_user.id,
            patient_id=document.patient_id,
            document_ids=document_ids,
            include_superseded=filters.include_superseded,
        )

        revision_filters = []
        if filters.approved_revision_set_id is not None:
            revision_filters.append(GraphMention.revision_set_id == filters.approved_revision_set_id)
        if filters.date_from is not None:
            revision_filters.append(
                DocumentPageRevision.created_at >= datetime.combine(filters.date_from, time.min, tzinfo=UTC)
            )
        if filters.date_to is not None:
            revision_filters.append(
                DocumentPageRevision.created_at
                < datetime.combine(
                    filters.date_to,
                    time.max,
                    tzinfo=UTC,
                )
            )

        # 1. Fetch mentions
        mention_stmt = (
            select(
                GraphMention.generation_id,
                Document.active_index_generation_id.label("source_active_generation_id"),
                GraphMention.entity_id,
                GraphEntity.normalized_label,
                GraphEntity.entity_type,
                DocumentPageRevision.confidence,
            )
            .join(Document, Document.id == GraphMention.document_id)
            .join(GraphEntity, GraphEntity.id == GraphMention.entity_id)
            .join(DocumentChunk, DocumentChunk.id == GraphMention.chunk_id)
            .join(DocumentPageRevision, DocumentPageRevision.id == GraphMention.page_revision_id)
            .where(
                GraphMention.document_id == document.id,
                GraphMention.patient_id == document.patient_id,
                GraphEntity.patient_id == document.patient_id,
                GraphEntity.lifecycle_status == "active",
                DocumentChunk.id.in_(allowed_chunk_ids),
                DocumentPageRevision.confidence.is_not(None),
                DocumentPageRevision.confidence >= filters.min_confidence,
                *revision_filters,
            )
        )
        if filters.entity_types:
            mention_stmt = mention_stmt.where(GraphEntity.entity_type.in_(filters.entity_types))

        mention_stmt = mention_stmt.limit(filters.node_limit)

        mention_results = await self.session.execute(mention_stmt)
        mentions = [
            {
                "generation_id": row.generation_id,
                "source_active_generation_id": row.source_active_generation_id,
                "entity_id": row.entity_id,
                "normalized_label": row.normalized_label,
                "entity_type": row.entity_type,
                "confidence": float(row.confidence),
            }
            for row in mention_results
        ]

        # 2. Fetch assertions (edges)
        assertion_stmt = (
            select(
                GraphRelationAssertion.id,
                GraphRelationEvidence.id.label("evidence_id"),
                GraphRelationAssertion.relation_type,
            )
            .join(
                GraphRelationEvidence,
                and_(
                    GraphRelationEvidence.assertion_id == GraphRelationAssertion.id,
                    GraphRelationEvidence.patient_id == GraphRelationAssertion.patient_id,
                ),
            )
            .join(Document, Document.id == GraphRelationEvidence.document_id)
            .join(DocumentChunk, DocumentChunk.id == GraphRelationEvidence.chunk_id)
            .join(DocumentPageRevision, DocumentPageRevision.id == GraphRelationEvidence.page_revision_id)
            .where(
                GraphRelationEvidence.document_id == document.id,
                GraphRelationEvidence.patient_id == document.patient_id,
                GraphRelationAssertion.patient_id == document.patient_id,
                GraphRelationAssertion.lifecycle_status == "active",
                DocumentChunk.id.in_(allowed_chunk_ids),
                DocumentPageRevision.confidence.is_not(None),
                DocumentPageRevision.confidence >= filters.min_confidence,
                *(
                    [GraphRelationEvidence.revision_set_id == filters.approved_revision_set_id]
                    if filters.approved_revision_set_id is not None
                    else []
                ),
            )
        )
        if filters.relation_types:
            assertion_stmt = assertion_stmt.where(GraphRelationAssertion.relation_type.in_(filters.relation_types))
        if filters.date_from:
            assertion_stmt = assertion_stmt.where(
                DocumentPageRevision.created_at >= datetime.combine(filters.date_from, time.min, tzinfo=UTC)
            )
        if filters.date_to:
            assertion_stmt = assertion_stmt.where(
                DocumentPageRevision.created_at < datetime.combine(filters.date_to, time.max, tzinfo=UTC)
            )

        assertion_stmt = assertion_stmt.limit(filters.edge_limit)

        assertion_results = await self.session.execute(assertion_stmt)

        # Group evidences by assertion
        assertions_map = {}
        for row in assertion_results:
            if row.id not in assertions_map:
                assertions_map[row.id] = {"id": row.id, "relation_type": row.relation_type, "evidence_ids": []}
            assertions_map[row.id]["evidence_ids"].append(row.evidence_id)

        return DocumentGraphRead(mentions=mentions, assertions=list(assertions_map.values()))
