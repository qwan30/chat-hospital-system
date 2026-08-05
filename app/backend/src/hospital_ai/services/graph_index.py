from __future__ import annotations

import uuid
from typing import Any
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.db.clinical_graph import (
    GraphEntity,
    GraphMention,
    GraphRelationAssertion,
    GraphRelationEvidence,
)
from hospital_ai.db.models import DocumentChunk
from hospital_ai.services.graph_rag import ExtractedEntity, ExtractedRelation, GraphExtraction


@dataclass
class GraphIndexResult:
    entities_inserted: int
    mentions_inserted: int
    assertions_inserted: int
    evidence_inserted: int


class GraphIndexService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _upsert_entity(self, patient_id: uuid.UUID, entity_type: str, normalized_label: str) -> GraphEntity:
        # We need a cross-dialect UPSERT or we just query and then insert.
        # Given it's async, we can do a standard select + insert if not found, 
        # but to be robust against concurrency, an upsert is better.
        # Since we use SQLite in tests and Postgres in prod, we'll try a basic approach:
        
        # SQLite doesn't cleanly support ON CONFLICT DO NOTHING with returning full ORM object 
        # identically to Postgres in older SQLAlchemy versions, but SQLAlchemy v2 handles it.
        # Let's do a simple select, and if none, insert.
        stmt = select(GraphEntity).where(
            GraphEntity.patient_id == patient_id,
            GraphEntity.entity_type == entity_type,
            GraphEntity.normalized_label == normalized_label
        )
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        if not entity:
            entity = GraphEntity(
                patient_id=patient_id,
                entity_type=entity_type,
                normalized_label=normalized_label
            )
            self.session.add(entity)
            await self.session.flush()
        return entity

    async def _upsert_assertion(
        self, patient_id: uuid.UUID, subject_id: uuid.UUID, object_id: uuid.UUID, item: ExtractedRelation
    ) -> GraphRelationAssertion:
        stmt = select(GraphRelationAssertion).where(
            GraphRelationAssertion.patient_id == patient_id,
            GraphRelationAssertion.subject_entity_id == subject_id,
            GraphRelationAssertion.object_entity_id == object_id,
            GraphRelationAssertion.relation_type == item.relation_type,
            GraphRelationAssertion.normalized_value == item.normalized_value
        )
        result = await self.session.execute(stmt)
        assertion = result.scalar_one_or_none()
        if not assertion:
            assertion = GraphRelationAssertion(
                patient_id=patient_id,
                subject_entity_id=subject_id,
                object_entity_id=object_id,
                relation_type=item.relation_type,
                normalized_value=item.normalized_value
            )
            self.session.add(assertion)
            await self.session.flush()
        return assertion

    async def index_chunk(
        self,
        generation_id: uuid.UUID,
        chunk: DocumentChunk,
        extraction: GraphExtraction,
    ) -> GraphIndexResult:
        result = GraphIndexResult(0, 0, 0, 0)
        
        entity_map = {}
        for item in extraction.entities:
            entity = await self._upsert_entity(chunk.patient_id, item.entity_type, item.normalized_label)
            entity_map[item.normalized_label] = entity.id
            result.entities_inserted += 1
            
            mention = GraphMention(
                patient_id=chunk.patient_id,
                entity_id=entity.id,
                generation_id=generation_id,
                document_id=chunk.document_id,
                revision_set_id=chunk.revision_set_id,
                page_revision_id=chunk.page_revision_id,
                chunk_id=chunk.id,
                independent_source_identity=str(chunk.id), # using chunk.id as independent identity for now
            )
            self.session.add(mention)
            result.mentions_inserted += 1

        for item in extraction.relations:
            subject_id = entity_map.get(item.subject_label)
            object_id = entity_map.get(item.object_label)
            
            if not subject_id or not object_id:
                # If entities were somehow not matched/upserted, skip this relation
                continue
                
            assertion = await self._upsert_assertion(chunk.patient_id, subject_id, object_id, item)
            result.assertions_inserted += 1
            
            evidence = GraphRelationEvidence(
                patient_id=chunk.patient_id,
                assertion_id=assertion.id,
                generation_id=generation_id,
                document_id=chunk.document_id,
                revision_set_id=chunk.revision_set_id,
                page_revision_id=chunk.page_revision_id,
                chunk_id=chunk.id,
                independent_source_identity=str(chunk.id),
            )
            self.session.add(evidence)
            result.evidence_inserted += 1

        await self.session.flush()
        return result
