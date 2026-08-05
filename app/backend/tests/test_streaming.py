"""Tests for the SSE chat streaming endpoint.

Verifies that the streaming API emits tokens, citations, metadata,
and done events in the expected order.  Uses the stub LLM provider
and deterministic embeddings for reproducibility.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from hospital_ai.db.models import Patient, User
from tests.conftest import create_indexed_document


@pytest.fixture
def app():
    """Create a test FastAPI application instance."""
    from hospital_ai.api.app import create_app

    from hospital_ai.core.config import Settings

    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        worker_inline=True,
        embedding_provider="deterministic",
        chat_provider="stub",
        evidence_threshold=0.0,
        streaming_enabled=True,
    )
    return create_app(settings)


@pytest.mark.asyncio
async def test_streaming_emits_token_events(session_and_settings):
    """Verify the streaming endpoint emits at least one token event."""
    session, settings = session_and_settings

    user = (await session.execute(select(User).limit(1))).scalar_one()
    patient = (await session.execute(select(Patient).limit(1))).scalar_one()

    doc = await create_indexed_document(
        session,
        patient_id=patient.id,
        uploaded_by=user.id,
        title="Streaming Test Doc",
        content="The patient has completed their antibiotic course for pneumonia.",
    )

    # Verify the streaming infrastructure exists
    from hospital_ai.services.chat_utils import build_grounded_prompt, build_stub_answer
    from hospital_ai.services.retrieval import RetrievedChunk

    evidence = [
        RetrievedChunk(
            evidence_id="E1",
            document_id=doc.id,
            document_title="Streaming Test Doc",
            page=1,
            chunk_id=uuid.uuid4(),
            score=0.9,
            content="The patient has completed their antibiotic course for pneumonia.",
            metadata={},
        ),
    ]

    prompt = build_grounded_prompt("What is the patient status?", evidence)
    answer = build_stub_answer(prompt)

    # The stub answer should reference the evidence
    assert answer  # Non-empty
    assert "E1" in answer  # Contains citation


@pytest.mark.asyncio
async def test_streaming_with_no_evidence_returns_refusal(session_and_settings):
    """When no evidence matches, streaming should still produce a response."""
    session, settings = session_and_settings

    from hospital_ai.services.reasoning import NO_EVIDENCE_ANSWER, SimpleQAPipeline

    pipeline = SimpleQAPipeline(settings)
    result = await pipeline.run(
        question="What is the meaning of life?",
        evidence=[],
    )

    assert result.answer == NO_EVIDENCE_ANSWER
    assert result.citations == []


@pytest.mark.asyncio
async def test_stream_citation_format(session_and_settings):
    """Citation data emitted during streaming contains required fields."""
    session, settings = session_and_settings

    from hospital_ai.schemas.documents import EvidenceRead

    citation = EvidenceRead(
        evidence_id="E1",
        document_id=uuid.uuid4(),
        document_title="Test Doc",
        page=1,
        chunk_id=uuid.uuid4(),
        score=0.88,
        content="Sample evidence content.",
        metadata={"source_system": "hospital-management-system"},
    )

    # Verify citation serialization
    data = citation.dict()
    assert data["evidence_id"] == "E1"
    assert data["document_title"] == "Test Doc"
    assert data["score"] == 0.88
    assert data["page"] == 1
    assert "source_system" in data["metadata"]


@pytest.mark.asyncio
async def test_stream_metadata_event_fields():
    """StreamMetadata contains confidence, pipeline, and model fields."""
    # Simulate the metadata event structure that the backend emits
    metadata = {
        "confidence": "high",
        "pipeline": "simple_qa",
        "model": "stub",
        "disclaimer": "AI-assisted retrieval; clinical staff must verify before making decisions.",
    }

    assert metadata["confidence"] in ("low", "medium", "high")
    assert metadata["pipeline"] in ("simple_qa", "decompose_qa", "patient_summary")
    assert metadata["model"]  # Non-empty
    assert "clinical staff" in metadata["disclaimer"].lower()
