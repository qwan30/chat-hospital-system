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

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.db.clinical_graph import LegacyGraphEntity as GraphEntity
from hospital_ai.db.clinical_graph import LegacyGraphRelation as GraphRelation
from hospital_ai.services.llm.base import LLMMessage
from hospital_ai.services.llm.manager import get_llm_manager

logger = logging.getLogger(__name__)

# ── ORM Models ──────────────────────────────────────────────────────────


# ── Ontology & Allowlist ──────────────────────────────────────────────────

CANONICAL_PATIENT_ANCHOR = "patient:self"

VALID_RELATION_TYPES = frozenset(
    [
        "treats",
        "causes",
        "contraindicates",
        "prescribed_for",
        "has_symptom",
        "indicates",
        "interacts_with",
        "diagnosed_with",
        "history_of",
        "allergic_to",
        "has_observation",
        "has_status",
    ]
)


def validate_relation_type(relation: str) -> Optional[str]:
    """Validate and normalize a relation type against the allowed clinical vocabulary."""
    normalized = relation.strip().casefold().replace(" ", "_")
    if normalized in VALID_RELATION_TYPES:
        return normalized
    return None


# ── Data classes ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ExtractedEntity:
    normalized_label: str
    entity_type: str
    confidence: float = 1.0

    @property
    def name(self) -> str:
        """Compatibility name used by the pre-provenance graph contract."""
        return self.normalized_label


@dataclass(frozen=True)
class ExtractedRelation:
    subject_label: str
    object_label: str
    relation_type: str
    normalized_value: str = ""
    weight: float = 1.0
    severity: Optional[str] = None
    source_layer: str = "nlp"

    def __post_init__(self):
        if not self.normalized_value:
            object.__setattr__(self, "normalized_value", self.relation_type)

    @property
    def source_name(self) -> str:
        """Compatibility name used by the pre-provenance graph contract."""
        return self.subject_label

    @property
    def target_name(self) -> str:
        """Compatibility name used by the pre-provenance graph contract."""
        return self.object_label


@dataclass(frozen=True)
class GraphExtraction:
    entities: list[ExtractedEntity]
    relations: list[ExtractedRelation]


@dataclass(frozen=True)
class GraphContext:
    """Context retrieved via graph traversal."""

    entities: list[ExtractedEntity]
    relations: list[ExtractedRelation]
    related_chunk_ids: set[uuid.UUID]
    summary: str


EntityRelationExtractor = Callable[[str], Awaitable[tuple[list[ExtractedEntity], list[ExtractedRelation]]]]


# ── Entity extraction (NLP & Grammar) ───────────────────────────────────


_EXPLICIT_RELATION_PATTERN = re.compile(
    r"(?P<source>[A-Za-z][A-Za-z0-9 _-]{0,79}?)\s+"
    r"(?:(?:also|directly|clearly)\s+)?"
    r"(?P<relation>treats|causes|contraindicates|prescribed[_ ]for|has[_ ]symptom|indicates|interacts[_ ]with)\s+"
    r"(?P<target>[A-Za-z][A-Za-z0-9 _-]{0,79}?)(?=[.,;]|$)",
    re.IGNORECASE,
)

_PATIENT_DIAGNOSIS_PATTERN = re.compile(
    r"(?:patient\s+(?:is\s+)?(?:diagnosed|admitted)\s+with|diagnosis\s+of)\s+"
    r"(?P<target>[A-Za-z0-9 _-]{2,60}?)(?=[.,;]|$)",
    re.IGNORECASE,
)

_PATIENT_HISTORY_PATTERN = re.compile(
    r"(?:(?:past\s+medical\s+)?history\s+of|prior\s+history\s+of)\s+(?P<target>[A-Za-z0-9 _-]{2,60}?)(?=[.,;]|$)",
    re.IGNORECASE,
)

_PATIENT_ALLERGY_PATTERN = re.compile(
    r"(?:(?:confirmed\s+)?allerg(?:y|ic)\s+to)\s+(?P<target>[A-Za-z0-9 _-]{2,60}?)(?=[.,;]|$)",
    re.IGNORECASE,
)

_NEGATION_CUE_PATTERN = re.compile(
    r"\b(no\s+known|no\s+history|no\s+prior|nkda|nka|denies|denied|ruled\s+out|without|none\s+reported|negative\s+for|no\s+allerg)\b",
    re.IGNORECASE,
)

_LAB_OBSERVATION_FIELDS = ("mrn", "analyte", "status")


def _is_clause_negated(clause: str) -> bool:
    """Check if a specific clinical sentence or clause contains a negation cue."""
    return bool(_NEGATION_CUE_PATTERN.search(clause))


def _split_clinical_clauses(content: str) -> list[str]:
    """Split clinical text into clauses by punctuation to localize negation scope."""
    # Split by periods, semicolons, and newlines
    clauses = re.split(r"[.;\n]+", content)
    return [c.strip() for c in clauses if c.strip()]


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
        ExtractedRelation(patient_node, analyte_node, "has_observation", source_layer="grammar"),
        ExtractedRelation(analyte_node, status_node, "has_status", source_layer="grammar"),
    ]
    return entities, relations


def _extract_explicit_relations_fallback(content: str) -> tuple[list[ExtractedEntity], list[ExtractedRelation]]:
    """Extract only explicit graph relations when an LLM response is unavailable.

    The fallback intentionally does not infer relations: it recognizes a small,
    deterministic grammar so offline safety evaluations can validate the same
    patient-scoped graph traversal as production indexing.
    """
    lab_entities, lab_relations = _extract_labeled_lab_observation(content)
    entities: dict[str, ExtractedEntity] = {entity.normalized_label: entity for entity in lab_entities}
    relations: list[ExtractedRelation] = list(lab_relations)
    seen_relations: set[tuple[str, str, str]] = {
        (relation.subject_label, relation.object_label, relation.relation_type) for relation in relations
    }

    clauses = _split_clinical_clauses(content)
    for clause in clauses:
        is_negated = _is_clause_negated(clause)

        # 1. Concept-to-concept explicit relations (treats, causes, contraindicates, indicates, etc.)
        for match in _EXPLICIT_RELATION_PATTERN.finditer(clause):
            if is_negated:
                continue
            source = match.group("source").strip().casefold()
            target = match.group("target").strip().casefold()
            raw_relation = match.group("relation").casefold().replace(" ", "_")
            valid_rel = validate_relation_type(raw_relation)
            if not valid_rel or not source or not target:
                continue

            relation_key = (source, target, valid_rel)
            if relation_key not in seen_relations:
                seen_relations.add(relation_key)
                entities.setdefault(source, ExtractedEntity(source, "concept"))
                entities.setdefault(target, ExtractedEntity(target, "concept"))
                relations.append(ExtractedRelation(source, target, valid_rel, source_layer="grammar"))

        # 2. Patient-anchored diagnoses (diagnosed_with)
        for match in _PATIENT_DIAGNOSIS_PATTERN.finditer(clause):
            if is_negated:
                continue
            target = match.group("target").strip().casefold()
            if not target:
                continue
            relation_key = (CANONICAL_PATIENT_ANCHOR, target, "diagnosed_with")
            if relation_key not in seen_relations:
                seen_relations.add(relation_key)
                entities.setdefault(
                    CANONICAL_PATIENT_ANCHOR, ExtractedEntity(CANONICAL_PATIENT_ANCHOR, "patient_anchor")
                )
                entities.setdefault(target, ExtractedEntity(target, "condition"))
                relations.append(
                    ExtractedRelation(CANONICAL_PATIENT_ANCHOR, target, "diagnosed_with", source_layer="grammar")
                )

        # 3. Patient-anchored history (history_of)
        for match in _PATIENT_HISTORY_PATTERN.finditer(clause):
            if is_negated:
                continue
            target = match.group("target").strip().casefold()
            if not target:
                continue
            relation_key = (CANONICAL_PATIENT_ANCHOR, target, "history_of")
            if relation_key not in seen_relations:
                seen_relations.add(relation_key)
                entities.setdefault(
                    CANONICAL_PATIENT_ANCHOR, ExtractedEntity(CANONICAL_PATIENT_ANCHOR, "patient_anchor")
                )
                entities.setdefault(target, ExtractedEntity(target, "condition"))
                relations.append(
                    ExtractedRelation(CANONICAL_PATIENT_ANCHOR, target, "history_of", source_layer="grammar")
                )

        # 4. Patient-anchored allergies (allergic_to)
        for match in _PATIENT_ALLERGY_PATTERN.finditer(clause):
            if is_negated:
                continue
            target = match.group("target").strip().casefold()
            if not target:
                continue
            relation_key = (CANONICAL_PATIENT_ANCHOR, target, "allergic_to")
            if relation_key not in seen_relations:
                seen_relations.add(relation_key)
                entities.setdefault(
                    CANONICAL_PATIENT_ANCHOR, ExtractedEntity(CANONICAL_PATIENT_ANCHOR, "patient_anchor")
                )
                entities.setdefault(target, ExtractedEntity(target, "drug"))
                relations.append(
                    ExtractedRelation(CANONICAL_PATIENT_ANCHOR, target, "allergic_to", source_layer="grammar")
                )

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
        "and explicitly stated relations from the provided clinical text.\n"
        "Entities must be medical concepts such as conditions, drugs, labs, symptoms, or procedures.\n"
        "Explicit relations must be one of:\n"
        "  - treats, causes, contraindicates, prescribed_for, has_symptom, indicates, interacts_with\n"
        "  - diagnosed_with, history_of, allergic_to (for patient-anchored facts, use source_name: 'patient:self')\n"
        "\n"
        "CRITICAL CLINICAL NEGATION RULES:\n"
        "1. Do NOT extract relations for negated, denied, absent, or ruled-out findings:\n"
        "   - 'NKDA', 'No known drug allergies' -> DO NOT extract allergic_to\n"
        "   - 'Denies chest pain', 'No shortness of breath' -> DO NOT extract has_symptom\n"
        "   - 'Ruled out myocardial infarction' -> DO NOT extract diagnosed_with\n"
        "   - 'No history of asthma' -> DO NOT extract history_of\n"
        "2. Do NOT extract fuzzy 'mentioned_with' relations.\n"
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
            name = e.get("name", "").lower().strip()
            etype = e.get("entity_type", "concept").lower().strip()
            if name:
                entities.append(
                    ExtractedEntity(
                        normalized_label=name,
                        entity_type=etype,
                        confidence=1.0,
                    )
                )

        relations = []
        seen_relations = set()
        for r in data.get("relations", []):
            subject_label = r.get("source_name", r.get("subject_label", "")).lower().strip()
            object_label = r.get("target_name", r.get("object_label", "")).lower().strip()
            raw_relation = r.get("relation_type", "").lower().strip()
            relation_type = validate_relation_type(raw_relation)
            if not subject_label or not object_label or not relation_type:
                continue
            if (subject_label, object_label, relation_type) not in seen_relations:
                seen_relations.add((subject_label, object_label, relation_type))
                relations.append(
                    ExtractedRelation(
                        subject_label=subject_label,
                        object_label=object_label,
                        relation_type=relation_type,
                        weight=1.0,
                        source_layer="nlp",
                    )
                )

        return entities, relations
    except Exception as e:
        logger.warning("NLP extraction failed", extra={"error_code": "NLP_EXTRACTION_FAILED"})
        return _extract_explicit_relations_fallback(content)


# ── Database operations ──────────────────────────────────────────────────


async def index_chunk_entities(
    session: AsyncSession,
    chunk_id: uuid.UUID,
    document_id: uuid.UUID,
    content: str,
    *,
    extractor: Optional[EntityRelationExtractor] = None,
) -> tuple[list, list]:
    import time

    start_time = time.time()
    trace_id = uuid.uuid4().hex

    active_extractor = extract_entities_and_relations_nlp if extractor is None else extractor
    entities, relations = await active_extractor(content)
    logger.info(
        "graph.extraction.completed",
        extra={
            "trace_id": trace_id,
            "document_id": str(document_id),
            "entity_count": len(entities),
            "relation_count": len(relations),
            "latency": time.time() - start_time,
        },
    )

    from hospital_ai.db.clinical_graph import LegacyGraphEntity, LegacyGraphRelation
    from hospital_ai.db.models import DocumentChunk
    from hospital_ai.services.graph_index import GraphIndexService

    chunk = await session.get(DocumentChunk, chunk_id)
    if not chunk:
        logger.warning(
            "graph.chunk.not_found",
            extra={
                "trace_id": trace_id,
                "document_id": str(document_id),
                "chunk_id": str(chunk_id),
                "error_code": "CHUNK_NOT_FOUND",
            },
        )
        return [], []

    from hospital_ai.services.graph_rag import GraphExtraction

    extraction = GraphExtraction(entities=entities, relations=relations)

    result = await GraphIndexService(session).index_chunk(chunk.generation_id, chunk, extraction)
    logger.info(
        "graph.index.completed",
        extra={
            "trace_id": trace_id,
            "document_id": str(document_id),
            "chunk_id": str(chunk.id),
            "generation_id": str(chunk.generation_id),
            "entities_inserted": result.entities_inserted,
            "mentions_inserted": result.mentions_inserted,
            "assertions_inserted": result.assertions_inserted,
            "evidence_inserted": result.evidence_inserted,
            "latency": time.time() - start_time,
        },
    )
    await session.execute(delete(LegacyGraphRelation).where(LegacyGraphRelation.source_chunk_id == chunk.id))
    await session.execute(delete(LegacyGraphEntity).where(LegacyGraphEntity.source_chunk_id == chunk.id))

    legacy_entities: list[LegacyGraphEntity] = []
    entities_by_label: dict[str, LegacyGraphEntity] = {}
    for item in entities:
        entity = entities_by_label.get(item.normalized_label)
        if entity is None:
            entity = LegacyGraphEntity(
                name=item.normalized_label,
                entity_type=item.entity_type,
                source_chunk_id=chunk.id,
                source_document_id=document_id,
                confidence=item.confidence,
            )
            entities_by_label[item.normalized_label] = entity
            legacy_entities.append(entity)
            session.add(entity)
    await session.flush()

    legacy_relations: list[LegacyGraphRelation] = []
    for item in relations:
        source = entities_by_label.get(item.subject_label)
        target = entities_by_label.get(item.object_label)
        if source is None or target is None:
            continue
        relation = LegacyGraphRelation(
            source_entity_id=source.id,
            target_entity_id=target.id,
            relation_type=item.relation_type,
            weight=item.weight,
            source_chunk_id=chunk.id,
        )
        legacy_relations.append(relation)
        session.add(relation)
    await session.flush()
    return legacy_entities, legacy_relations


async def find_related_entities(
    session: AsyncSession,
    entity_names: list[str],
    *,
    max_hops: int = 2,
    patient_id: Optional[uuid.UUID] = None,
) -> GraphContext:
    if not entity_names:
        return GraphContext(entities=[], relations=[], related_chunk_ids=set(), summary="No entities to query.")

    normalized = [name.lower() for name in entity_names]

    if patient_id is None:
        return await _find_related_legacy_entities(session, normalized, entity_names, max_hops=max_hops)

    from hospital_ai.db.clinical_graph import GraphEntity, GraphRelationAssertion, GraphRelationEvidence
    from hospital_ai.db.models import Document, DocumentChunk

    allowed_chunks = None
    if patient_id is not None:
        from hospital_ai.db.models import DocumentPage

        allowed_chunks = (
            select(DocumentChunk.id)
            .join(Document, Document.id == DocumentChunk.document_id)
            .join(DocumentPage, DocumentPage.id == DocumentChunk.page_id)
            .where(
                DocumentChunk.patient_id == patient_id,
                Document.patient_id == patient_id,
                Document.status.in_(("ready", "ready_with_warnings")),
                DocumentChunk.deleted_at.is_(None),
                Document.deleted_at.is_(None),
                DocumentPage.deleted_at.is_(None),
                DocumentChunk.generation_id == Document.active_index_generation_id,
            )
            .scalar_subquery()
        )

    def _scope_to_patient(stmt):
        if patient_id is not None:
            return stmt.where(GraphEntity.patient_id == patient_id)
        return stmt

    def _scope_relations_to_patient(stmt):
        if patient_id is not None:
            return stmt.where(GraphRelationAssertion.patient_id == patient_id)
        return stmt

    result = await session.execute(
        _scope_to_patient(select(GraphEntity).where(func.lower(GraphEntity.normalized_label).in_(normalized)))
    )
    seed_entities = list(result.scalars().all())

    if not seed_entities:
        return GraphContext(
            entities=[],
            relations=[],
            related_chunk_ids=set(),
            summary=f"No graph entities found for: {', '.join(entity_names)}",
        )

    visited_ids: set[uuid.UUID] = {e.id for e in seed_entities}
    visited_relation_ids: set[uuid.UUID] = set()
    all_entities = list(seed_entities)
    all_relations: list[GraphRelationAssertion] = []
    frontier_ids = visited_ids.copy()

    for _ in range(max_hops):
        if not frontier_ids:
            break

        result = await session.execute(
            _scope_relations_to_patient(
                select(GraphRelationAssertion).where(
                    or_(
                        GraphRelationAssertion.subject_entity_id.in_(frontier_ids),
                        GraphRelationAssertion.object_entity_id.in_(frontier_ids),
                    )
                )
            )
        )
        relations = list(result.scalars().all())

        new_relations = [r for r in relations if r.id not in visited_relation_ids]
        all_relations.extend(new_relations)
        for r in new_relations:
            visited_relation_ids.add(r.id)

        next_frontier: set[uuid.UUID] = set()
        for rel in new_relations:
            for eid in (rel.subject_entity_id, rel.object_entity_id):
                if eid not in visited_ids:
                    next_frontier.add(eid)
                    visited_ids.add(eid)

        if next_frontier:
            result = await session.execute(
                _scope_to_patient(select(GraphEntity).where(GraphEntity.id.in_(next_frontier)))
            )
            new_entities = list(result.scalars().all())
            all_entities.extend(new_entities)
            # Traversal Guard: Do NOT expand outward from patient:self hub node into unrelated conditions
            frontier_ids = {e.id for e in new_entities if e.normalized_label != CANONICAL_PATIENT_ANCHOR}
        else:
            frontier_ids = set()

    chunk_ids: set[uuid.UUID] = set()
    if patient_id is not None and all_relations:
        assertion_ids = [r.id for r in all_relations]
        # Query GraphRelationEvidence to find supporting chunks
        result = await session.execute(
            select(GraphRelationEvidence.chunk_id)
            .where(GraphRelationEvidence.assertion_id.in_(assertion_ids))
            .where(GraphRelationEvidence.chunk_id.in_(allowed_chunks))
        )
        chunk_ids.update(result.scalars().all())
    elif all_relations:
        assertion_ids = [r.id for r in all_relations]
        result = await session.execute(
            select(GraphRelationEvidence.chunk_id).where(GraphRelationEvidence.assertion_id.in_(assertion_ids))
        )
        chunk_ids.update(result.scalars().all())

    entity_list = [
        ExtractedEntity(normalized_label=e.normalized_label, entity_type=e.entity_type, confidence=1.0)
        for e in all_entities
    ]
    relation_list = []
    entity_id_to_name = {e.id: e.normalized_label for e in all_entities}
    for rel in all_relations:
        src_name = entity_id_to_name.get(rel.subject_entity_id, "?")
        tgt_name = entity_id_to_name.get(rel.object_entity_id, "?")
        relation_list.append(
            ExtractedRelation(
                subject_label=src_name,
                object_label=tgt_name,
                relation_type=rel.relation_type,
                weight=1.0,
            )
        )

    summary_parts = [f"Found {len(entity_list)} entities and {len(relation_list)} relations."]
    for e in entity_list[:5]:
        summary_parts.append(f"- {e.normalized_label} ({e.entity_type})")
    if len(entity_list) > 5:
        summary_parts.append("...")

    return GraphContext(
        entities=entity_list,
        relations=relation_list,
        related_chunk_ids=chunk_ids,
        summary="\n".join(summary_parts),
    )


async def _find_related_legacy_entities(
    session: AsyncSession,
    normalized_names: list[str],
    original_names: list[str],
    *,
    max_hops: int,
) -> GraphContext:
    """Traverse renamed legacy graph tables for pre-CDI-V2 callers."""
    result = await session.execute(select(GraphEntity).where(func.lower(GraphEntity.name).in_(normalized_names)))
    seed_entities = list(result.scalars().all())
    if not seed_entities:
        return GraphContext(
            entities=[],
            relations=[],
            related_chunk_ids=set(),
            summary=f"No graph entities found for: {', '.join(original_names)}",
        )

    visited_entity_ids = {entity.id for entity in seed_entities}
    visited_relation_ids: set[uuid.UUID] = set()
    all_entities = list(seed_entities)
    all_relations: list[GraphRelation] = []
    frontier_ids = set(visited_entity_ids)

    for _ in range(max_hops):
        if not frontier_ids:
            break
        result = await session.execute(
            select(GraphRelation).where(
                or_(
                    GraphRelation.source_entity_id.in_(frontier_ids),
                    GraphRelation.target_entity_id.in_(frontier_ids),
                )
            )
        )
        relations = [relation for relation in result.scalars().all() if relation.id not in visited_relation_ids]
        all_relations.extend(relations)
        visited_relation_ids.update(relation.id for relation in relations)

        next_frontier: set[uuid.UUID] = set()
        for relation in relations:
            for entity_id in (relation.source_entity_id, relation.target_entity_id):
                if entity_id not in visited_entity_ids:
                    visited_entity_ids.add(entity_id)
                    next_frontier.add(entity_id)
        if next_frontier:
            result = await session.execute(select(GraphEntity).where(GraphEntity.id.in_(next_frontier)))
            all_entities.extend(result.scalars().all())
        frontier_ids = next_frontier

    entity_id_to_name = {entity.id: entity.name for entity in all_entities}
    entity_list = [
        ExtractedEntity(normalized_label=entity.name, entity_type=entity.entity_type, confidence=entity.confidence)
        for entity in all_entities
    ]
    relation_list = [
        ExtractedRelation(
            subject_label=entity_id_to_name.get(relation.source_entity_id, "?"),
            object_label=entity_id_to_name.get(relation.target_entity_id, "?"),
            relation_type=relation.relation_type,
            weight=relation.weight,
        )
        for relation in all_relations
    ]
    chunk_ids = {entity.source_chunk_id for entity in all_entities}
    chunk_ids.update(relation.source_chunk_id for relation in all_relations)
    summary_parts = [f"Found {len(entity_list)} entities and {len(relation_list)} relations."]
    summary_parts.extend(f"- {entity.name} ({entity.entity_type})" for entity in entity_list[:5])
    if len(entity_list) > 5:
        summary_parts.append("...")
    return GraphContext(
        entities=entity_list,
        relations=relation_list,
        related_chunk_ids=chunk_ids,
        summary="\n".join(summary_parts),
    )
