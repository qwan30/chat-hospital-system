"""Graph RAG — SQL-backed entity-relationship extraction and traversal.

This is a lightweight "graph RAG" implementation that uses SQL tables to
store entities (medical terms, drug names, conditions, etc.) and their
relationships extracted from document chunks.  It provides an alternative
retrieval path that complements vector similarity search with structured
relationship traversal.

## Architecture

    Document chunks → entity_extraction() → GraphEntity + GraphRelation rows
    Query → extract_query_entities() → SQL traversal → related chunks

This avoids a dedicated graph database (Neo4j/ArangoDB) by leveraging the
existing PostgreSQL / SQLite database.  A future migration can promote
these tables into a true graph engine.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy import String, Text, ForeignKey, Integer, Float, func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from hospital_ai.db.models import Base, TimestampMixin


# ── ORM Models ──────────────────────────────────────────────────────────


class GraphEntity(TimestampMixin, Base):
    """A named entity extracted from document text (e.g. drug, condition, lab)."""

    __tablename__ = "graph_entities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_chunk_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_chunks.id"), nullable=False, index=True
    )
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id"), nullable=False, index=True
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)


class GraphRelation(TimestampMixin, Base):
    """A relationship between two entities (e.g. 'treats', 'causes', 'contraindicates')."""

    __tablename__ = "graph_relations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_entity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("graph_entities.id"), nullable=False, index=True
    )
    target_entity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("graph_entities.id"), nullable=False, index=True
    )
    relation_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    source_chunk_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_chunks.id"), nullable=False, index=True
    )


# ── Data classes ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ExtractedEntity:
    name: str
    entity_type: str
    confidence: float = 1.0


@dataclass(frozen=True)
class ExtractedRelation:
    source_name: str
    target_name: str
    relation_type: str
    weight: float = 1.0


@dataclass(frozen=True)
class GraphContext:
    """Context retrieved via graph traversal."""
    entities: List[ExtractedEntity]
    relations: List[ExtractedRelation]
    related_chunk_ids: Set[uuid.UUID]
    summary: str


# ── Entity extraction (heuristic) ────────────────────────────────────────

# Patterns for common medical entities
DRUG_PATTERN = re.compile(
    r"\b(aspirin|metformin|lisinopril|amlodipine|atorvastatin|omeprazole|"
    r"amoxicillin|vancomycin|ciprofloxacin|warfarin|heparin|insulin|"
    r"ibuprofen|acetaminophen|prednisone|hydrochlorothiazide|"
    r"gabapentin|sertraline|fluoxetine|clopidogrel)\b",
    re.IGNORECASE,
)

CONDITION_PATTERN = re.compile(
    r"\b(hypertension|diabetes|pneumonia|sepsis|heart failure|"
    r"atrial fibrillation|copd|asthma|obesity|anemia|"
    r"chronic kidney disease|stroke|myocardial infarction|"
    r"urinary tract infection|cellulitis|deep vein thrombosis)\b",
    re.IGNORECASE,
)

LAB_PATTERN = re.compile(
    r"\b(hemoglobin|hematocrit|wbc|platelet|creatinine|bun|"
    r"glucose|hba1c|troponin|bnp|alt|ast|albumin|bilirubin|"
    r"sodium|potassium|chloride|bicarbonate|inr|ptt)\b",
    re.IGNORECASE,
)

RELATION_PATTERNS = [
    (re.compile(r"(\w+)\s+(?:treats?|for treatment of)\s+(\w+)", re.IGNORECASE), "treats"),
    (re.compile(r"(\w+)\s+(?:causes?|leads? to)\s+(\w+)", re.IGNORECASE), "causes"),
    (re.compile(r"(\w+)\s+(?:contraindicat\w+)\s+(\w+)", re.IGNORECASE), "contraindicates"),
    (re.compile(r"(\w+)\s+(?:interact\w+ with)\s+(\w+)", re.IGNORECASE), "interacts_with"),
]


def extract_entities(text: str) -> List[ExtractedEntity]:
    """Extract medical entities from text using pattern matching."""
    entities: Dict[str, ExtractedEntity] = {}

    for match in DRUG_PATTERN.finditer(text):
        name = match.group(1).lower()
        entities[name] = ExtractedEntity(name=name, entity_type="drug")

    for match in CONDITION_PATTERN.finditer(text):
        name = match.group(1).lower()
        entities[name] = ExtractedEntity(name=name, entity_type="condition")

    for match in LAB_PATTERN.finditer(text):
        name = match.group(1).lower()
        entities[name] = ExtractedEntity(name=name, entity_type="lab")

    return list(entities.values())


def extract_relations(text: str, entities: List[ExtractedEntity]) -> List[ExtractedRelation]:
    """Extract relations between entities found in the text."""
    entity_names = {e.name for e in entities}
    relations: List[ExtractedRelation] = []

    for pattern, relation_type in RELATION_PATTERNS:
        for match in pattern.finditer(text):
            source = match.group(1).lower()
            target = match.group(2).lower()
            if source in entity_names and target in entity_names:
                relations.append(
                    ExtractedRelation(
                        source_name=source,
                        target_name=target,
                        relation_type=relation_type,
                    )
                )

    # Co-occurrence: if a drug and condition appear in the same sentence,
    # infer a weak "mentioned_with" relationship.
    sentences = re.split(r"[.!?]+", text)
    for sentence in sentences:
        sentence_lower = sentence.lower()
        drugs_in_sentence = [e for e in entities if e.entity_type == "drug" and e.name in sentence_lower]
        conditions_in_sentence = [e for e in entities if e.entity_type == "condition" and e.name in sentence_lower]

        for drug in drugs_in_sentence:
            for condition in conditions_in_sentence:
                relations.append(
                    ExtractedRelation(
                        source_name=drug.name,
                        target_name=condition.name,
                        relation_type="mentioned_with",
                        weight=0.5,
                    )
                )

    return relations


# ── Database operations ──────────────────────────────────────────────────


async def index_chunk_entities(
    session: AsyncSession,
    chunk_id: uuid.UUID,
    document_id: uuid.UUID,
    content: str,
) -> Tuple[List[GraphEntity], List[GraphRelation]]:
    """Extract and persist entities and relations from a chunk."""
    entities = extract_entities(content)
    relations = extract_relations(content, entities)

    entity_rows: Dict[str, GraphEntity] = {}
    for entity in entities:
        row = GraphEntity(
            name=entity.name,
            entity_type=entity.entity_type,
            source_chunk_id=chunk_id,
            source_document_id=document_id,
            confidence=entity.confidence,
        )
        session.add(row)
        entity_rows[entity.name] = row

    await session.flush()

    relation_rows: List[GraphRelation] = []
    for relation in relations:
        source = entity_rows.get(relation.source_name)
        target = entity_rows.get(relation.target_name)
        if source and target:
            row = GraphRelation(
                source_entity_id=source.id,
                target_entity_id=target.id,
                relation_type=relation.relation_type,
                weight=relation.weight,
                source_chunk_id=chunk_id,
            )
            session.add(row)
            relation_rows.append(row)

    return list(entity_rows.values()), relation_rows


async def find_related_entities(
    session: AsyncSession,
    entity_names: List[str],
    *,
    max_hops: int = 2,
    patient_id: Optional[uuid.UUID] = None,
) -> GraphContext:
    """Find entities related to the given names via graph traversal.

    F-RAG-003: when ``patient_id`` is provided every seed lookup, relation
    traversal, and entity expansion is restricted to chunks owned by that
    patient, so the returned ``GraphContext`` (including its summary and
    entity list) cannot leak data sourced from another patient's records.

    ``patient_id=None`` returns a cross-patient view and is intended only
    for offline analytics. Caller paths that surface ``GraphContext``
    fields to a user (summary, entities, relations) MUST pass a non-None
    ``patient_id``.
    """
    if not entity_names:
        return GraphContext(entities=[], relations=[], related_chunk_ids=set(), summary="No entities to query.")

    # Normalize
    normalized = [name.lower() for name in entity_names]

    # Lazy import to avoid a circular dependency between the graph_rag
    # module (registered against `Base`) and the wider models module that
    # imports services for relationship targets.
    from hospital_ai.db.models import DocumentChunk

    def _scope_to_patient(stmt):
        if patient_id is None:
            return stmt
        allowed_chunks = (
            select(DocumentChunk.id)
            .where(DocumentChunk.patient_id == patient_id)
            .scalar_subquery()
        )
        return stmt.where(GraphEntity.source_chunk_id.in_(allowed_chunks))

    def _scope_relations_to_patient(stmt):
        if patient_id is None:
            return stmt
        allowed_chunks = (
            select(DocumentChunk.id)
            .where(DocumentChunk.patient_id == patient_id)
            .scalar_subquery()
        )
        return stmt.where(GraphRelation.source_chunk_id.in_(allowed_chunks))

    # Find seed entities (patient-scoped).
    result = await session.execute(
        _scope_to_patient(
            select(GraphEntity).where(func.lower(GraphEntity.name).in_(normalized))
        )
    )
    seed_entities = list(result.scalars().all())

    if not seed_entities:
        return GraphContext(
            entities=[],
            relations=[],
            related_chunk_ids=set(),
            summary=f"No graph entities found for: {', '.join(entity_names)}",
        )

    # BFS traversal (patient-scoped at every hop).
    visited_ids: Set[uuid.UUID] = {e.id for e in seed_entities}
    all_entities = list(seed_entities)
    all_relations: List[GraphRelation] = []
    frontier_ids = visited_ids.copy()

    for _ in range(max_hops):
        if not frontier_ids:
            break

        result = await session.execute(
            _scope_relations_to_patient(
                select(GraphRelation).where(
                    or_(
                        GraphRelation.source_entity_id.in_(frontier_ids),
                        GraphRelation.target_entity_id.in_(frontier_ids),
                    )
                )
            )
        )
        relations = list(result.scalars().all())
        all_relations.extend(relations)

        next_frontier: Set[uuid.UUID] = set()
        for rel in relations:
            for eid in (rel.source_entity_id, rel.target_entity_id):
                if eid not in visited_ids:
                    next_frontier.add(eid)
                    visited_ids.add(eid)

        if next_frontier:
            result = await session.execute(
                _scope_to_patient(
                    select(GraphEntity).where(GraphEntity.id.in_(next_frontier))
                )
            )
            new_entities = list(result.scalars().all())
            all_entities.extend(new_entities)

        frontier_ids = next_frontier

    # Collect related chunk IDs
    chunk_ids: Set[uuid.UUID] = set()
    for entity in all_entities:
        chunk_ids.add(entity.source_chunk_id)
    for relation in all_relations:
        chunk_ids.add(relation.source_chunk_id)

    # Build summary
    entity_list = [
        ExtractedEntity(name=e.name, entity_type=e.entity_type, confidence=e.confidence)
        for e in all_entities
    ]
    relation_list = []
    entity_id_to_name = {e.id: e.name for e in all_entities}
    for rel in all_relations:
        src_name = entity_id_to_name.get(rel.source_entity_id, "?")
        tgt_name = entity_id_to_name.get(rel.target_entity_id, "?")
        relation_list.append(
            ExtractedRelation(
                source_name=src_name,
                target_name=tgt_name,
                relation_type=rel.relation_type,
                weight=rel.weight,
            )
        )

    summary_parts = [f"Found {len(entity_list)} entities and {len(relation_list)} relations."]
    for e in entity_list[:5]:
        summary_parts.append(f"  - {e.name} ({e.entity_type})")
    if len(entity_list) > 5:
        summary_parts.append(f"  ... and {len(entity_list) - 5} more")

    return GraphContext(
        entities=entity_list,
        relations=relation_list,
        related_chunk_ids=chunk_ids,
        summary="\n".join(summary_parts),
    )
