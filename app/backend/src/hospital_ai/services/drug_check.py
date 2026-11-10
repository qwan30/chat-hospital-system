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

from hospital_ai.db.clinical_graph import (
    GraphEntity,
    GraphMention,
    GraphRelationAssertion,
    GraphRelationEvidence,
)
from hospital_ai.db.models import Document
from hospital_ai.services.drug_catalog import get_drug_catalog_service
from hospital_ai.services.evidence_scope import ActiveEvidenceScope
from hospital_ai.services.graph_rag import (
    extract_entities_and_relations_nlp,
    extract_entities_and_relations_offline,
)


@dataclass(frozen=True)
class DrugWarning:
    """A structured drug interaction warning with evidence."""

    drug_name: str
    interacting_entity: str
    interaction_type: str  # contraindicates | interacts_with | causes | mentioned_with
    severity: str  # critical | high | medium | low
    evidence_chunk_id: Optional[uuid.UUID]
    message: str


SEVERITY_MAP = {
    "allergic_to": "critical",
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
        "allergic_to": f"🚨 ALLERGY ALERT: Patient has documented allergy to {drug.title()} / {entity.title()}.",
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
        self.catalog = get_drug_catalog_service()

    async def _filter_generation_valid_entities(
        self,
        patient_id: uuid.UUID,
        entities: list[GraphEntity],
        user_id: Optional[uuid.UUID] = None,
    ) -> tuple[list[GraphEntity], dict[uuid.UUID, uuid.UUID]]:
        """Filter active entities by generation validity and optional user evidence scope."""
        if not entities:
            return [], {}

        entity_ids = [e.id for e in entities]
        stmt = (
            select(GraphMention.entity_id, GraphMention.chunk_id)
            .join(Document, Document.id == GraphMention.document_id)
            .where(
                GraphMention.patient_id == patient_id,
                GraphMention.entity_id.in_(entity_ids),
                Document.active_index_generation_id == GraphMention.generation_id,
                Document.deleted_at.is_(None),
                Document.status.in_(("ready", "ready_with_warnings")),
            )
        )
        if user_id is not None:
            stmt = stmt.where(
                GraphMention.chunk_id.in_(
                    ActiveEvidenceScope(self.session).authorized_chunk_ids(
                        user_id=user_id,
                        patient_id=patient_id,
                    )
                )
            )
        valid_mention_result = await self.session.execute(stmt)
        valid_chunk_by_entity: dict[uuid.UUID, uuid.UUID] = {}
        for ent_id, chunk_id in valid_mention_result.all():
            if ent_id not in valid_chunk_by_entity:
                valid_chunk_by_entity[ent_id] = chunk_id

        valid_entities = [e for e in entities if e.id in valid_chunk_by_entity]
        return valid_entities, valid_chunk_by_entity

    async def check_interactions(
        self,
        query_text: str,
        patient_id: Optional[uuid.UUID],
        *,
        min_severity: str = "low",
        user_id: Optional[uuid.UUID] = None,
        use_llm: bool = False,
    ) -> list[DrugWarning]:
        """Check for drug interactions relevant to the query and patient.

        1. Extracts candidate drug entities from the query text (catalog + offline/NLP).
        2. Finds graph relations and catalog interactions for active, generation-valid
           patient medications and allergies.
        3. Returns structured warnings sorted by severity.
        """
        if not patient_id:
            return []

        catalog_mentions = {d.lower().strip() for d in self.catalog.extract_drug_mentions(query_text)}
        try:
            if use_llm:
                entities, _ = await extract_entities_and_relations_nlp(query_text)
                nlp_drugs = {e.normalized_label.lower().strip() for e in entities if e.entity_type == "drug"}
            else:
                entities, _ = await extract_entities_and_relations_offline(query_text)
                nlp_drugs = {
                    e.normalized_label.lower().strip() for e in entities if e.entity_type in ("drug", "concept")
                }
        except Exception:
            nlp_drugs = set()

        candidate_drugs = catalog_mentions | nlp_drugs
        if not candidate_drugs:
            return []

        severity_order = ["critical", "high", "medium", "low"]
        min_idx = severity_order.index(min_severity) if min_severity in severity_order else len(severity_order)

        warnings: list[DrugWarning] = []
        seen: set[tuple[str, str, str]] = set()

        # 1. Existing GraphRelationAssertion lookup for candidate drugs in patient's chart
        result = await self.session.execute(
            select(GraphEntity).where(
                GraphEntity.normalized_label.in_(candidate_drugs),
                GraphEntity.patient_id == patient_id,
                GraphEntity.lifecycle_status == "active",
            )
        )
        raw_patient_drug_entities = list(result.scalars().all())
        patient_drug_entities, _ = await self._filter_generation_valid_entities(
            patient_id, raw_patient_drug_entities, user_id=user_id
        )

        if patient_drug_entities:
            drug_entity_ids = {e.id for e in patient_drug_entities}
            drug_id_to_name = {e.id: e.normalized_label for e in patient_drug_entities}

            rel_stmt = (
                select(GraphRelationAssertion, GraphRelationEvidence.chunk_id)
                .join(
                    GraphRelationEvidence,
                    GraphRelationEvidence.assertion_id == GraphRelationAssertion.id,
                )
                .join(Document, Document.id == GraphRelationEvidence.document_id)
                .where(
                    or_(
                        GraphRelationAssertion.subject_entity_id.in_(drug_entity_ids),
                        GraphRelationAssertion.object_entity_id.in_(drug_entity_ids),
                    ),
                    GraphRelationAssertion.patient_id == patient_id,
                    GraphRelationAssertion.lifecycle_status == "active",
                    Document.deleted_at.is_(None),
                    Document.status.in_(("ready", "ready_with_warnings")),
                    Document.active_index_generation_id == GraphRelationEvidence.generation_id,
                )
            )
            if user_id is not None:
                rel_stmt = rel_stmt.where(
                    GraphRelationEvidence.chunk_id.in_(
                        ActiveEvidenceScope(self.session).authorized_chunk_ids(
                            user_id=user_id,
                            patient_id=patient_id,
                        )
                    )
                )
            result = await self.session.execute(rel_stmt)
            relations_and_chunks = result.all()

            if relations_and_chunks:
                related_entity_ids: set[uuid.UUID] = set()
                for rel, _ in relations_and_chunks:
                    related_entity_ids.add(rel.subject_entity_id)
                    related_entity_ids.add(rel.object_entity_id)
                related_entity_ids -= drug_entity_ids

                entity_name_map = dict(drug_id_to_name)
                if related_entity_ids:
                    result = await self.session.execute(
                        select(GraphEntity).where(
                            GraphEntity.id.in_(related_entity_ids),
                            GraphEntity.lifecycle_status == "active",
                        )
                    )
                    raw_related_entities = list(result.scalars().all())
                    valid_related_entities, _ = await self._filter_generation_valid_entities(
                        patient_id, raw_related_entities, user_id=user_id
                    )
                    for entity in valid_related_entities:
                        entity_name_map[entity.id] = entity.normalized_label

                for rel, chunk_id in relations_and_chunks:
                    if rel.subject_entity_id in drug_entity_ids:
                        drug_id = rel.subject_entity_id
                        other_id = rel.object_entity_id
                    else:
                        drug_id = rel.object_entity_id
                        other_id = rel.subject_entity_id

                    if drug_id not in entity_name_map or other_id not in entity_name_map:
                        continue
                    drug_name = entity_name_map[drug_id]
                    other_name = entity_name_map[other_id]
                    severity = _severity_for(rel.relation_type)

                    if severity_order.index(severity) > min_idx:
                        continue

                    d1 = drug_name.lower().strip()
                    d2 = other_name.lower().strip()
                    key = (min(d1, d2), max(d1, d2), rel.relation_type)
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

        # 2. Catalog cross-referencing against active, generation-valid patient entities
        active_result = await self.session.execute(
            select(GraphEntity).where(
                GraphEntity.patient_id == patient_id,
                GraphEntity.entity_type.in_(["drug", "allergy"]),
                GraphEntity.lifecycle_status == "active",
            )
        )
        raw_active_entities = list(active_result.scalars().all())
        valid_active_entities, valid_chunk_by_entity = await self._filter_generation_valid_entities(
            patient_id, raw_active_entities, user_id=user_id
        )

        for candidate in sorted(candidate_drugs):
            for patient_entity in valid_active_entities:
                patient_drug = patient_entity.normalized_label.lower().strip()
                if candidate == patient_drug:
                    continue

                interaction = self.catalog.get_interaction(candidate, patient_drug)
                if not interaction:
                    continue

                severity = interaction.severity
                if severity not in severity_order or severity_order.index(severity) > min_idx:
                    continue

                key = (
                    min(candidate, patient_drug),
                    max(candidate, patient_drug),
                    interaction.interaction_type,
                )
                if key in seen:
                    continue
                seen.add(key)

                chunk_id = valid_chunk_by_entity.get(patient_entity.id, uuid.UUID(int=0))
                warnings.append(
                    DrugWarning(
                        drug_name=candidate,
                        interacting_entity=patient_drug,
                        interaction_type=interaction.interaction_type,
                        severity=severity,
                        evidence_chunk_id=chunk_id,
                        message=(
                            f"{severity.upper()} Interaction: {candidate.capitalize()} and "
                            f"{patient_drug.capitalize()}. {interaction.mechanism_action} "
                            f"Recommendation: {interaction.clinical_recommendation}"
                        ),
                    )
                )

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
