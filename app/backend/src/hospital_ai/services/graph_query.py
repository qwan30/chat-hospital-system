import uuid
from datetime import date
from typing import Literal, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from hospital_ai.db.models import Document, User
from hospital_ai.db.clinical_graph import GraphEntity, GraphMention, GraphRelationAssertion, GraphRelationEvidence
from hospital_ai.db.clinical_documents import DocumentIndexGeneration, DocumentRevisionSet
from hospital_ai.schemas.document_graph import DocumentGraphRead

class GraphFilters(BaseModel):
    node_limit: Literal[25, 50, 100] = 50
    edge_limit: Literal[50, 100, 250] = 100
    hop_depth: int = Field(2, ge=1, le=3)
    entity_types: tuple[str, ...] = ()
    relation_types: tuple[str, ...] = ()
    min_confidence: float = Field(0.0, ge=0.0, le=1.0)
    document_scope: tuple[UUID, ...] = ()
    approved_revision_set_id: UUID | None = None
    date_from: date | None = None
    date_to: date | None = None
    layout: Literal["force", "timeline", "hierarchical"] = "force"
    include_superseded: bool = False

class GraphQueryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def document_graph(
        self, document: Document, current_user: User, filters: GraphFilters
    ) -> DocumentGraphRead:
        from sqlalchemy import select
        
        # 1. Fetch mentions
        # We need to join GraphMention -> Document to check active_index_generation_id
        mention_stmt = (
            select(
                GraphMention.generation_id,
                Document.active_index_generation_id.label("source_active_generation_id"),
                GraphMention.entity_id,
                GraphEntity.normalized_label,
            )
            .join(Document, Document.id == GraphMention.document_id)
            .join(GraphEntity, GraphEntity.id == GraphMention.entity_id)
            .where(GraphMention.document_id == document.id)
        )
        
        if not filters.include_superseded:
            mention_stmt = mention_stmt.where(GraphMention.generation_id == Document.active_index_generation_id)
            
        mention_stmt = mention_stmt.limit(filters.node_limit)
        
        mention_results = await self.session.execute(mention_stmt)
        mentions = [
            {
                "generation_id": row.generation_id,
                "source_active_generation_id": row.source_active_generation_id,
                "entity_id": row.entity_id,
                "normalized_label": row.normalized_label,
            }
            for row in mention_results
        ]
        
        # 2. Fetch assertions (edges)
        assertion_stmt = (
            select(
                GraphRelationAssertion.id,
                GraphRelationEvidence.id.label("evidence_id"),
            )
            .join(GraphRelationEvidence, GraphRelationEvidence.assertion_id == GraphRelationAssertion.id)
            .join(Document, Document.id == GraphRelationEvidence.document_id)
            .where(GraphRelationEvidence.document_id == document.id)
        )
        
        if not filters.include_superseded:
            assertion_stmt = assertion_stmt.where(GraphRelationEvidence.generation_id == Document.active_index_generation_id)
            
        assertion_stmt = assertion_stmt.limit(filters.edge_limit)
        
        assertion_results = await self.session.execute(assertion_stmt)
        
        # Group evidences by assertion
        assertions_map = {}
        for row in assertion_results:
            if row.id not in assertions_map:
                assertions_map[row.id] = {"id": row.id, "evidence_ids": []}
            assertions_map[row.id]["evidence_ids"].append(row.evidence_id)
            
        return DocumentGraphRead(mentions=mentions, assertions=list(assertions_map.values()))
