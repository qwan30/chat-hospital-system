"""Tests for Negation-Aware Clinical Extraction and Fallback Grammar."""

import pytest

from hospital_ai.services.graph_rag import (
    CANONICAL_PATIENT_ANCHOR,
    extract_entities_and_relations_offline,
)


@pytest.mark.asyncio
async def test_negation_nkda_no_false_allergy():
    """Ensure NKDA and negative allergy statements do NOT create allergic_to edges."""
    texts = [
        "Patient has no known drug allergies (NKDA).",
        "NKDA, denies allergy to penicillin.",
        "No known allergies to any medications.",
        "Allergies: None reported.",
    ]
    for text in texts:
        entities, relations = await extract_entities_and_relations_offline(text)
        allergy_relations = [r for r in relations if r.relation_type == "allergic_to"]
        assert len(allergy_relations) == 0, f"False allergy edge extracted from: {text}"


@pytest.mark.asyncio
async def test_negation_denies_history_no_false_history_edge():
    """Ensure denied conditions do NOT create history_of or diagnosed_with edges."""
    texts = [
        "Patient denies history of asthma and hypertension.",
        "No prior history of diabetes mellitus.",
        "Ruled out myocardial infarction in the ED.",
    ]
    for text in texts:
        entities, relations = await extract_entities_and_relations_offline(text)
        invalid_relations = [r for r in relations if r.relation_type in ("history_of", "diagnosed_with")]
        assert len(invalid_relations) == 0, f"False condition edge extracted from: {text}"


@pytest.mark.asyncio
async def test_affirmative_diagnosis_and_allergy_extraction():
    """Ensure explicitly stated diagnoses and allergies are extracted with canonical patient anchor."""
    text = "Patient is diagnosed with type 2 diabetes and has confirmed allergy to penicillin."
    entities, relations = await extract_entities_and_relations_offline(text)

    diag_rel = next((r for r in relations if r.relation_type == "diagnosed_with"), None)
    allergy_rel = next((r for r in relations if r.relation_type == "allergic_to"), None)

    assert diag_rel is not None
    assert diag_rel.subject_label == CANONICAL_PATIENT_ANCHOR
    assert "diabetes" in diag_rel.object_label

    assert allergy_rel is not None
    assert allergy_rel.subject_label == CANONICAL_PATIENT_ANCHOR
    assert "penicillin" in allergy_rel.object_label


@pytest.mark.asyncio
async def test_compound_sentence_selective_negation():
    """Ensure compound sentences extract positive conditions while filtering negated symptoms."""
    text = "Patient diagnosed with COPD; denies chest pain."
    entities, relations = await extract_entities_and_relations_offline(text)

    diag_rel = next((r for r in relations if r.relation_type == "diagnosed_with"), None)
    symptom_rel = next((r for r in relations if r.relation_type == "has_symptom"), None)

    assert diag_rel is not None
    assert "copd" in diag_rel.object_label
    assert symptom_rel is None, "Negated symptom 'chest pain' should not be extracted"


@pytest.mark.asyncio
async def test_indicates_relation_extraction():
    """Ensure 'indicates' diagnostic relation is extracted between findings and conditions."""
    text = "Elevated troponin indicates acute myocardial infarction."
    entities, relations = await extract_entities_and_relations_offline(text)

    ind_rel = next((r for r in relations if r.relation_type == "indicates"), None)
    assert ind_rel is not None
    assert "troponin" in ind_rel.subject_label
    assert "myocardial" in ind_rel.object_label
