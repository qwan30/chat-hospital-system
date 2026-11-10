"""Adversarial clinical safety, temporal entailment, and GraphRAG boundary tests."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings
from hospital_ai.db.clinical_documents import DocumentIndexGeneration
from hospital_ai.db.clinical_graph import (
    GraphEntity,
    GraphMention,
    GraphRelationAssertion,
)
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import Document, Patient
from hospital_ai.services.claim_validation import ClaimValidator, ValidationContext
from hospital_ai.services.drug_check import DrugCheckService
from hospital_ai.services.graph_rag import (
    CANONICAL_PATIENT_ANCHOR,
    extract_entities_and_relations_offline,
    find_related_entities,
)


def test_adversarial_date_swap_rejection():
    validator = ClaimValidator()
    evidence = {
        "E1": (
            "Patient admitted on 2026-05-01. "
            "Underwent coronary bypass surgery on 2026-05-02. "
            "Discharged on 2026-05-10."
        )
    }
    swapped_claim = "Patient underwent coronary bypass surgery on 2026-05-10 [E1]."
    res = validator.validate_sentence(swapped_claim, evidence, ValidationContext())
    assert res.passed is False
    assert any(c.reason in ("EVENT_DATE_MISMATCH", "DATE_MISMATCH") for c in res.claims)


def test_multi_date_legitimate_claim_acceptance():
    validator = ClaimValidator()
    evidence = {
        "E1": (
            "Patient admitted on 2026-05-01. "
            "Underwent coronary bypass surgery on 2026-05-02. "
            "Discharged on 2026-05-10."
        )
    }
    legitimate_claim = "Patient underwent coronary bypass surgery on 2026-05-02 [E1]."
    res = validator.validate_sentence(legitimate_claim, evidence, ValidationContext())
    assert res.passed is True


    # Sub-clause event-date binding within a single sentence
    subclause_evidence = {"E1": "Admitted on 2026-05-01, operated on 2026-05-02."}
    subclause_res = validator.validate_sentence(
        "Patient was operated on 2026-05-02 [E1].",
        subclause_evidence,
        ValidationContext(),
    )
    assert subclause_res.passed is True

    subclause_swapped = validator.validate_sentence(
        "Patient was operated on 2026-05-01 [E1].",
        subclause_evidence,
        ValidationContext(),
    )
    assert subclause_swapped.passed is False

    # Shared subject/measurement across two dates remains DATE_AMBIGUOUS
    ambiguous_res = validator.validate_sentence(
        "HbA1c was 7.1% on 2026-08-01 [E1].",
        {"E1": "HbA1c 7.1% collected 2026-08-01 and repeated 2026-08-02"},
        ValidationContext(),
    )
    assert ambiguous_res.passed is False
    assert ambiguous_res.claims[0].reason == "DATE_AMBIGUOUS"

@pytest.mark.asyncio
async def test_candidate_drug_ddi_warning(
    session_and_settings: tuple[AsyncSession, Settings],
):
    db_session, _ = session_and_settings
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
    db_session.add_all([doc, gen])
    await db_session.flush()

    aspirin = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient_id,
        normalized_label="aspirin",
        entity_type="drug",
        lifecycle_status="active",
    )
    db_session.add(aspirin)
    await db_session.flush()

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
    db_session.add(mention)
    await db_session.commit()

    service = DrugCheckService(db_session)
    warnings = await service.check_interactions(
        query_text="Can I prescribe warfarin 5mg daily for this patient?",
        patient_id=patient_id,
    )
    assert len(warnings) >= 1
    assert any(
        "warfarin" in w.drug_name.lower() or "aspirin" in w.drug_name.lower()
        for w in warnings
    )


@pytest.mark.asyncio
async def test_graph_traversal_via_patient_to_condition(
    session_and_settings: tuple[AsyncSession, Settings],
):
    db_session, _ = session_and_settings
    patient_id = uuid.uuid4()
    patient = Patient(
        id=patient_id,
        full_name="Traversal Test Patient",
        mrn=f"MRN-{uuid.uuid4().hex[:6]}",
    )
    db_session.add(patient)
    await db_session.flush()

    diltiazem = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient_id,
        normalized_label="diltiazem",
        entity_type="drug",
    )
    patient_self = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient_id,
        normalized_label=CANONICAL_PATIENT_ANCHOR,
        entity_type="patient_anchor",
    )
    penicillin = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient_id,
        normalized_label="penicillin",
        entity_type="allergy",
    )
    nsaid = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient_id,
        normalized_label="nsaid",
        entity_type="drug",
    )
    heart_failure = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient_id,
        normalized_label="heart_failure",
        entity_type="condition",
    )
    db_session.add_all([diltiazem, patient_self, penicillin, nsaid, heart_failure])
    await db_session.flush()

    db_session.add_all(
        [
            GraphRelationAssertion(
                id=uuid.uuid4(),
                patient_id=patient_id,
                subject_entity_id=diltiazem.id,
                object_entity_id=patient_self.id,
                relation_type="prescribed_for",
                normalized_value="prescribed_for",
            ),
            GraphRelationAssertion(
                id=uuid.uuid4(),
                patient_id=patient_id,
                subject_entity_id=patient_self.id,
                object_entity_id=penicillin.id,
                relation_type="allergic_to",
                normalized_value="allergic_to",
            ),
            GraphRelationAssertion(
                id=uuid.uuid4(),
                patient_id=patient_id,
                subject_entity_id=patient_self.id,
                object_entity_id=nsaid.id,
                relation_type="contraindicates",
                normalized_value="contraindicates",
            ),
            GraphRelationAssertion(
                id=uuid.uuid4(),
                patient_id=patient_id,
                subject_entity_id=patient_self.id,
                object_entity_id=heart_failure.id,
                relation_type="diagnosed_with",
                normalized_value="diagnosed_with",
            ),
        ]
    )
    await db_session.commit()

    # 1. Default traversal crosses patient:self for allergic_to/contraindicates, blocks diagnosed_with
    default_ctx = await find_related_entities(
        db_session,
        ["diltiazem"],
        max_hops=2,
        patient_id=patient_id,
    )
    default_labels = {e.normalized_label for e in default_ctx.entities}
    assert "penicillin" in default_labels
    assert "nsaid" in default_labels
    assert "heart_failure" not in default_labels

    # 2. Opt-in include_patient_conditions=True crosses patient:self for diagnosed_with
    condition_ctx = await find_related_entities(
        db_session,
        ["diltiazem"],
        max_hops=2,
        patient_id=patient_id,
        include_patient_conditions=True,
    )
    condition_labels = {e.normalized_label for e in condition_ctx.entities}
    assert "penicillin" in condition_labels
    assert "nsaid" in condition_labels
    assert "heart_failure" in condition_labels


@pytest.mark.asyncio
async def test_discontinued_medication_does_not_block_candidate(
    session_and_settings: tuple[AsyncSession, Settings],
):
    db_session, _ = session_and_settings
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
    db_session.add_all([doc, gen])
    await db_session.flush()

    discontinued_warfarin = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient_id,
        normalized_label="warfarin",
        entity_type="drug",
        lifecycle_status="discontinued",
    )
    db_session.add(discontinued_warfarin)
    await db_session.flush()

    mention = GraphMention(
        id=uuid.uuid4(),
        patient_id=patient_id,
        entity_id=discontinued_warfarin.id,
        generation_id=gen.id,
        document_id=doc.id,
        revision_set_id=gen.revision_set_id,
        page_revision_id=uuid.uuid4(),
        chunk_id=uuid.uuid4(),
        independent_source_identity="chart.pdf:1:1",
    )
    db_session.add(mention)
    await db_session.commit()

    service = DrugCheckService(db_session)
    warnings = await service.check_interactions(
        query_text="Can we start aspirin 81mg daily?",
        patient_id=patient_id,
        min_severity="high",
    )
    assert len(warnings) == 0


@pytest.mark.asyncio
async def test_unapproved_generation_medication_ignored(
    session_and_settings: tuple[AsyncSession, Settings],
):
    db_session, _ = session_and_settings
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
        state="superseded",
    )
    doc.active_index_generation_id = active_gen.id
    db_session.add_all([doc, active_gen, unapproved_gen])
    await db_session.flush()

    drug = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient_id,
        normalized_label="warfarin",
        entity_type="drug",
        lifecycle_status="active",
    )
    db_session.add(drug)
    await db_session.flush()

    mention = GraphMention(
        id=uuid.uuid4(),
        patient_id=patient_id,
        entity_id=drug.id,
        generation_id=unapproved_gen.id,
        document_id=doc.id,
        revision_set_id=unapproved_gen.revision_set_id,
        page_revision_id=uuid.uuid4(),
        chunk_id=uuid.uuid4(),
        independent_source_identity="chart.pdf:1:1",
    )
    db_session.add(mention)
    await db_session.commit()

    service = DrugCheckService(db_session)
    warnings = await service.check_interactions(
        query_text="Can we start aspirin 81mg daily?",
        patient_id=patient_id,
        min_severity="high",
    )
    assert len(warnings) == 0


@pytest.mark.asyncio
async def test_negated_allergy_does_not_block(
    session_and_settings: tuple[AsyncSession, Settings],
):
    _ = session_and_settings
    entities, relations = await extract_entities_and_relations_offline(
        "Patient reports NKDA (no known drug allergies). No known allergy to penicillin."
    )
    allergy_relations = [r for r in relations if r.relation_type == "allergic_to"]
    assert len(allergy_relations) == 0
    assert not any(e.normalized_label == "penicillin" for e in entities)


@pytest.mark.asyncio
async def test_graph_entity_cap_prunes_relations_before_evidence_lookup(
    session_and_settings: tuple[AsyncSession, Settings],
):
    db_session, _ = session_and_settings
    patient_id = uuid.uuid4()
    patient = Patient(
        id=patient_id,
        full_name="Cap Test Patient",
        mrn=f"MRN-{uuid.uuid4().hex[:6]}",
    )
    db_session.add(patient)
    await db_session.flush()

    seed = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient_id,
        normalized_label="warfarin",
        entity_type="drug",
    )
    neighbors = [
        GraphEntity(
            id=uuid.uuid4(),
            patient_id=patient_id,
            normalized_label=f"condition_{i}",
            entity_type="condition",
        )
        for i in range(20)
    ]
    db_session.add_all([seed, *neighbors])
    await db_session.flush()

    db_session.add_all(
        [
            GraphRelationAssertion(
                id=uuid.uuid4(),
                patient_id=patient_id,
                subject_entity_id=seed.id,
                object_entity_id=neighbor.id,
                relation_type="contraindicates",
                normalized_value="contraindicates",
            )
            for neighbor in neighbors
        ]
    )
    await db_session.commit()

    ctx = await find_related_entities(
        db_session,
        ["warfarin"],
        max_hops=1,
        patient_id=patient_id,
    )
    assert len(ctx.entities) == 15
    assert len(ctx.relations) == 14
    assert all(r.subject_label != "?" and r.object_label != "?" for r in ctx.relations)
