"""Unified Evaluation Metrics, Hard Gates, and Summary Reporting."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


class BlockingEvaluationError(Exception):
    """Raised when evaluation cannot produce a trustworthy score due to incomplete prerequisites."""


class TimelineMetricResult(BaseModel):
    event_recall: float
    evidence_identity_accuracy: float
    superseded_retrieval_count: int

    class Config:
        frozen = True


class StreamMetricResult(BaseModel):
    sequence_correctness: bool
    interrupt_handling_correctness: bool

    class Config:
        frozen = True


class UnifiedMetricsSummary(BaseModel):
    unauthorized_evidence_count: int = 0
    wrong_patient_citations_count: int = 0
    superseded_retrieval_count: int = 0
    independent_reviewers_count: int = 2
    reproducible_hashes: bool = True
    displayed_graph_provenance: float = 1.0
    factual_claim_validation_passed: bool = True
    timeline_evidence_identity: float = 1.0
    sse_sequence_correct: bool = True
    sse_interrupt_correct: bool = True
    ocr_engine_available: bool = True
    review_completed: bool = True


class GateResult(BaseModel):
    gate_name: str
    passed: bool
    reason: Optional[str] = None

    class Config:
        frozen = True


class UnifiedEvaluationRunReport(BaseModel):
    run_id: str
    timestamp: str
    git_sha: str
    corpus_version: str
    corpus_hash: str
    source_hashes: dict[str, str] = Field(default_factory=dict)
    approved_revisions: tuple[str, ...] = ()
    model_version: str
    embedding_version: str
    graph_version: str
    prompt_version: str
    evaluator_version: str
    metric_version: str
    limitations: tuple[str, ...] = ()
    metrics: dict[str, Any] = Field(default_factory=dict)
    hard_gates_passed: bool = False
    blocking_state: bool = False


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def evaluate_timeline_metrics(expected: Sequence[Any], observed: Sequence[Any]) -> TimelineMetricResult:
    """Calculate recall, evidence identity accuracy, and superseded retrieval count for timelines."""
    expected_count = len(expected)
    if not expected_count:
        return TimelineMetricResult(event_recall=1.0, evidence_identity_accuracy=1.0, superseded_retrieval_count=0)

    observed_by_id = {str(_get_val(obs, "event_id", "")): obs for obs in observed}
    matched_events = 0
    matched_identity = 0
    superseded_count = sum(1 for obs in observed if _get_val(obs, "superseded", False) is True)

    for exp in expected:
        event_id = str(_get_val(exp, "event_id", ""))
        obs = observed_by_id.get(event_id)
        if obs is not None:
            matched_events += 1
            exp_locs = _get_val(exp, "evidence_locators", [])
            exp_paths = {str(_get_val(loc, "source_path", "")) for loc in exp_locs}
            obs_paths = set(str(p) for p in _get_val(obs, "evidence_paths", []))
            if exp_paths and exp_paths == obs_paths and not _get_val(obs, "superseded", False):
                matched_identity += 1

    recall = matched_events / expected_count
    identity_acc = matched_identity / expected_count
    return TimelineMetricResult(
        event_recall=recall,
        evidence_identity_accuracy=identity_acc,
        superseded_retrieval_count=superseded_count,
    )


def evaluate_stream_metrics(
    events: Sequence[Any], interrupted: bool = False, error_occurred: bool = False
) -> StreamMetricResult:
    """Verify strictly increasing SSE sequence numbers and safe interrupt/error terminal outcomes."""
    seqs = []
    for event in events:
        seq = _get_val(event, "sequence")
        if seq is not None and isinstance(seq, int):
            seqs.append(seq)

    seq_correct = True
    if len(seqs) > 1:
        for i in range(1, len(seqs)):
            if seqs[i] != seqs[i - 1] + 1:
                seq_correct = False
                break

    interrupt_correct = True
    if interrupted or error_occurred:
        for event in events:
            if _get_val(event, "unvalidated") is True:
                interrupt_correct = False
                break

    return StreamMetricResult(
        sequence_correctness=seq_correct,
        interrupt_handling_correctness=interrupt_correct,
    )


def evaluate_hard_gates(
    summary: UnifiedMetricsSummary, raise_on_blocking: bool = True
) -> tuple[tuple[GateResult, ...], bool]:
    """Evaluate zero-tolerance release gates across all product stages."""
    if raise_on_blocking:
        if not summary.ocr_engine_available:
            raise BlockingEvaluationError("unavailable real OCR engine blocks evaluation score calculation")
        if not summary.review_completed or summary.independent_reviewers_count < 2:
            raise BlockingEvaluationError("incomplete review status blocks evaluation score calculation")

    gates = (
        GateResult(
            gate_name="zero_unauthorized_evidence",
            passed=summary.unauthorized_evidence_count == 0,
            reason=f"found {summary.unauthorized_evidence_count} unauthorized pieces of evidence",
        ),
        GateResult(
            gate_name="zero_wrong_patient_citations",
            passed=summary.wrong_patient_citations_count == 0,
            reason=f"found {summary.wrong_patient_citations_count} wrong-patient citations",
        ),
        GateResult(
            gate_name="zero_superseded_retrieval",
            passed=summary.superseded_retrieval_count == 0,
            reason=f"found {summary.superseded_retrieval_count} superseded chunks retrieved",
        ),
        GateResult(
            gate_name="two_independent_reviewers",
            passed=summary.independent_reviewers_count >= 2,
            reason=f"only {summary.independent_reviewers_count} independent reviewers found",
        ),
        GateResult(
            gate_name="reproducible_hashes",
            passed=summary.reproducible_hashes is True,
            reason="hashes were non-reproducible or mutated",
        ),
        GateResult(
            gate_name="100pct_displayed_graph_provenance",
            passed=summary.displayed_graph_provenance == 1.0,
            reason=f"graph provenance accuracy was {summary.displayed_graph_provenance}",
        ),
        GateResult(
            gate_name="factual_claim_validation",
            passed=summary.factual_claim_validation_passed is True,
            reason="factual claim validation failed",
        ),
        GateResult(
            gate_name="100pct_timeline_evidence_identity",
            passed=summary.timeline_evidence_identity == 1.0,
            reason=f"timeline evidence identity accuracy was {summary.timeline_evidence_identity}",
        ),
        GateResult(
            gate_name="sse_sequence_and_interrupt_correctness",
            passed=summary.sse_sequence_correct and summary.sse_interrupt_correct,
            reason="validated-SSE stream sequence or interrupt handling failed",
        ),
    )
    all_passed = all(g.passed for g in gates)
    return gates, all_passed


def write_summary_json(report: UnifiedEvaluationRunReport, path: Path) -> None:
    """Write out the final summary JSON file with deterministic schema mapping."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.json(indent=2), encoding="utf-8")
