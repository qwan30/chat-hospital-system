"""Unit tests for unified evaluation metrics, hard release gates, and blocking states."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hospital_ai.evaluation.unified_metrics import (
    BlockingEvaluationError,
    UnifiedEvaluationRunReport,
    UnifiedMetricsSummary,
    evaluate_hard_gates,
    evaluate_stream_metrics,
    evaluate_timeline_metrics,
    write_summary_json,
)


def test_evaluate_timeline_metrics_exact_identity_and_zero_superseded() -> None:
    expected = [
        {"event_id": "e1", "event_type": "lab", "evidence_locators": [{"source_path": "a.csv"}]},
        {"event_id": "e2", "event_type": "med", "evidence_locators": [{"source_path": "b.pdf"}]},
    ]
    observed = [
        {"event_id": "e1", "event_type": "lab", "evidence_paths": ["a.csv"], "superseded": False},
        {"event_id": "e2", "event_type": "med", "evidence_paths": ["b.pdf"], "superseded": False},
    ]
    result = evaluate_timeline_metrics(expected, observed)
    assert result.event_recall == 1.0
    assert result.evidence_identity_accuracy == 1.0
    assert result.superseded_retrieval_count == 0


def test_evaluate_timeline_metrics_detects_superseded_and_mismatched_identity() -> None:
    expected = [
        {"event_id": "e1", "event_type": "lab", "evidence_locators": [{"source_path": "a.csv"}]},
    ]
    observed = [
        {"event_id": "e1", "event_type": "lab", "evidence_paths": ["wrong.csv"], "superseded": True},
    ]
    result = evaluate_timeline_metrics(expected, observed)
    assert result.evidence_identity_accuracy == 0.0
    assert result.superseded_retrieval_count == 1


def test_evaluate_stream_metrics_sequence_and_interrupt_correctness() -> None:
    events = [
        {"type": "token", "sequence": 1, "content": "hello "},
        {"type": "token", "sequence": 2, "content": "world."},
        {"type": "done", "sequence": 3},
    ]
    result = evaluate_stream_metrics(events, interrupted=False, error_occurred=False)
    assert result.sequence_correctness is True
    assert result.interrupt_handling_correctness is True


def test_evaluate_stream_metrics_detects_sequence_gap() -> None:
    events = [
        {"type": "token", "sequence": 1, "content": "hello "},
        {"type": "token", "sequence": 5, "content": "gap"},
    ]
    result = evaluate_stream_metrics(events, interrupted=False, error_occurred=False)
    assert result.sequence_correctness is False


def test_evaluate_hard_gates_passes_when_all_zero_tolerance_met() -> None:
    summary = UnifiedMetricsSummary(
        unauthorized_evidence_count=0,
        wrong_patient_citations_count=0,
        superseded_retrieval_count=0,
        independent_reviewers_count=2,
        reproducible_hashes=True,
        displayed_graph_provenance=1.0,
        factual_claim_validation_passed=True,
        timeline_evidence_identity=1.0,
        sse_sequence_correct=True,
        sse_interrupt_correct=True,
        ocr_engine_available=True,
        review_completed=True,
    )
    gates, all_passed = evaluate_hard_gates(summary)
    assert all_passed is True
    assert all(g.passed for g in gates)


def test_evaluate_hard_gates_fails_on_unauthorized_or_wrong_patient() -> None:
    summary = UnifiedMetricsSummary(
        unauthorized_evidence_count=1,
        wrong_patient_citations_count=1,
        superseded_retrieval_count=0,
        independent_reviewers_count=2,
        reproducible_hashes=True,
        displayed_graph_provenance=1.0,
        factual_claim_validation_passed=True,
        timeline_evidence_identity=1.0,
        sse_sequence_correct=True,
        sse_interrupt_correct=True,
        ocr_engine_available=True,
        review_completed=True,
    )
    gates, all_passed = evaluate_hard_gates(summary)
    assert all_passed is False


def test_blocking_state_for_unavailable_ocr_or_incomplete_review() -> None:
    summary_no_ocr = UnifiedMetricsSummary(
        unauthorized_evidence_count=0,
        wrong_patient_citations_count=0,
        superseded_retrieval_count=0,
        independent_reviewers_count=2,
        reproducible_hashes=True,
        displayed_graph_provenance=1.0,
        factual_claim_validation_passed=True,
        timeline_evidence_identity=1.0,
        sse_sequence_correct=True,
        sse_interrupt_correct=True,
        ocr_engine_available=False,
        review_completed=True,
    )
    with pytest.raises(BlockingEvaluationError, match="unavailable real OCR"):
        evaluate_hard_gates(summary_no_ocr, raise_on_blocking=True)

    summary_no_review = summary_no_ocr.copy(update={"ocr_engine_available": True, "review_completed": False})
    with pytest.raises(BlockingEvaluationError, match="incomplete review"):
        evaluate_hard_gates(summary_no_review, raise_on_blocking=True)


def test_write_summary_json_persists_reproducible_report(tmp_path: Path) -> None:
    report = UnifiedEvaluationRunReport(
        run_id="run-123",
        timestamp="2026-08-05T12:00:00Z",
        git_sha="abcdef1234567890abcdef1234567890abcdef12",
        corpus_version="hospital-ai-unified-clinical-corpus-v3",
        corpus_hash="d" * 64,
        source_hashes={"doc1.pdf": "e" * 64},
        approved_revisions=("rev-1",),
        model_version="stub-v1",
        embedding_version="deterministic-v1",
        graph_version="graph-v1",
        prompt_version="prompt-v1",
        evaluator_version="eval-v1",
        metric_version="metric-v3",
        limitations=("offline execution",),
        metrics={"recall_at_5": 1.0},
        hard_gates_passed=True,
        blocking_state=False,
    )
    out_path = tmp_path / "summary.json"
    write_summary_json(report, out_path)
    assert out_path.is_file()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["run_id"] == "run-123"
    assert data["corpus_version"] == "hospital-ai-unified-clinical-corpus-v3"
    assert data["hard_gates_passed"] is True
