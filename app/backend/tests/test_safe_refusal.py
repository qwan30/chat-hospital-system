"""Tests for safe-refusal behaviour of reasoning pipelines.

Verifies that queries with no matching evidence return the standard
"could not find sufficient evidence" message and empty citations,
rather than hallucinating an answer.
"""

import pytest

from hospital_ai.services.reasoning import (
    DISCLAIMER,
    NO_EVIDENCE_ANSWER,
    DecomposeQAPipeline,
    ReasoningResult,
    SimpleQAPipeline,
)
from hospital_ai.services.retrieval import RetrievedChunk
from tests.conftest import create_indexed_document

# ── Helpers ──────────────────────────────────────────────────────────────


def _empty_evidence() -> list:
    """Return an empty evidence list simulating zero retrieval hits."""
    return []


# ── Tests ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_simple_qa_safe_refusal_with_no_evidence(session_and_settings):
    """SimpleQAPipeline returns safe refusal when no evidence is retrieved."""
    session, settings = session_and_settings
    pipeline = SimpleQAPipeline(settings)

    result = await pipeline.run(
        question="What colour is the patient's cat?",
        evidence=_empty_evidence(),
    )

    assert isinstance(result, ReasoningResult)
    assert result.answer == NO_EVIDENCE_ANSWER
    assert result.citations == []
    assert result.confidence == "low"
    assert result.disclaimer == DISCLAIMER
    assert result.pipeline == "simple_qa"


@pytest.mark.asyncio
async def test_decompose_qa_safe_refusal_with_no_evidence(session_and_settings):
    """DecomposeQAPipeline returns safe refusal when no evidence is retrieved."""
    session, settings = session_and_settings
    pipeline = DecomposeQAPipeline(settings)

    result = await pipeline.run(
        question="What is the weather outside?",
        evidence=_empty_evidence(),
    )

    assert isinstance(result, ReasoningResult)
    assert result.answer == NO_EVIDENCE_ANSWER
    assert result.citations == []
    assert result.confidence == "low"


@pytest.mark.asyncio
async def test_simple_qa_safe_refusal_preserves_disclaimer(session_and_settings):
    """Disclaimer is always set, even on safe-refusal responses."""
    session, settings = session_and_settings
    pipeline = SimpleQAPipeline(settings)

    result = await pipeline.run(
        question="Tell me something completely unrelated to any medical record.",
        evidence=[],
    )

    assert DISCLAIMER in result.disclaimer
    assert "clinical staff must verify" in result.disclaimer.lower()


@pytest.mark.asyncio
async def test_simple_qa_answer_with_valid_evidence(session_and_settings):
    """When evidence IS available, a non-empty answer should be returned."""
    session, settings = session_and_settings
    pipeline = SimpleQAPipeline(settings)

    # Create a document with indexed content
    from sqlalchemy import select

    from hospital_ai.db.models import Patient, User

    user = (await session.execute(select(User).limit(1))).scalar_one()
    patient = (await session.execute(select(Patient).limit(1))).scalar_one()

    doc = await create_indexed_document(
        session,
        patient_id=patient.id,
        uploaded_by=user.id,
        title="Test Protocol",
        content="The standard protocol for sepsis includes broad-spectrum antibiotics within 1 hour.",
    )

    # Build a simulated retrieval chunk
    import uuid

    evidence = [
        RetrievedChunk(
            evidence_id="E1",
            document_id=doc.id,
            document_title="Test Protocol",
            page=1,
            chunk_id=uuid.uuid4(),
            score=0.85,
            content="The standard protocol for sepsis includes broad-spectrum antibiotics within 1 hour.",
            metadata={},
        ),
    ]

    result = await pipeline.run(
        question="What is the sepsis protocol?",
        evidence=evidence,
    )

    assert result.answer != NO_EVIDENCE_ANSWER
    assert result.answer  # Non-empty
    assert result.pipeline == "simple_qa"


@pytest.mark.asyncio
async def test_decompose_refusal_single_subquestion(session_and_settings):
    """A question that cannot be decomposed falls back to simple QA refusal."""
    session, settings = session_and_settings
    pipeline = DecomposeQAPipeline(settings)

    result = await pipeline.run(
        question="What?",  # Too short to decompose
        evidence=[],
    )

    assert result.answer == NO_EVIDENCE_ANSWER
    assert result.pipeline == "decompose_qa"
