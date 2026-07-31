"""Graph RAG — SQL-backed entity-relationship extraction and traversal.

This is a lightweight "graph RAG" implementation that uses SQL tables to
store entities (medical terms, drug names, conditions, etc.) and their
relationships extracted from document chunks.  It provides an alternative
retrieval path that complements vector similarity search with structured
relationship traversal.

## Architecture

    Document chunks → LLM extraction → GraphEntity + GraphRelation rows
    Query → extract query terms → SQL traversal → related chunks

This avoids a dedicated graph database (Neo4j/ArangoDB) by leveraging the
existing PostgreSQL / SQLite database.  A future migration can promote
these tables into a true graph engine.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Optional
from typing_extensions import TypeAlias

from sqlalchemy import Float, ForeignKey, String, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from hospital_ai.db.models import Base, TimestampMixin
from hospital_ai.services.llm.base import LLMMessage
from hospital_ai.services.llm.manager import get_llm_manager

# ── ORM Models ──────────────────────────────────────────────────────────


class GraphEntity(TimestampMixin, Base):
    """A named entity extracted from document text (e.g. drug, condition, lab)."""

    __tablename__ = "graph_entities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_chunks.id"), nullable=False, index=True)
    source_document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)


class GraphRelation(TimestampMixin, Base):
    """A relationship between two entities (e.g. 'treats', 'causes', 'contraindicates')."""

    __tablename__ = "graph_relations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("graph_entities.id"), nullable=False, index=True)
    target_entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("graph_entities.id"), nullable=False, index=True)
    relation_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    source_chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_chunks.id"), nullable=False, index=True)


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

    entities: list[ExtractedEntity]
    relations: list[ExtractedRelation]
    related_chunk_ids: set[uuid.UUID]
    summary: str


EntityRelationExtractor: TypeAlias = Callable[[str], Awaitable[tuple[list[ExtractedEntity], list[ExtractedRelation]]]]


# ── Entity extraction (NLP) ──────────────────────────────────────────────


_EXPLICIT_RELATION_PATTERN = re.compile(
    r"(?P<source>[A-Za-z][A-Za-z0-9 _-]{0,79}?)\s+"
    r"(?:(?:also|directly)\s+)?"
    r"(?P<relation>treats|causes|contraindicates|prescribed[_ ]for|has[_ ]symptom)\s+"
    r"(?P<target>[A-Za-z][A-Za-z0-9 _-]{0,79}?)(?=[.,;]|$)",
    re.IGNORECASE,
)

_LAB_OBSERVATION_FIELDS = ("mrn", "analyte", "status")


def _extract_labeled_lab_observation(content: str) -> tuple[list[ExtractedEntity], list[ExtractedRelation]]:
    """Build a clinical observation graph from complete, explicitly labeled CSV fields.

    The parser intentionally rejects incomplete or duplicate fields.  It does
    not infer a patient, analyte, or status from prose; each graph edge is
    justified by a source-literal lab field.
    """
    values_by_field: dict[str, list[str]] = {}
    for line in content.splitlines():
        field, separator, value = line.partition(":")
        normalized_field = field.strip().casefold()
        if separator and normalized_field in _LAB_OBSERVATION_FIELDS:
            values_by_field.setdefault(normalized_field, []).append(value.strip())

    if any(len(values_by_field.get(field, ())) != 1 for field in _LAB_OBSERVATION_FIELDS):
        return [], []

    mrn, analyte, status = (values_by_field[field][0] for field in _LAB_OBSERVATION_FIELDS)
    if any(not value or len(value) > 200 for value in (mrn, analyte, status)):
        return [], []

    patient_node = f"patient:{mrn.casefold()}"
    analyte_node = f"analyte:{analyte.casefold()}"
    status_node = f"status:{status.casefold()}"
    entities = [
        ExtractedEntity(patient_node, "patient"),
        ExtractedEntity(analyte_node, "lab_analyte"),
        ExtractedEntity(status_node, "lab_status"),
    ]
    relations = [
        ExtractedRelation(patient_node, analyte_node, "has_observation"),
        ExtractedRelation(analyte_node, status_node, "has_status"),
    ]
    return entities, relations


def _extract_explicit_relations_fallback(content: str) -> tuple[list[ExtractedEntity], list[ExtractedRelation]]:
    """Extract only explicit graph relations when an LLM response is unavailable.

    The fallback intentionally does not infer relations: it recognizes a small,
    deterministic grammar so offline safety evaluations can validate the same
    patient-scoped graph traversal as production indexing.
    """
    lab_entities, lab_relations = _extract_labeled_lab_observation(content)
    entities: dict[str, ExtractedEntity] = {entity.name: entity for entity in lab_entities}
    relations: list[ExtractedRelation] = list(lab_relations)
    seen_relations: set[tuple[str, str, str]] = {
        (relation.source_name, relation.target_name, relation.relation_type) for relation in relations
    }

    for match in _EXPLICIT_RELATION_PATTERN.finditer(content):
        source = match.group("source").strip().casefold()
        target = match.group("target").strip().casefold()
        relation_type = match.group("relation").casefold().replace(" ", "_")
        relation_key = (source, target, relation_type)
        if relation_key in seen_relations:
            continue

        seen_relations.add(relation_key)
        entities.setdefault(source, ExtractedEntity(source, "concept"))
        entities.setdefault(target, ExtractedEntity(target, "concept"))
        relations.append(ExtractedRelation(source, target, relation_type))

    return list(entities.values()), relations


async def extract_entities_and_relations_offline(
    content: str,
) -> tuple[list[ExtractedEntity], list[ExtractedRelation]]:
    """Extract explicit graph relations without initializing an LLM provider."""
    return _extract_explicit_relations_fallback(content)


async def extract_entities_and_relations_nlp(content: str) -> tuple[list[ExtractedEntity], list[ExtractedRelation]]:
    """Extract entities and relations from text using the LLM via Proposition Transfer."""
    llm = get_llm_manager().get()

    prompt = (
        "You are a medical NLP engine. Your task is to extract medical entities "
        "and explicitly stated relations from the provided text.\n"
        "Entities must be medical concepts such as conditions, drugs, labs, symptoms, or procedures.\n"
        "Explicit relations must be one of: treats, causes, contraindicates, "
        "prescribed_for, has_symptom. Do NOT extract fuzzy 'mentioned_with' relations.\n"
        "Only extract a relation if the text explicitly states or strongly implies it "
        '(e.g. "X treats Y", "X causes Y").\n'
        "\n"
        "Respond ONLY with valid JSON in the exact following format, without markdown wrapping:\n"
        "{\n"
        '  "entities": [\n'
        '    {"name": "entity name in lowercase", "entity_type": "drug"}\n'
        "  ],\n"
        '  "relations": [\n'
        '    {"source_name": "entity 1", "target_name": "entity 2", "relation_type": "treats"}\n'
        "  ]\n"
        "}"
    )

    messages = [
        LLMMessage(role="system", content=prompt),
        LLMMessage(role="user", content=content),
    ]

    try:
        response = await llm.generate(messages, temperature=0.0)
        text = response.text.strip()

        # Robust JSON extraction via regex (handles conversational filler)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)

        data = json.loads(text.strip())

        entities = []
        for e in data.get("entities", []):
            entities.append(
                ExtractedEntity(
                    name=e["name"].lower(),
                    entity_type=e["entity_type"].lower(),
                    confidence=1.0,
                )
            )

        relations = []
        for r in data.get("relations", []):
            relations.append(
                ExtractedRelation(
                    source_name=r["source_name"].lower(),
                    target_name=r["target_name"].lower(),
                    relation_type=r["relation_type"].lower(),
                    weight=1.0,
                )
            )

        return entities, relations
    except Exception as e:
        logging.getLogger(__name__).warning("NLP extraction failed: %s", e)
        return _extract_explicit_relations_fallback(content)


# ── Database operations ──────────────────────────────────────────────────


async def index_chunk_entities(
    session: AsyncSession,
    chunk_id: uuid.UUID,
    document_id: uuid.UUID,
    content: str,
    *,
    extractor: EntityRelationExtractor | None = None,
) -> tuple[list[GraphEntity], list[GraphRelation]]:
    """Replace a chunk's graph projection with freshly extracted entities.

    ``extractor`` defaults to production LLM-backed extraction. Offline callers
    can explicitly provide :func:`extract_entities_and_relations_offline`.
    """
    await session.execute(delete(GraphRelation).where(GraphRelation.source_chunk_id == chunk_id))
    await session.execute(delete(GraphEntity).where(GraphEntity.source_chunk_id == chunk_id))
    active_extractor = extract_entities_and_relations_nlp if extractor is None else extractor
    entities, relations = await active_extractor(content)

    entity_rows: dict[str, GraphEntity] = {}
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

    relation_rows: list[GraphRelation] = []
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
    entity_names: list[str],
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
    from hospital_ai.db.models import Document, DocumentChunk, DocumentPage

    allowed_chunks = None
    if patient_id is not None:
        allowed_chunks = (
            select(DocumentChunk.id)
            .join(Document, Document.id == DocumentChunk.document_id)
            .join(
                DocumentPage,
                (DocumentPage.id == DocumentChunk.page_id) & (DocumentPage.document_id == DocumentChunk.document_id),
            )
            .where(
                DocumentChunk.patient_id == patient_id,
                Document.patient_id == patient_id,
                Document.status == "indexed",
                DocumentChunk.deleted_at.is_(None),
                Document.deleted_at.is_(None),
                DocumentPage.deleted_at.is_(None),
            )
            .scalar_subquery()
        )

    def _scope_to_patient(stmt):
        if allowed_chunks is None:
            return stmt
        return stmt.where(GraphEntity.source_chunk_id.in_(allowed_chunks))

    def _scope_relations_to_patient(stmt):
        if allowed_chunks is None:
            return stmt
        return stmt.where(GraphRelation.source_chunk_id.in_(allowed_chunks))

    # Find seed entities (patient-scoped).
    result = await session.execute(
        _scope_to_patient(select(GraphEntity).where(func.lower(GraphEntity.name).in_(normalized)))
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
    visited_ids: set[uuid.UUID] = {e.id for e in seed_entities}
    visited_relation_ids: set[uuid.UUID] = set()
    all_entities = list(seed_entities)
    all_relations: list[GraphRelation] = []
    frontier_ids = visited_ids.copy()

    for _ in range(max_hops):
        if not frontier_ids:
            break

        result = await session.execute(
            _scope_relations_to_patient(
                select(GraphRelation)
                .where(
                    or_(
                        GraphRelation.source_entity_id.in_(frontier_ids),
                        GraphRelation.target_entity_id.in_(frontier_ids),
                    )
                )
                .where(GraphRelation.relation_type != "mentioned_with")
            )
        )
        relations = list(result.scalars().all())

        new_relations = [r for r in relations if r.id not in visited_relation_ids]
        all_relations.extend(new_relations)
        for r in new_relations:
            visited_relation_ids.add(r.id)

        next_frontier: set[uuid.UUID] = set()
        for rel in new_relations:
            for eid in (rel.source_entity_id, rel.target_entity_id):
                if eid not in visited_ids:
                    next_frontier.add(eid)
                    visited_ids.add(eid)

        if next_frontier:
            result = await session.execute(
                _scope_to_patient(select(GraphEntity).where(GraphEntity.id.in_(next_frontier)))
            )
            new_entities = list(result.scalars().all())
            all_entities.extend(new_entities)

            # Expand next_frontier by name to enable cross-chunk traversal
            new_entity_names = {e.name.lower() for e in new_entities}
            if new_entity_names:
                expanded_result = await session.execute(
                    _scope_to_patient(select(GraphEntity.id).where(func.lower(GraphEntity.name).in_(new_entity_names)))
                )
                expanded_ids = set(expanded_result.scalars().all())
                for eid in expanded_ids:
                    if eid not in visited_ids:
                        next_frontier.add(eid)
                        visited_ids.add(eid)

        frontier_ids = next_frontier

    # Collect related chunk IDs
    chunk_ids: set[uuid.UUID] = set()
    for entity in all_entities:
        chunk_ids.add(entity.source_chunk_id)
    for relation in all_relations:
        chunk_ids.add(relation.source_chunk_id)

    # Build summary
    entity_list = [
        ExtractedEntity(name=e.name, entity_type=e.entity_type, confidence=e.confidence) for e in all_entities
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
