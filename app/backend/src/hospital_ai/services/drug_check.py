"""Drug interaction and allergy checking service.

Uses the graph RAG entity/relation tables to detect potential
drug–drug, drug–condition, and drug–allergy interactions from
indexed clinical documents.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.db.clinical_graph import GraphEntity, GraphRelationAssertion, GraphRelationEvidence
from hospital_ai.services.graph_rag import (
    extract_entities_and_relations_nlp,
)


@dataclass(frozen=True)
class DrugWarning:
    """A structured drug interaction warning with evidence."""

    drug_name: str
    interacting_entity: str
    interaction_type: str  # contraindicates | interacts_with | causes | mentioned_with
    severity: str  # critical | high | medium | low
    evidence_chunk_id: uuid.UUID
    message: str


SEVERITY_MAP = {
    "contraindicates": "critical",
    "interacts_with": "high",
    "causes": "medium",
    "mentioned_with": "low",
}

# Drug-allergy interaction keywords (common clinical flags)
ALLERGY_KEYWORDS = frozenset(
    [
        "allergy",
        "allergic",
        "anaphylaxis",
        "reaction",
        "hypersensitivity",
        "contraindicated",
        "adverse",
    ]
)


def _severity_for(relation_type: str) -> str:
    return SEVERITY_MAP.get(relation_type, "medium")


def _build_message(drug: str, entity: str, relation_type: str) -> str:
    templates = {
        "contraindicates": f"⚠️ CRITICAL: {drug.title()} is contraindicated with {entity.title()}.",
        "interacts_with": f"⚠️ WARNING: {drug.title()} has a known interaction with {entity.title()}.",
        "causes": f"⚠️ CAUTION: {drug.title()} may cause or worsen {entity.title()}.",
        "mentioned_with": f"ℹ️ NOTE: {drug.title()} was mentioned alongside {entity.title()} in clinical records.",
    }
    return templates.get(
        relation_type,
        f"⚠️ {drug.title()} has a relationship ({relation_type}) with {entity.title()}.",
    )


class DrugCheckService:
    """Checks for drug interactions using the SQL-backed entity graph."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def check_interactions(
        self,
        query_text: str,
        patient_id: Optional[uuid.UUID],
        *,
        min_severity: str = "low",
    ) -> list[DrugWarning]:
        """Check for drug interactions relevant to the query and patient.

        1. Extracts drug entities from the query text.
        2. Finds graph relations for those drugs within the patient's documents.
        3. Returns structured warnings sorted by severity.
        """
        if not patient_id:
            return []

        entities, _ = await extract_entities_and_relations_nlp(query_text)
        drug_names = [e.normalized_label for e in entities if e.entity_type == "drug"]

        if not drug_names:
            return []

        # Find graph entities for these drugs within the patient's documents
        result = await self.session.execute(
            select(GraphEntity).where(
                GraphEntity.normalized_label.in_(drug_names),
                GraphEntity.patient_id == patient_id,
            )
        )
        patient_drug_entities = list(result.scalars().all())

        if not patient_drug_entities:
            return []

        drug_entity_ids = {e.id for e in patient_drug_entities}
        drug_id_to_name = {e.id: e.normalized_label for e in patient_drug_entities}

        # Find relations involving these drugs
        result = await self.session.execute(
            select(GraphRelationAssertion, GraphRelationEvidence.chunk_id)
            .join(GraphRelationEvidence)
            .where(
                or_(
                    GraphRelationAssertion.subject_entity_id.in_(drug_entity_ids),
                    GraphRelationAssertion.object_entity_id.in_(drug_entity_ids),
                ),
                GraphRelationAssertion.patient_id == patient_id,
            )
        )
        relations_and_chunks = result.all()

        if not relations_and_chunks:
            return []

        # Resolve target entities
        related_entity_ids: set[uuid.UUID] = set()
        for rel, _ in relations_and_chunks:
            related_entity_ids.add(rel.subject_entity_id)
            related_entity_ids.add(rel.object_entity_id)
        related_entity_ids -= drug_entity_ids

        entity_name_map = dict(drug_id_to_name)
        if related_entity_ids:
            result = await self.session.execute(select(GraphEntity).where(GraphEntity.id.in_(related_entity_ids)))
            for entity in result.scalars().all():
                entity_name_map[entity.id] = entity.normalized_label

        # Build warnings
        severity_order = ["critical", "high", "medium", "low"]
        min_idx = severity_order.index(min_severity) if min_severity in severity_order else len(severity_order)

        warnings: list[DrugWarning] = []
        seen: set[tuple] = set()

        for rel, chunk_id in relations_and_chunks:
            # Determine which end is the drug
            if rel.subject_entity_id in drug_entity_ids:
                drug_id = rel.subject_entity_id
                other_id = rel.object_entity_id
            else:
                drug_id = rel.object_entity_id
                other_id = rel.subject_entity_id

            drug_name = entity_name_map.get(drug_id, "unknown")
            other_name = entity_name_map.get(other_id, "unknown")
            severity = _severity_for(rel.relation_type)

            # Filter by min_severity
            if severity_order.index(severity) > min_idx:
                continue

            # Deduplicate
            key = (drug_name, other_name, rel.relation_type)
            if key in seen:
                continue
            seen.add(key)

            warnings.append(
                DrugWarning(
                    drug_name=drug_name,
                    interacting_entity=other_name,
                    interaction_type=rel.relation_type,
                    severity=severity,
                    evidence_chunk_id=chunk_id,
                    message=_build_message(drug_name, other_name, rel.relation_type),
                )
            )

        # Sort by severity (critical first)
        warnings.sort(key=lambda w: severity_order.index(w.severity))
        return warnings


async def check_drug_interactions_for_query(
    session: AsyncSession,
    query_text: str,
    patient_id: Optional[uuid.UUID],
) -> list[DrugWarning]:
    """Convenience function wrapping DrugCheckService."""
    return await DrugCheckService(session).check_interactions(
        query_text=query_text,
        patient_id=patient_id,
        min_severity="low",
    )
