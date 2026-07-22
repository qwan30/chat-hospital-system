import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from starlette.requests import Request

from hospital_ai.api.routes.graph import _canonical_entity_info, get_patient_graph
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID, PATIENT_ELEANOR_ID
from hospital_ai.db.models import DocumentChunk, DocumentPage, PatientPermission, User
from hospital_ai.services.graph_rag import GraphEntity, GraphRelation
from tests.conftest import create_indexed_document


def _request(patient_id: uuid.UUID) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": f"/api/v1/graph/patients/{patient_id}",
            "headers": [],
            "client": ("127.0.0.1", 8000),
        }
    )


def test_canonicalization_does_not_match_ast_or_alt_substrings():
    assert _canonical_entity_info("fasting glucose", "lab")[0] != "AST"
    assert _canonical_entity_info("salt intake", "concept")[0] != "ALT"


@pytest.mark.parametrize(
    ("first_label", "second_label", "canonical_name"),
    [
        ("HbA1c 48 mmol/mol", "HbA1c 64 mmol/mol", "HbA1c"),
        ("Potassium 3.1", "Kali 4.4", "Potassium"),
        ("Hemoglobin 9.8", "Hgb 12.6", "Hemoglobin"),
        ("BNP 180", "BNP 420", "BNP"),
        ("Creatinine 1.1", "Creatinine 2.3", "Creatinine"),
        ("Glucose 95", "Glucose 240", "Glucose"),
        ("AST 18 U/L", "AST 61 U/L", "AST"),
        ("ALT 22 U/L", "ALT 73 U/L", "ALT"),
        ("Sodium 132", "Natri 140", "Sodium"),
        ("eGFR 42", "eGFR 78", "eGFR"),
    ],
)
def test_distinct_lab_values_have_distinct_consolidation_keys(first_label, second_label, canonical_name):
    first = _canonical_entity_info(first_label, "lab")
    second = _canonical_entity_info(second_label, "lab")

    assert first[0] == canonical_name
    assert second[0] == canonical_name
    assert first[2] == first_label
    assert second[2] == second_label
    assert first[2] != second[2]


async def _seed_indexed_chunk(session, *, patient_id=PATIENT_ALICE_ID, title="Graph endpoint evidence"):
    document = await create_indexed_document(
        session,
        patient_id=patient_id,
        uploaded_by=DOCTOR_ID,
        title=title,
        content="Metformin treats diabetes.",
    )
    chunk_result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document.id))
    chunk = chunk_result.scalars().one()
    return document, chunk


async def _seed_graph_entities(session):
    document, chunk = await _seed_indexed_chunk(session)
    source = GraphEntity(
        name="metformin",
        entity_type="drug",
        source_chunk_id=chunk.id,
        source_document_id=document.id,
        confidence=1.0,
    )
    target = GraphEntity(
        name="diabetes",
        entity_type="condition",
        source_chunk_id=chunk.id,
        source_document_id=document.id,
        confidence=1.0,
    )
    session.add_all([source, target])
    await session.commit()
    return document, chunk, source, target


async def _get_graph(session):
    doctor = await session.get(User, DOCTOR_ID)
    return await get_patient_graph(
        request=_request(PATIENT_ALICE_ID),
        patient_id=PATIENT_ALICE_ID,
        db=session,
        current_user=doctor,
    )


@pytest.mark.asyncio
async def test_doctor_can_read_seeded_cardiology_patient_graph(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    response = await get_patient_graph(
        request=_request(PATIENT_ELEANOR_ID),
        patient_id=PATIENT_ELEANOR_ID,
        db=session,
        current_user=doctor,
    )

    assert response.patient_id == PATIENT_ELEANOR_ID
    assert any(node.id == "pt" for node in response.nodes)


@pytest.mark.asyncio
async def test_patient_graph_does_not_fabricate_edges_for_unrelated_entities(session_and_settings):
    session, _ = session_and_settings
    await _seed_graph_entities(session)
    response = await _get_graph(session)

    assert response.edges == []


@pytest.mark.asyncio
async def test_patient_graph_returns_only_persisted_relation_with_provenance(session_and_settings):
    session, _ = session_and_settings
    document, chunk, source, target = await _seed_graph_entities(session)
    relation_document, relation_chunk = await _seed_indexed_chunk(
        session,
        title="Validated relation evidence",
    )
    relation = GraphRelation(
        source_entity_id=source.id,
        target_entity_id=target.id,
        relation_type="treats",
        weight=1.0,
        source_chunk_id=relation_chunk.id,
    )
    session.add(relation)
    await session.commit()
    response = await _get_graph(session)

    assert len(response.edges) == 1
    edge = response.edges[0]
    assert edge.id == f"edge-{relation.id}"
    assert edge.from_node == f"node-{source.id}"
    assert edge.to_node == f"node-{target.id}"
    assert edge.label == "treats"
    assert edge.source_document_id == relation_document.id
    assert edge.source_chunk_id == relation_chunk.id

    step = response.reasoning_path[0].steps[0]
    assert step.source_document_id == relation_document.id
    assert step.source_chunk_id == relation_chunk.id

    clinical_nodes = {node.id: node for node in response.nodes if node.type != "patient"}
    assert clinical_nodes[f"node-{source.id}"].source_document_id == document.id
    assert clinical_nodes[f"node-{source.id}"].source_chunk_id == chunk.id
    assert clinical_nodes[f"node-{target.id}"].source_document_id == document.id
    assert clinical_nodes[f"node-{target.id}"].source_chunk_id == chunk.id


@pytest.mark.parametrize(
    "invalid_source",
    [
        "chunk_patient_mismatch",
        "document_patient_mismatch",
        "page_document_mismatch",
        "deleted_chunk",
        "deleted_page",
        "deleted_document",
        "non_indexed_document",
    ],
)
@pytest.mark.asyncio
async def test_patient_graph_excludes_entities_without_an_active_patient_source_chain(
    session_and_settings,
    invalid_source,
):
    session, _ = session_and_settings
    document, chunk, _, _ = await _seed_graph_entities(session)

    if invalid_source == "chunk_patient_mismatch":
        chunk.patient_id = PATIENT_BOB_ID
    elif invalid_source == "document_patient_mismatch":
        document.patient_id = PATIENT_BOB_ID
    elif invalid_source == "page_document_mismatch":
        bob_document, _ = await _seed_indexed_chunk(
            session,
            patient_id=PATIENT_BOB_ID,
            title="Cross-patient page source",
        )
        page_result = await session.execute(select(DocumentPage).where(DocumentPage.document_id == bob_document.id))
        chunk.page_id = page_result.scalars().one().id
    elif invalid_source == "deleted_chunk":
        chunk.deleted_at = datetime.now(UTC)
    elif invalid_source == "deleted_page":
        page = await session.get(DocumentPage, chunk.page_id)
        page.deleted_at = datetime.now(UTC)
    elif invalid_source == "deleted_document":
        document.deleted_at = datetime.now(UTC)
    elif invalid_source == "non_indexed_document":
        document.status = "uploaded"

    await session.commit()
    response = await _get_graph(session)

    assert [node.type for node in response.nodes] == ["patient"]
    assert response.edges == []


@pytest.mark.parametrize("invalid_relation_source", ["cross_patient", "deleted_chunk"])
@pytest.mark.asyncio
async def test_patient_graph_excludes_relations_from_invalid_source_chunks(
    session_and_settings,
    invalid_relation_source,
):
    session, _ = session_and_settings
    _, _, source, target = await _seed_graph_entities(session)
    source_patient_id = PATIENT_BOB_ID if invalid_relation_source == "cross_patient" else PATIENT_ALICE_ID
    _, relation_chunk = await _seed_indexed_chunk(
        session,
        patient_id=source_patient_id,
        title=f"Invalid relation source: {invalid_relation_source}",
    )
    if invalid_relation_source == "deleted_chunk":
        relation_chunk.deleted_at = datetime.now(UTC)
    relation = GraphRelation(
        source_entity_id=source.id,
        target_entity_id=target.id,
        relation_type="treats",
        weight=1.0,
        source_chunk_id=relation_chunk.id,
    )
    session.add(relation)
    await session.commit()

    response = await _get_graph(session)

    assert response.edges == []
    assert response.reasoning_path == []


@pytest.mark.asyncio
async def test_patient_graph_filters_source_chunks_denied_by_role_access_tags(session_and_settings):
    session, _ = session_and_settings
    document, chunk, _, _ = await _seed_graph_entities(session)
    chunk.meta = {"access_tags": ["medication"]}
    lab_user = User(email="graph-lab@example.test", full_name="Graph Lab", role="lab_staff")
    session.add(lab_user)
    await session.flush()
    session.add(PatientPermission(user_id=lab_user.id, patient_id=PATIENT_ALICE_ID, scope="read"))
    await session.commit()

    response = await get_patient_graph(
        request=_request(PATIENT_ALICE_ID),
        patient_id=PATIENT_ALICE_ID,
        db=session,
        current_user=lab_user,
    )

    assert [node.type for node in response.nodes] == ["patient"]


@pytest.mark.asyncio
async def test_patient_graph_uses_deterministic_first_alias_as_stable_node_id(session_and_settings):
    session, _ = session_and_settings
    document, chunk = await _seed_indexed_chunk(session)
    expected_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    later_id = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
    session.add_all(
        [
            GraphEntity(
                id=later_id,
                name="Metformin 500 mg",
                entity_type="drug",
                source_chunk_id=chunk.id,
                source_document_id=document.id,
                confidence=1.0,
            ),
            GraphEntity(
                id=expected_id,
                name="metformin",
                entity_type="medication",
                source_chunk_id=chunk.id,
                source_document_id=document.id,
                confidence=1.0,
            ),
        ]
    )
    await session.commit()

    response = await _get_graph(session)
    medications = [node for node in response.nodes if node.type == "medication"]

    assert len(medications) == 1
    assert medications[0].id == f"node-{expected_id}"
