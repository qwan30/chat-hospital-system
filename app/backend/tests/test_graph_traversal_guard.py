"""Tests for BFS Traversal Guard (Anti-Hub Explosion) and Enhanced DrugCheckService."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings
from hospital_ai.db.clinical_graph import GraphEntity, GraphRelationAssertion
from hospital_ai.db.models import Patient
from hospital_ai.services.drug_check import SEVERITY_MAP
from hospital_ai.services.graph_rag import (
    CANONICAL_PATIENT_ANCHOR,
    find_related_entities,
)


def test_severity_map_contains_allergic_to():
    """Verify allergic_to is categorized as critical severity in SEVERITY_MAP."""
    assert "allergic_to" in SEVERITY_MAP
    assert SEVERITY_MAP["allergic_to"] == "critical"


@pytest.mark.asyncio
async def test_traversal_guard_prevents_patient_hub_expansion(session_and_settings: tuple[AsyncSession, Settings]):
    """Verify that BFS traversal from a drug to patient:self does NOT expand outward into unrelated conditions."""
    db_session, _ = session_and_settings
    patient_id = uuid.uuid4()
    patient = Patient(id=patient_id, full_name="Test Patient", mrn=f"MRN-{uuid.uuid4().hex[:6]}")
    db_session.add(patient)
    await db_session.flush()

    # Create entities
    metformin = GraphEntity(patient_id=patient_id, entity_type="drug", normalized_label="metformin")
    patient_anchor = GraphEntity(
        patient_id=patient_id, entity_type="patient_anchor", normalized_label=CANONICAL_PATIENT_ANCHOR
    )
    unrelated_asthma = GraphEntity(patient_id=patient_id, entity_type="condition", normalized_label="asthma")
    unrelated_hypertension = GraphEntity(
        patient_id=patient_id, entity_type="condition", normalized_label="hypertension"
    )

    db_session.add_all([metformin, patient_anchor, unrelated_asthma, unrelated_hypertension])
    await db_session.flush()

    # Relations:
    # metformin <-[prescribed_for]-> patient_anchor
    # patient_anchor <-[history_of]-> unrelated_asthma
    # patient_anchor <-[diagnosed_with]-> unrelated_hypertension
    rel1 = GraphRelationAssertion(
        patient_id=patient_id,
        subject_entity_id=metformin.id,
        object_entity_id=patient_anchor.id,
        relation_type="prescribed_for",
        normalized_value="prescribed_for",
    )
    rel2 = GraphRelationAssertion(
        patient_id=patient_id,
        subject_entity_id=patient_anchor.id,
        object_entity_id=unrelated_asthma.id,
        relation_type="history_of",
        normalized_value="history_of",
    )
    rel3 = GraphRelationAssertion(
        patient_id=patient_id,
        subject_entity_id=patient_anchor.id,
        object_entity_id=unrelated_hypertension.id,
        relation_type="diagnosed_with",
        normalized_value="diagnosed_with",
    )
    db_session.add_all([rel1, rel2, rel3])
    await db_session.flush()

    # Query starting from metformin with max_hops=2
    context = await find_related_entities(
        db_session,
        entity_names=["metformin"],
        max_hops=2,
        patient_id=patient_id,
    )

    extracted_labels = {e.normalized_label for e in context.entities}
    assert "metformin" in extracted_labels
    assert CANONICAL_PATIENT_ANCHOR in extracted_labels
    # With Traversal Guard enabled, unrelated conditions connected via patient:self must NOT be expanded!
    assert "asthma" not in extracted_labels, "Traversal guard failed: asthma leaked via patient hub expansion"
    assert "hypertension" not in extracted_labels, (
        "Traversal guard failed: hypertension leaked via patient hub expansion"
    )
