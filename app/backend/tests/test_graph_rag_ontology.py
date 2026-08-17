"""Tests for Graph RAG 10-relation ontology, canonical patient anchor, and schema validation."""

import pytest
from hospital_ai.services.graph_rag import (
    CANONICAL_PATIENT_ANCHOR,
    VALID_RELATION_TYPES,
    ExtractedEntity,
    ExtractedRelation,
    validate_relation_type,
)


def test_valid_relation_types_contains_all_10_clinical_relations():
    """Verify that all 10 standard clinical relations and 2 lab grammar relations are in the allowlist."""
    expected_relations = {
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
    }
    assert expected_relations.issubset(VALID_RELATION_TYPES)


def test_canonical_patient_anchor_constant():
    """Verify canonical patient anchor constant format."""
    assert CANONICAL_PATIENT_ANCHOR == "patient:self"


def test_validate_relation_type_helper():
    """Verify validation helper accepts valid relations and normalizes casing/spaces."""
    assert validate_relation_type("treats") == "treats"
    assert validate_relation_type("Interacts_With") == "interacts_with"
    assert validate_relation_type("diagnosed with") == "diagnosed_with"
    assert validate_relation_type("allergic to") == "allergic_to"
    assert validate_relation_type("indicates") == "indicates"
    assert validate_relation_type("history_of") == "history_of"
    assert validate_relation_type("invalid_unknown_rel") is None


def test_extracted_relation_dataclass_fields():
    """Verify ExtractedRelation dataclass supports severity and source_layer metadata."""
    rel = ExtractedRelation(
        subject_label="warfarin",
        object_label="aspirin",
        relation_type="interacts_with",
        normalized_value="interacts_with",
        weight=1.0,
        severity="high",
        source_layer="catalog",
    )
    assert rel.subject_label == "warfarin"
    assert rel.object_label == "aspirin"
    assert rel.relation_type == "interacts_with"
    assert rel.severity == "high"
    assert rel.source_layer == "catalog"
