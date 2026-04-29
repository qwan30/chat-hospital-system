"""Tests for reasoning pipelines."""

import uuid
from typing import Tuple

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings
from hospital_ai.services.reasoning import (
    DecomposeQAPipeline,
    PatientSummaryPipeline,
    SimpleQAPipeline,
    _decompose_question,
)
from hospital_ai.services.retrieval import RetrievedChunk


def _make_chunk(
    evidence_id: str = "E1",
    title: str = "Lab Report",
    content: str = "Patient has elevated blood pressure 140/90 mmHg.",
    score: float = 0.85,
    page: int = 1,
) -> RetrievedChunk:
    return RetrievedChunk(
        evidence_id=evidence_id,
        document_id=uuid.uuid4(),
        document_title=title,
        page=page,
        chunk_id=uuid.uuid4(),
        score=score,
        content=content,
        metadata={"source_system": "test"},
    )


@pytest.fixture
def stub_settings() -> Settings:
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        embedding_provider="deterministic",
        chat_provider="stub",
        evidence_threshold=0.0,
    )


# ── SimpleQAPipeline ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_simple_qa_returns_answer_with_citations(stub_settings: Settings) -> None:
    evidence = [
        _make_chunk("E1", "Lab Report", "Blood pressure 140/90 mmHg recorded.", 0.90),
        _make_chunk("E2", "Encounter Note", "Patient is on Lisinopril 10mg.", 0.75),
    ]

    result = await SimpleQAPipeline(stub_settings).run(
        question="What is the patient's blood pressure?",
        evidence=evidence,
    )

    assert result.pipeline == "simple_qa"
    assert result.answer  # Non-empty answer
    assert result.confidence in ("high", "medium", "low")
    assert result.disclaimer  # Has a disclaimer


@pytest.mark.asyncio
async def test_simple_qa_no_evidence_returns_safe_message(stub_settings: Settings) -> None:
    result = await SimpleQAPipeline(stub_settings).run(
        question="What is the patient's blood pressure?",
        evidence=[],
    )

    assert "could not find" in result.answer.lower()
    assert result.confidence == "low"
    assert result.citations == []


@pytest.mark.asyncio
async def test_simple_qa_single_evidence(stub_settings: Settings) -> None:
    evidence = [
        _make_chunk("E1", "CBC Report", "WBC count: 7500 cells/uL (normal range).", 0.88),
    ]

    result = await SimpleQAPipeline(stub_settings).run(
        question="What is the WBC count?",
        evidence=evidence,
    )

    assert result.answer
    assert "[E1]" in result.answer


# ── DecomposeQAPipeline ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_decompose_qa_with_complex_question(stub_settings: Settings) -> None:
    evidence = [
        _make_chunk("E1", "Labs", "Hemoglobin: 12.5 g/dL", 0.80),
        _make_chunk("E2", "Encounter", "Blood pressure: 130/85", 0.78),
        _make_chunk("E3", "Rx", "Metformin 500mg twice daily", 0.72),
    ]

    result = await DecomposeQAPipeline(stub_settings).run(
        question="What is the patient's hemoglobin level and what medications are they taking?",
        evidence=evidence,
    )

    assert result.pipeline == "decompose_qa"
    assert result.answer
    assert result.sub_questions is not None


@pytest.mark.asyncio
async def test_decompose_qa_simple_fallback(stub_settings: Settings) -> None:
    """A simple question should not decompose."""
    evidence = [
        _make_chunk("E1", "Labs", "Hemoglobin: 12.5 g/dL", 0.80),
    ]

    result = await DecomposeQAPipeline(stub_settings).run(
        question="What is the hemoglobin level?",
        evidence=evidence,
    )

    assert result.pipeline == "decompose_qa"
    # Should fall back to simple pipeline since question is not decomposable
    assert result.sub_questions is not None
    assert len(result.sub_questions) == 1


@pytest.mark.asyncio
async def test_decompose_qa_no_evidence(stub_settings: Settings) -> None:
    result = await DecomposeQAPipeline(stub_settings).run(
        question="What are the lab results and medications?",
        evidence=[],
    )

    assert "could not find" in result.answer.lower()
    assert result.confidence == "low"


# ── PatientSummaryPipeline ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_patient_summary_produces_structured_output(stub_settings: Settings) -> None:
    evidence = [
        _make_chunk("E1", "Demographics", "John Doe, Male, 65 years", 0.90),
        _make_chunk("E2", "Conditions", "Type 2 diabetes, hypertension", 0.85),
        _make_chunk("E3", "Labs", "HbA1c: 7.2%, Creatinine: 1.1 mg/dL", 0.82),
    ]

    result = await PatientSummaryPipeline(stub_settings).run(
        patient_name="John Doe",
        evidence=evidence,
    )

    assert result.pipeline == "patient_summary"
    assert result.answer
    assert result.confidence in ("high", "medium", "low")


@pytest.mark.asyncio
async def test_patient_summary_no_evidence(stub_settings: Settings) -> None:
    result = await PatientSummaryPipeline(stub_settings).run(
        patient_name="Unknown",
        evidence=[],
    )

    assert "no evidence" in result.answer.lower()
    assert result.confidence == "low"
    assert result.citations == []


# ── Decompose heuristic ──────────────────────────────────────────────────


def test_decompose_question_splits_on_and() -> None:
    parts = _decompose_question(
        "What is the blood pressure and what medications are prescribed?"
    )
    assert len(parts) >= 2


def test_decompose_question_splits_on_comma() -> None:
    parts = _decompose_question(
        "Show hemoglobin levels, creatinine, and blood pressure"
    )
    assert len(parts) >= 2


def test_decompose_question_no_split_for_simple() -> None:
    parts = _decompose_question("What is the hemoglobin?")
    assert len(parts) == 1
    assert parts[0] == "What is the hemoglobin?"


def test_decompose_question_ignores_short_fragments() -> None:
    parts = _decompose_question("Show A and B and the full blood count results for the patient")
    # "A" and "B" are too short (<10 chars), should be filtered
    assert all(len(p) > 10 for p in parts)
