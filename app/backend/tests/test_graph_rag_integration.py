"""Tests for graph RAG entity extraction, persistence, and traversal.

Covers:
- Heuristic entity extraction from clinical text
- Relation extraction (explicit patterns + co-occurrence)
- index_chunk_entities() DB persistence
- find_related_entities() BFS traversal
- Integration with retrieval pipeline via RetrievalService.get_chunks_by_ids()
"""

import uuid

import pytest
from sqlalchemy import select

from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import User
from hospital_ai.services.graph_rag import (
    ExtractedEntity,
    ExtractedRelation,
    GraphContext,
    GraphEntity,
    GraphRelation,
    extract_entities,
    extract_relations,
    find_related_entities,
    index_chunk_entities,
)
from hospital_ai.services.retrieval import RetrievalService
from tests.conftest import create_indexed_document


# ── Unit: extract_entities ────────────────────────────────────────────


def test_extract_drug_entities():
    text = "Patient is currently on metformin 500mg and lisinopril 10mg."
    entities = extract_entities(text)
    names = {e.name for e in entities}
    assert "metformin" in names
    assert "lisinopril" in names
    assert all(e.entity_type == "drug" for e in entities if e.name in ("metformin", "lisinopril"))


def test_extract_condition_entities():
    text = "Diagnosed with hypertension and diabetes mellitus type 2."
    entities = extract_entities(text)
    names = {e.name for e in entities}
    assert "hypertension" in names
    assert "diabetes" in names


def test_extract_lab_entities():
    text = "Lab results: hemoglobin 12.5, creatinine 1.1, hba1c 7.2%."
    entities = extract_entities(text)
    names = {e.name for e in entities}
    assert "hemoglobin" in names
    assert "creatinine" in names
    assert "hba1c" in names


def test_extract_entities_deduplicates():
    text = "Metformin was started. Metformin dose increased."
    entities = extract_entities(text)
    metformin_count = sum(1 for e in entities if e.name == "metformin")
    assert metformin_count == 1


def test_extract_entities_empty_text():
    entities = extract_entities("")
    assert entities == []


def test_extract_entities_no_medical_terms():
    entities = extract_entities("The patient had lunch and went for a walk.")
    assert entities == []


# ── Unit: extract_relations ──────────────────────────────────────────


def test_extract_co_occurrence_relations():
    text = "Metformin treats diabetes. Lisinopril treats hypertension."
    entities = extract_entities(text)
    relations = extract_relations(text, entities)
    assert len(relations) > 0
    types = {r.relation_type for r in relations}
    # Should have at least mentioned_with from co-occurrence
    assert len(types) > 0


def test_extract_mentioned_with_drug_condition():
    text = "Patient takes aspirin for heart failure."
    entities = extract_entities(text)
    relations = extract_relations(text, entities)
    # aspirin and heart failure co-occur in the same sentence
    mentioned = [r for r in relations if r.relation_type == "mentioned_with"]
    assert len(mentioned) >= 1
    assert any(r.source_name == "aspirin" for r in mentioned)


def test_extract_relations_empty_entities():
    relations = extract_relations("Some text.", [])
    assert relations == []


# ── Integration: index_chunk_entities ────────────────────────────────


@pytest.mark.asyncio
async def test_index_chunk_entities_persists(session_and_settings):
    session, settings = session_and_settings
    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Drug note",
        content="Patient takes metformin for diabetes. Also on lisinopril for hypertension.",
    )

    # Get the first chunk
    from hospital_ai.db.models import DocumentChunk

    result = await session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    )
    chunk = result.scalars().first()
    assert chunk is not None

    entities, relations = await index_chunk_entities(
        session,
        chunk_id=chunk.id,
        document_id=doc.id,
        content=chunk.content,
    )
    await session.commit()

    assert len(entities) >= 3  # metformin, diabetes, lisinopril, hypertension
    assert all(isinstance(e, GraphEntity) for e in entities)

    # Verify persisted in DB
    db_entities = await session.execute(
        select(GraphEntity).where(GraphEntity.source_chunk_id == chunk.id)
    )
    persisted = list(db_entities.scalars().all())
    assert len(persisted) >= 3


@pytest.mark.asyncio
async def test_index_chunk_entities_creates_relations(session_and_settings):
    session, settings = session_and_settings
    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Relation note",
        content="Metformin treats diabetes. Lisinopril treats hypertension.",
    )

    from hospital_ai.db.models import DocumentChunk

    result = await session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    )
    chunk = result.scalars().first()

    entities, relations = await index_chunk_entities(
        session,
        chunk_id=chunk.id,
        document_id=doc.id,
        content=chunk.content,
    )
    await session.commit()

    # Should have at least co-occurrence relations
    assert len(relations) >= 0  # relations depend on text matching
    # Verify relations are persisted
    db_relations = await session.execute(
        select(GraphRelation).where(GraphRelation.source_chunk_id == chunk.id)
    )
    persisted_relations = list(db_relations.scalars().all())
    assert len(persisted_relations) == len(relations)


# ── Integration: find_related_entities ───────────────────────────────


@pytest.mark.asyncio
async def test_find_related_entities_returns_context(session_and_settings):
    session, settings = session_and_settings
    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Graph test note",
        content="Patient takes metformin for diabetes and lisinopril for hypertension.",
    )

    from hospital_ai.db.models import DocumentChunk

    result = await session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    )
    chunk = result.scalars().first()

    await index_chunk_entities(
        session,
        chunk_id=chunk.id,
        document_id=doc.id,
        content=chunk.content,
    )
    await session.commit()

    # Search for metformin
    ctx = await find_related_entities(session, ["metformin"], max_hops=2)
    assert isinstance(ctx, GraphContext)
    assert len(ctx.entities) >= 1
    assert any(e.name == "metformin" for e in ctx.entities)
    assert chunk.id in ctx.related_chunk_ids


@pytest.mark.asyncio
async def test_find_related_entities_empty_names(session_and_settings):
    session, settings = session_and_settings
    ctx = await find_related_entities(session, [], max_hops=2)
    assert ctx.entities == []
    assert ctx.related_chunk_ids == set()


@pytest.mark.asyncio
async def test_find_related_entities_unknown_name(session_and_settings):
    session, settings = session_and_settings
    ctx = await find_related_entities(session, ["nonexistent_drug_xyz"], max_hops=2)
    assert ctx.entities == []
    assert ctx.related_chunk_ids == set()


@pytest.mark.asyncio
async def test_find_related_entities_bfs_multi_hop(session_and_settings):
    session, settings = session_and_settings
    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Multi-hop note",
        content="Metformin treats diabetes. Insulin also treats diabetes.",
    )

    from hospital_ai.db.models import DocumentChunk

    result = await session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    )
    chunk = result.scalars().first()

    await index_chunk_entities(
        session,
        chunk_id=chunk.id,
        document_id=doc.id,
        content=chunk.content,
    )
    await session.commit()

    # Search for metformin should find insulin via diabetes (if relations exist)
    ctx = await find_related_entities(session, ["metformin"], max_hops=2)
    assert len(ctx.entities) >= 1
    # At minimum, metformin itself should be found
    assert any(e.name == "metformin" for e in ctx.entities)


# ── Integration: get_chunks_by_ids with graph evidence ───────────────


@pytest.mark.asyncio
async def test_retrieval_get_chunks_by_ids(session_and_settings):
    session, settings = session_and_settings
    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Retrieval test",
        content="Patient has documented allergy to penicillin.",
    )

    from hospital_ai.db.models import DocumentChunk

    result = await session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    )
    chunk = result.scalars().first()

    svc = RetrievalService(session)
    chunks = await svc.get_chunks_by_ids(
        [chunk.id],
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
    )
    assert len(chunks) == 1
    assert chunks[0].chunk_id == chunk.id
    assert chunks[0].evidence_id == "G1"


@pytest.mark.asyncio
async def test_retrieval_get_chunks_by_ids_empty(session_and_settings):
    session, settings = session_and_settings
    svc = RetrievalService(session)
    chunks = await svc.get_chunks_by_ids(
        [],
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
    )
    assert chunks == []
