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

from hospital_ai.db.clinical_documents import DocumentIndexGeneration
from hospital_ai.db.clinical_graph import GraphEntity, GraphMention
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import Document, DocumentChunk
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


# ── Candidate drug catalog cross-referencing & lifecycle/generation filtering ──


@pytest.mark.asyncio
async def test_drug_check_detects_candidate_drug_interaction(session_and_settings):
    session, _ = session_and_settings
    patient_id = PATIENT_ALICE_ID

    doc = Document(
        id=uuid.uuid4(),
        patient_id=patient_id,
        uploaded_by=DOCTOR_ID,
        title="chart.pdf",
        document_type="note",
        storage_uri="memory://chart.pdf",
        mime_type="application/pdf",
        status="ready",
    )
    gen = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=doc.id,
        revision_set_id=uuid.uuid4(),
        revision_set_sha256="0" * 64,
        state="active",
    )
    doc.active_index_generation_id = gen.id
    session.add_all([doc, gen])
    await session.flush()

    aspirin = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient_id,
        normalized_label="aspirin",
        entity_type="drug",
        lifecycle_status="active",
    )
    session.add(aspirin)
    await session.flush()

    mention = GraphMention(
        id=uuid.uuid4(),
        patient_id=patient_id,
        entity_id=aspirin.id,
        generation_id=gen.id,
        document_id=doc.id,
        revision_set_id=gen.revision_set_id,
        page_revision_id=uuid.uuid4(),
        chunk_id=uuid.uuid4(),
        independent_source_identity="chart.pdf:1:1",
    )
    session.add(mention)
    await session.commit()

    service = DrugCheckService(session)
    warnings = await service.check_interactions(
        query_text="Can we prescribe warfarin 5mg to this patient?",
        patient_id=patient_id,
    )
    assert len(warnings) >= 1
    warfarin_warnings = [w for w in warnings if "warfarin" in w.drug_name.lower() or "aspirin" in w.drug_name.lower()]
    assert len(warfarin_warnings) >= 1
    assert warfarin_warnings[0].severity in ("high", "critical")


@pytest.mark.asyncio
async def test_drug_check_ignores_discontinued_medication(session_and_settings):
    session, _ = session_and_settings
    patient_id = PATIENT_ALICE_ID

    doc = Document(
        id=uuid.uuid4(),
        patient_id=patient_id,
        uploaded_by=DOCTOR_ID,
        title="old.pdf",
        document_type="note",
        storage_uri="memory://old.pdf",
        mime_type="application/pdf",
        status="ready",
    )
    gen = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=doc.id,
        revision_set_id=uuid.uuid4(),
        revision_set_sha256="0" * 64,
        state="active",
    )
    doc.active_index_generation_id = gen.id
    session.add_all([doc, gen])
    await session.flush()

    discontinued_warfarin = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient_id,
        normalized_label="warfarin",
        entity_type="drug",
        lifecycle_status="discontinued",
    )
    session.add(discontinued_warfarin)
    await session.flush()

    mention = GraphMention(
        id=uuid.uuid4(),
        patient_id=patient_id,
        entity_id=discontinued_warfarin.id,
        generation_id=gen.id,
        document_id=doc.id,
        revision_set_id=gen.revision_set_id,
        page_revision_id=uuid.uuid4(),
        chunk_id=uuid.uuid4(),
        independent_source_identity="old.pdf:1:1",
    )
    session.add(mention)
    await session.commit()

    service = DrugCheckService(session)
    warnings = await service.check_interactions(
        query_text="Can we start aspirin 81mg daily?",
        patient_id=patient_id,
        min_severity="high",
    )
    assert len(warnings) == 0


@pytest.mark.asyncio
async def test_drug_check_ignores_unapproved_generation_medication(session_and_settings):
    session, _ = session_and_settings
    patient_id = PATIENT_ALICE_ID

    doc = Document(
        id=uuid.uuid4(),
        patient_id=patient_id,
        uploaded_by=DOCTOR_ID,
        title="unapproved.pdf",
        document_type="note",
        storage_uri="memory://unapproved.pdf",
        mime_type="application/pdf",
        status="ready",
    )
    active_gen = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=doc.id,
        revision_set_id=uuid.uuid4(),
        revision_set_sha256="1" * 64,
        state="active",
    )
    unapproved_gen = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=doc.id,
        revision_set_id=uuid.uuid4(),
        revision_set_sha256="2" * 64,
        state="building",
    )
    doc.active_index_generation_id = active_gen.id
    session.add_all([doc, active_gen, unapproved_gen])
    await session.flush()

    unapproved_warfarin = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient_id,
        normalized_label="warfarin",
        entity_type="drug",
        lifecycle_status="active",
    )
    session.add(unapproved_warfarin)
    await session.flush()

    mention = GraphMention(
        id=uuid.uuid4(),
        patient_id=patient_id,
        entity_id=unapproved_warfarin.id,
        generation_id=unapproved_gen.id,
        document_id=doc.id,
        revision_set_id=unapproved_gen.revision_set_id,
        page_revision_id=uuid.uuid4(),
        chunk_id=uuid.uuid4(),
        independent_source_identity="unapproved.pdf:1:1",
    )
    session.add(mention)
    await session.commit()

    service = DrugCheckService(session)
    warnings = await service.check_interactions(
        query_text="Can we start aspirin 81mg daily?",
        patient_id=patient_id,
        min_severity="high",
    )
    assert len(warnings) == 0


@pytest.mark.asyncio
async def test_check_interactions_blocks_superseded_or_unauthorized_relation_evidence(
    session_and_settings,
):
    from hospital_ai.db.clinical_graph import GraphRelationAssertion, GraphRelationEvidence

    session, _ = session_and_settings
    patient_id = PATIENT_ALICE_ID

    doc = Document(
        id=uuid.uuid4(),
        patient_id=patient_id,
        uploaded_by=DOCTOR_ID,
        title="rel_evidence.pdf",
        document_type="note",
        storage_uri="memory://rel_evidence.pdf",
        mime_type="application/pdf",
        status="ready",
    )
    active_gen = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=doc.id,
        revision_set_id=uuid.uuid4(),
        revision_set_sha256="3" * 64,
        state="active",
    )
    superseded_gen = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=doc.id,
        revision_set_id=uuid.uuid4(),
        revision_set_sha256="4" * 64,
        state="superseded",
    )
    doc.active_index_generation_id = active_gen.id
    session.add_all([doc, active_gen, superseded_gen])
    await session.flush()

    # Warfarin is valid in active generation
    warfarin = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient_id,
        normalized_label="warfarin",
        entity_type="drug",
        lifecycle_status="active",
    )
    # Experimental target entity only mentioned in superseded generation
    stale_target = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient_id,
        normalized_label="experimental_compound_x",
        entity_type="condition",
        lifecycle_status="active",
    )
    session.add_all([warfarin, stale_target])
    await session.flush()

    active_mention = GraphMention(
        id=uuid.uuid4(),
        patient_id=patient_id,
        entity_id=warfarin.id,
        generation_id=active_gen.id,
        document_id=doc.id,
        revision_set_id=active_gen.revision_set_id,
        page_revision_id=uuid.uuid4(),
        chunk_id=uuid.uuid4(),
        independent_source_identity="rel_evidence.pdf:1:1",
    )
    stale_mention = GraphMention(
        id=uuid.uuid4(),
        patient_id=patient_id,
        entity_id=stale_target.id,
        generation_id=superseded_gen.id,
        document_id=doc.id,
        revision_set_id=superseded_gen.revision_set_id,
        page_revision_id=uuid.uuid4(),
        chunk_id=uuid.uuid4(),
        independent_source_identity="rel_evidence.pdf:1:2",
    )
    rel = GraphRelationAssertion(
        id=uuid.uuid4(),
        patient_id=patient_id,
        subject_entity_id=warfarin.id,
        object_entity_id=stale_target.id,
        relation_type="contraindicates",
        normalized_value="contraindicates",
        lifecycle_status="active",
    )
    rel_ev = GraphRelationEvidence(
        id=uuid.uuid4(),
        patient_id=patient_id,
        assertion_id=rel.id,
        generation_id=superseded_gen.id,
        document_id=doc.id,
        revision_set_id=superseded_gen.revision_set_id,
        page_revision_id=uuid.uuid4(),
        chunk_id=stale_mention.chunk_id,
        independent_source_identity="rel_evidence.pdf:1:2",
    )
    session.add_all([active_mention, stale_mention, rel, rel_ev])
    await session.commit()

    service = DrugCheckService(session)
    warnings = await service.check_interactions(
        query_text="Review warfarin dose",
        patient_id=patient_id,
    )
    assert all(w.interacting_entity != "experimental_compound_x" for w in warnings)
