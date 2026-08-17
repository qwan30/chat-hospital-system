"""Tests for deterministic drug interaction catalog service with symmetric matching."""

from hospital_ai.services.drug_catalog import (
    get_drug_catalog_service,
)


def test_drug_catalog_loads_interactions():
    """Verify drug catalog successfully loads entries from drug_interaction_matrix.csv."""
    catalog = get_drug_catalog_service()
    assert len(catalog.interactions) >= 100


def test_drug_catalog_symmetric_lookup():
    """Verify drug catalog matches drug pairs bidirectionally."""
    catalog = get_drug_catalog_service()

    # Warfarin and Aspirin interaction
    interaction_ab = catalog.get_interaction("warfarin", "aspirin")
    interaction_ba = catalog.get_interaction("aspirin", "warfarin")

    assert interaction_ab is not None
    assert interaction_ba is not None
    assert interaction_ab.severity in ("critical", "high", "medium", "low")
    assert interaction_ab == interaction_ba


def test_drug_catalog_find_interactions_in_text():
    """Verify catalog identifies multiple mentioned drugs and returns pairwise interactions."""
    catalog = get_drug_catalog_service()
    sample_text = (
        "Patient is currently taking warfarin 5mg daily. "
        "The physician added aspirin 81mg for antiplatelet therapy. "
        "Monitor for bleeding risk."
    )
    relations = catalog.find_interactions_in_text(sample_text)
    assert len(relations) >= 1

    warfarin_aspirin_rel = next(
        (
            r
            for r in relations
            if (r.subject_label == "warfarin" and r.object_label == "aspirin")
            or (r.subject_label == "aspirin" and r.object_label == "warfarin")
        ),
        None,
    )
    assert warfarin_aspirin_rel is not None
    assert warfarin_aspirin_rel.relation_type == "interacts_with"
    assert warfarin_aspirin_rel.source_layer == "catalog"
    assert warfarin_aspirin_rel.severity is not None
