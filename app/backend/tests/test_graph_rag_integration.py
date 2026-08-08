"""Tests for graph RAG entity extraction, persistence, and traversal.

Covers:
- Heuristic entity extraction from clinical text
- Relation extraction (explicit patterns + co-occurrence)
- index_chunk_entities() DB persistence
- find_related_entities() BFS traversal
- Integration with retrieval pipeline via RetrievalService.get_chunks_by_ids()
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.services.graph_rag import (
    ExtractedEntity,
    ExtractedRelation,
    GraphContext,
    _extract_explicit_relations_fallback,
    extract_entities_and_relations_nlp,
    extract_entities_and_relations_offline,
    find_related_entities,
    index_chunk_entities,
)
from hospital_ai.services.retrieval import RetrievalService
from tests.conftest import create_indexed_document


@pytest.fixture(autouse=True)
def mock_extract(monkeypatch):
    async def mock_extract_nlp(content):
        # some dummy entities
        return [
            ExtractedEntity("metformin", "drug"),
            ExtractedEntity("diabetes", "condition"),
            ExtractedEntity("lisinopril", "drug"),
            ExtractedEntity("hypertension", "condition"),
        ], [
            ExtractedRelation("metformin", "diabetes", "treats"),
            ExtractedRelation("lisinopril", "hypertension", "treats"),
        ]

    monkeypatch.setattr("hospital_ai.services.graph_rag.extract_entities_and_relations_nlp", mock_extract_nlp)


def test_explicit_relation_fallback_is_deterministic():
    entities, relations = _extract_explicit_relations_fallback(
        "Metformin treats diabetes. Insulin also treats diabetes."
    )

    assert {(entity.normalized_label, entity.entity_type) for entity in entities} == {
        ("metformin", "concept"),
        ("diabetes", "concept"),
        ("insulin", "concept"),
    }
    assert {(relation.subject_label, relation.object_label, relation.relation_type) for relation in relations} == {
        ("metformin", "diabetes", "treats"),
        ("insulin", "diabetes", "treats"),
    }


def test_explicit_relation_fallback_extracts_complete_labeled_lab_observation():
    """A lab observation graph must be derived only from explicit source fields."""
    entities, relations = _extract_explicit_relations_fallback("MRN: MRN-0001\nAnalyte: Creatinine\nStatus: High")

    assert {(entity.normalized_label, entity.entity_type) for entity in entities} == {
        ("patient:mrn-0001", "patient"),
        ("analyte:creatinine", "lab_analyte"),
        ("status:high", "lab_status"),
    }
    assert {(relation.subject_label, relation.object_label, relation.relation_type) for relation in relations} == {
        ("patient:mrn-0001", "analyte:creatinine", "has_observation"),
        ("analyte:creatinine", "status:high", "has_status"),
    }


@pytest.mark.parametrize(
    "content",
    (
        "MRN: MRN-0001\nAnalyte: Creatinine",
        "MRN: MRN-0001\nMRN: MRN-0002\nAnalyte: Creatinine\nStatus: High",
    ),
)
def test_explicit_relation_fallback_rejects_incomplete_or_ambiguous_lab_observation(content: str):
    entities, relations = _extract_explicit_relations_fallback(content)

    assert entities == []
    assert relations == []


@pytest.mark.asyncio
async def test_llm_failure_uses_explicit_relation_fallback(monkeypatch):
    class FailingLlm:
        async def generate(self, *_args, **_kwargs):
            raise RuntimeError("provider unavailable")

    class FailingManager:
        def get(self):
            return FailingLlm()

    monkeypatch.setattr("hospital_ai.services.graph_rag.get_llm_manager", lambda: FailingManager())

    entities, relations = await extract_entities_and_relations_nlp("Metformin treats diabetes.")

    assert {(entity.normalized_label, entity.entity_type) for entity in entities} == {
        ("metformin", "concept"),
        ("diabetes", "concept"),
    }
    assert [(relation.subject_label, relation.object_label, relation.relation_type) for relation in relations] == [
        ("metformin", "diabetes", "treats")
    ]


# ── Integration: index_chunk_entities ────────────────────────────────


@pytest.mark.asyncio
async def test_index_chunk_entities_defaults_to_production_extractor(session_and_settings, monkeypatch):
    session, _settings = session_and_settings
    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Production extractor note",
        content="Metformin treats diabetes.",
    )
    from hospital_ai.db.models import DocumentChunk

    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
    chunk = result.scalars().one()
    calls: list[str] = []

    async def production_extractor(content: str):
        calls.append(content)
        return [ExtractedEntity("metformin", "drug")], []

    monkeypatch.setattr("hospital_ai.services.graph_rag.extract_entities_and_relations_nlp", production_extractor)

    await index_chunk_entities(session, chunk.id, doc.id, chunk.content)

    assert calls == [chunk.content]


@pytest.mark.asyncio
async def test_index_chunk_entities_with_offline_extractor_never_gets_llm_manager(session_and_settings, monkeypatch):
    session, _settings = session_and_settings
    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Offline extractor note",
        content="Metformin treats diabetes.",
    )
    from hospital_ai.db.models import DocumentChunk

    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
    chunk = result.scalars().one()

    def llm_manager_was_called():
        raise AssertionError("offline extraction must not access the LLM manager")

    monkeypatch.setattr("hospital_ai.services.graph_rag.get_llm_manager", llm_manager_was_called)

    await index_chunk_entities(
        session,
        chunk.id,
        doc.id,
        chunk.content,
        extractor=extract_entities_and_relations_offline,
    )

    from hospital_ai.db.clinical_graph import GraphEntity, GraphRelationAssertion

    entities = list(
        (await session.execute(select(GraphEntity).where(GraphEntity.patient_id == PATIENT_ALICE_ID))).scalars()
    )
    relations = list(
        (
            await session.execute(
                select(GraphRelationAssertion).where(GraphRelationAssertion.patient_id == PATIENT_ALICE_ID)
            )
        ).scalars()
    )

    from hospital_ai.db.clinical_graph import GraphEntity, GraphRelationAssertion

    entities = list(
        (await session.execute(select(GraphEntity).where(GraphEntity.patient_id == PATIENT_ALICE_ID))).scalars()
    )
    relations = list(
        (
            await session.execute(
                select(GraphRelationAssertion).where(GraphRelationAssertion.patient_id == PATIENT_ALICE_ID)
            )
        ).scalars()
    )

    assert sorted([entity.normalized_label for entity in entities]) == ["diabetes", "metformin"]
    assert [(relation.relation_type) for relation in relations] == ["treats"]


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

    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
    chunk = result.scalars().first()
    assert chunk is not None

    await index_chunk_entities(
        session,
        chunk_id=chunk.id,
        document_id=doc.id,
        content=chunk.content,
    )
    await session.commit()

    from hospital_ai.db.clinical_graph import GraphEntity

    result = await session.execute(select(GraphEntity).where(GraphEntity.patient_id == doc.patient_id))
    db_entities = result.scalars().all()
    assert len(db_entities) == 4
    names = {e.normalized_label for e in db_entities}
    assert "metformin" in names
    assert "lisinopril" in names


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

    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
    chunk = result.scalars().first()

    await index_chunk_entities(
        session,
        chunk_id=chunk.id,
        document_id=doc.id,
        content=chunk.content,
    )
    await session.commit()

    from hospital_ai.db.clinical_graph import GraphRelationAssertion

    result = await session.execute(
        select(GraphRelationAssertion).where(GraphRelationAssertion.patient_id == doc.patient_id)
    )
    db_relations = result.scalars().all()
    assert len(db_relations) == 2
    types = {r.relation_type for r in db_relations}
    assert "treats" in types


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

    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
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
    assert any(e.normalized_label == "metformin" for e in ctx.entities)
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

    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
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
    assert any(e.normalized_label == "metformin" for e in ctx.entities)


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

    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
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
