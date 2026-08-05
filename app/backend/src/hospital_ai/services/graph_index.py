from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.db.clinical_graph import (
    GraphEntity,
    GraphMention,
    GraphRelationAssertion,
    GraphRelationEvidence,
    deterministic_provenance_id,
    immutable_source_identity,
)
from hospital_ai.db.models import DocumentChunk
from hospital_ai.services.graph_rag import ExtractedRelation, GraphExtraction


@dataclass
class GraphIndexResult:
    entities_inserted: int
    mentions_inserted: int
    assertions_inserted: int
    evidence_inserted: int


class GraphIndexService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _insert_ignore(
        self,
        model: type,
        values: dict,
        conflict_columns: tuple[str, ...],
    ) -> bool:
        dialect = self.session.get_bind().dialect.name
        if dialect == "postgresql":
            statement = postgres_insert(model).values(**values)
        elif dialect == "sqlite":
            statement = sqlite_insert(model).values(**values)
        else:
            raise RuntimeError(f"Unsupported graph index dialect: {dialect}")
        result = await self.session.execute(statement.on_conflict_do_nothing(index_elements=list(conflict_columns)))
        return bool(result.rowcount)

    async def _upsert_entity(self, patient_id: uuid.UUID, entity_type: str, normalized_label: str) -> GraphEntity:
        await self._insert_ignore(
            GraphEntity,
            {
                "patient_id": patient_id,
                "entity_type": entity_type,
                "normalized_label": normalized_label,
            },
            ("patient_id", "entity_type", "normalized_label"),
        )
        result = await self.session.execute(
            select(GraphEntity).where(
                GraphEntity.patient_id == patient_id,
                GraphEntity.entity_type == entity_type,
                GraphEntity.normalized_label == normalized_label,
            )
        )
        return result.scalar_one()

    async def _upsert_assertion(
        self, patient_id: uuid.UUID, subject_id: uuid.UUID, object_id: uuid.UUID, item: ExtractedRelation
    ) -> GraphRelationAssertion:
        await self._insert_ignore(
            GraphRelationAssertion,
            {
                "patient_id": patient_id,
                "subject_entity_id": subject_id,
                "object_entity_id": object_id,
                "relation_type": item.relation_type,
                "normalized_value": item.normalized_value,
            },
            ("patient_id", "subject_entity_id", "object_entity_id", "relation_type", "normalized_value"),
        )
        result = await self.session.execute(
            select(GraphRelationAssertion).where(
                GraphRelationAssertion.patient_id == patient_id,
                GraphRelationAssertion.subject_entity_id == subject_id,
                GraphRelationAssertion.object_entity_id == object_id,
                GraphRelationAssertion.relation_type == item.relation_type,
                GraphRelationAssertion.normalized_value == item.normalized_value,
            )
        )
        return result.scalar_one()

    async def index_chunk(
        self,
        generation_id: uuid.UUID,
        chunk: DocumentChunk,
        extraction: GraphExtraction,
    ) -> GraphIndexResult:
        result = GraphIndexResult(0, 0, 0, 0)
        source_identity = immutable_source_identity(
            document_id=chunk.document_id,
            generation_id=generation_id,
            revision_set_id=chunk.revision_set_id,
            page_revision_id=chunk.page_revision_id,
            chunk_id=chunk.id,
            source_text_sha256=chunk.source_text_sha256,
        )

        entity_map = {}
        for item in extraction.entities:
            entity = await self._upsert_entity(chunk.patient_id, item.entity_type, item.normalized_label)
            entity_map[item.normalized_label] = entity.id
            result.entities_inserted += 1

            mention_inserted = await self._insert_ignore(
                GraphMention,
                {
                    "id": deterministic_provenance_id(
                        kind="mention", owner_id=entity.id, source_identity=source_identity
                    ),
                    "patient_id": chunk.patient_id,
                    "entity_id": entity.id,
                    "generation_id": generation_id,
                    "document_id": chunk.document_id,
                    "revision_set_id": chunk.revision_set_id,
                    "page_revision_id": chunk.page_revision_id,
                    "chunk_id": chunk.id,
                    "independent_source_identity": source_identity,
                },
                ("id",),
            )
            result.mentions_inserted += int(mention_inserted)

        for item in extraction.relations:
            subject_id = entity_map.get(item.subject_label)
            object_id = entity_map.get(item.object_label)

            if not subject_id or not object_id:
                # If entities were somehow not matched/upserted, skip this relation
                continue

            assertion = await self._upsert_assertion(chunk.patient_id, subject_id, object_id, item)
            result.assertions_inserted += 1

            evidence_inserted = await self._insert_ignore(
                GraphRelationEvidence,
                {
                    "id": deterministic_provenance_id(
                        kind="evidence", owner_id=assertion.id, source_identity=source_identity
                    ),
                    "patient_id": chunk.patient_id,
                    "assertion_id": assertion.id,
                    "generation_id": generation_id,
                    "document_id": chunk.document_id,
                    "revision_set_id": chunk.revision_set_id,
                    "page_revision_id": chunk.page_revision_id,
                    "chunk_id": chunk.id,
                    "independent_source_identity": source_identity,
                },
                ("id",),
            )
            result.evidence_inserted += int(evidence_inserted)

        return result
