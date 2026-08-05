from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from hospital_ai.db.clinical_graph import GraphEntity, GraphMention, GraphRelationAssertion, GraphRelationEvidence
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import DocumentChunk
from hospital_ai.services.graph_index import GraphIndexService
from hospital_ai.services.graph_rag import ExtractedEntity, ExtractedRelation, GraphExtraction
from tests.conftest import create_indexed_document


@pytest.mark.asyncio
async def test_concurrent_sources_share_canonical_rows_and_keep_provenance(session_and_settings) -> None:
    session, _ = session_and_settings
    doc_a = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Concurrent graph source A",
        content="Metformin treats diabetes.",
    )
    doc_b = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Concurrent graph source B",
        content="Metformin treats diabetes.",
    )
    chunk_ids = [
        row.id
        for row in (
            await session.execute(select(DocumentChunk).where(DocumentChunk.document_id.in_((doc_a.id, doc_b.id))))
        ).scalars()
    ]
    generation_ids = {
        document_id: document_generation_id
        for document_id, document_generation_id in (
            (doc_a.id, doc_a.active_index_generation_id),
            (doc_b.id, doc_b.active_index_generation_id),
        )
    }
    extraction = GraphExtraction(
        entities=[
            ExtractedEntity(normalized_label="metformin", entity_type="drug"),
            ExtractedEntity(normalized_label="diabetes", entity_type="condition"),
        ],
        relations=[ExtractedRelation("metformin", "diabetes", "treats")],
    )

    session_factory = async_sessionmaker(session.bind, expire_on_commit=False)

    async def index_one(chunk_id: uuid.UUID) -> None:
        async with session_factory() as worker_session:
            chunk = await worker_session.get(DocumentChunk, chunk_id)
            assert chunk is not None
            await GraphIndexService(worker_session).index_chunk(
                generation_ids[chunk.document_id],
                chunk,
                extraction,
            )
            await worker_session.commit()

    await asyncio.gather(*(index_one(chunk_id) for chunk_id in chunk_ids))

    entities = list((await session.execute(select(GraphEntity))).scalars())
    assertions = list((await session.execute(select(GraphRelationAssertion))).scalars())
    mentions = list((await session.execute(select(GraphMention))).scalars())
    evidence = list((await session.execute(select(GraphRelationEvidence))).scalars())

    assert len([row for row in entities if row.patient_id == PATIENT_ALICE_ID]) == 2
    assert len([row for row in assertions if row.patient_id == PATIENT_ALICE_ID]) == 1
    assert len(mentions) == 4
    assert len(evidence) == 2
    assert len({row.independent_source_identity for row in mentions}) == 2
    assert len({row.independent_source_identity for row in evidence}) == 2
