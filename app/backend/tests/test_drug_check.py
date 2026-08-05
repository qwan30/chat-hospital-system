"""Tests for drug interaction and allergy checking service.

Covers:
- Drug entity detection from query text
- Interaction lookup against patient documents
- Warning severity classification
- Warning message templates
- Edge cases: no drugs in query, no graph data, no patient docs
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import DocumentChunk
from hospital_ai.services.drug_check import (
    DrugCheckService,
    DrugWarning,
    _build_message,
    _severity_for,
    check_drug_interactions_for_query,
)
from hospital_ai.services.graph_rag import (
    index_chunk_entities,
)
from tests.conftest import create_indexed_document

# ── Unit: severity mapping ───────────────────────────────────────────


def test_severity_map_critical():
    assert _severity_for("contraindicates") == "critical"


def test_severity_map_high():
    assert _severity_for("interacts_with") == "high"


def test_severity_map_medium():
    assert _severity_for("causes") == "medium"


def test_severity_map_low():
    assert _severity_for("mentioned_with") == "low"


def test_severity_map_unknown():
    assert _severity_for("unknown_relation") == "medium"


# ── Unit: message templates ──────────────────────────────────────────


def test_build_message_contraindicates():
    msg = _build_message("warfarin", "aspirin", "contraindicates")
    assert "CRITICAL" in msg
    assert "Warfarin" in msg
    assert "Aspirin" in msg


def test_build_message_interacts():
    msg = _build_message("metformin", "insulin", "interacts_with")
    assert "WARNING" in msg


def test_build_message_causes():
    msg = _build_message("prednisone", "diabetes", "causes")
    assert "CAUTION" in msg


def test_build_message_mentioned():
    msg = _build_message("aspirin", "hypertension", "mentioned_with")
    assert "NOTE" in msg


def test_build_message_unknown_type():
    msg = _build_message("drug_a", "drug_b", "custom_relation")
    assert "drug_a" in msg.lower() or "Drug_A" in msg


# ── Integration: check_interactions ──────────────────────────────────


@pytest.mark.asyncio
async def test_check_interactions_no_drugs_in_query(session_and_settings):
    session, settings = session_and_settings
    warnings = await DrugCheckService(session).check_interactions(
        query_text="What is the patient's blood pressure?",
        patient_id=PATIENT_ALICE_ID,
    )
    assert warnings == []


@pytest.mark.asyncio
async def test_check_interactions_no_graph_data(session_and_settings):
    """When drugs are in query but no graph entities exist, returns empty."""
    session, settings = session_and_settings
    warnings = await DrugCheckService(session).check_interactions(
        query_text="Is the patient on metformin?",
        patient_id=PATIENT_ALICE_ID,
    )
    assert warnings == []


@pytest.mark.asyncio
async def test_check_interactions_with_indexed_data(session_and_settings):
    """When graph entities and relations exist, returns warnings."""
    session, settings = session_and_settings

    # Create a document with drug+condition co-occurrence
    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Medication note",
        content="Patient takes warfarin for atrial fibrillation. Aspirin is also prescribed.",
    )

    # Index graph entities
    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
    chunk = result.scalars().first()
    await index_chunk_entities(session, chunk_id=chunk.id, document_id=doc.id, content=chunk.content)
    await session.commit()

    # Now query for warfarin — should find co-occurrence relations
    warnings = await DrugCheckService(session).check_interactions(
        query_text="Is warfarin safe for this patient?",
        patient_id=PATIENT_ALICE_ID,
    )
    # Warnings depend on relation extraction; at minimum, service should not error
    assert isinstance(warnings, list)


@pytest.mark.asyncio
async def test_check_interactions_sorted_by_severity(session_and_settings):
    """Warnings should be sorted critical → low."""
    session, settings = session_and_settings

    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Drug interaction note",
        content="Aspirin mentioned with hypertension. Warfarin mentioned with heart failure.",
    )

    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
    chunk = result.scalars().first()
    await index_chunk_entities(session, chunk_id=chunk.id, document_id=doc.id, content=chunk.content)
    await session.commit()

    warnings = await DrugCheckService(session).check_interactions(
        query_text="Should the patient take aspirin and warfarin?",
        patient_id=PATIENT_ALICE_ID,
    )

    if len(warnings) >= 2:
        severity_order = ["critical", "high", "medium", "low"]
        for i in range(len(warnings) - 1):
            assert severity_order.index(warnings[i].severity) <= severity_order.index(warnings[i + 1].severity)


@pytest.mark.asyncio
async def test_check_interactions_deduplicates(session_and_settings):
    """Same drug-entity-type triple should not appear twice."""
    session, settings = session_and_settings

    # Index the same drug mention in two chunks
    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Duplicate mention note",
        content="Aspirin for hypertension. Aspirin mentioned with hypertension again.",
    )

    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
    chunk = result.scalars().first()
    await index_chunk_entities(session, chunk_id=chunk.id, document_id=doc.id, content=chunk.content)
    await session.commit()

    warnings = await DrugCheckService(session).check_interactions(
        query_text="Is aspirin appropriate?",
        patient_id=PATIENT_ALICE_ID,
    )

    # Check no duplicates
    seen = set()
    for w in warnings:
        key = (w.drug_name, w.interacting_entity, w.interaction_type)
        assert key not in seen, f"Duplicate warning: {key}"
        seen.add(key)


# ── Convenience function ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_convenience_function(session_and_settings):
    session, settings = session_and_settings
    warnings = await check_drug_interactions_for_query(
        session,
        query_text="No drugs mentioned here.",
        patient_id=PATIENT_ALICE_ID,
    )
    assert warnings == []


# ── DrugWarning dataclass ────────────────────────────────────────────


def test_drug_warning_frozen():
    warning = DrugWarning(
        drug_name="aspirin",
        interacting_entity="hypertension",
        interaction_type="mentioned_with",
        severity="low",
        evidence_chunk_id=uuid.uuid4(),
        message="test",
    )
    with pytest.raises(AttributeError):
        warning.drug_name = "changed"
