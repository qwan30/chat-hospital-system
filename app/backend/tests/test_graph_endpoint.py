import uuid

import pytest
from sqlalchemy import select
from starlette.requests import Request

from hospital_ai.api.routes.graph import _canonical_entity_info, get_patient_graph
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import DocumentChunk, User
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


def test_distinct_lab_values_have_distinct_consolidation_keys():
    first = _canonical_entity_info("Potassium 3.1", "lab")
    second = _canonical_entity_info("Potassium 4.4", "lab")

    assert first[2] != second[2]


async def _seed_graph_entities(session):
    document = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Graph endpoint evidence",
        content="Metformin treats diabetes.",
    )
    chunk_result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document.id))
    chunk = chunk_result.scalars().one()
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


@pytest.mark.asyncio
async def test_patient_graph_does_not_fabricate_edges_for_unrelated_entities(session_and_settings):
    session, _ = session_and_settings
    await _seed_graph_entities(session)
    doctor = await session.get(User, DOCTOR_ID)

    response = await get_patient_graph(
        request=_request(PATIENT_ALICE_ID),
        patient_id=PATIENT_ALICE_ID,
        db=session,
        current_user=doctor,
    )

    assert response.edges == []


@pytest.mark.asyncio
async def test_patient_graph_returns_only_persisted_relation_with_provenance(session_and_settings):
    session, _ = session_and_settings
    document, chunk, source, target = await _seed_graph_entities(session)
    relation = GraphRelation(
        source_entity_id=source.id,
        target_entity_id=target.id,
        relation_type="treats",
        weight=1.0,
        source_chunk_id=chunk.id,
    )
    session.add(relation)
    await session.commit()
    doctor = await session.get(User, DOCTOR_ID)

    response = await get_patient_graph(
        request=_request(PATIENT_ALICE_ID),
        patient_id=PATIENT_ALICE_ID,
        db=session,
        current_user=doctor,
    )

    assert len(response.edges) == 1
    edge = response.edges[0]
    assert edge.id == f"edge-{relation.id}"
    assert edge.from_node == f"node-{source.id}"
    assert edge.to_node == f"node-{target.id}"
    assert edge.label == "treats"
    assert edge.source_document_id == document.id
    assert edge.source_chunk_id == chunk.id

    clinical_nodes = {node.id: node for node in response.nodes if node.type != "patient"}
    assert clinical_nodes[f"node-{source.id}"].source_document_id == document.id
    assert clinical_nodes[f"node-{source.id}"].source_chunk_id == chunk.id
    assert clinical_nodes[f"node-{target.id}"].source_document_id == document.id
    assert clinical_nodes[f"node-{target.id}"].source_chunk_id == chunk.id
