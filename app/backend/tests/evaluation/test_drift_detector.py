from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from hospital_ai.evaluation.contracts import (
    DriftGateResult,
    DriftViolation,
    MetricDriftComparison,
)
from hospital_ai.evaluation.drift_detector import evaluate_metric_drift


def test_drift_data_contracts_instantiation() -> None:
    comp = MetricDriftComparison(
        metric_name="faithfulness_rate",
        baseline_value=0.9640,
        candidate_value=0.9500,
        delta=-0.0140,
        tolerance=-0.0200,
        higher_is_better=True,
        hard_gate_min=0.9000,
        status="passed",
    )
    assert comp.metric_name == "faithfulness_rate"
    assert comp.status == "passed"

    violation = DriftViolation(
        metric_name="unauthorized_evidence_count",
        violation_type="hard_gate",
        baseline_value=0.0,
        candidate_value=1.0,
        message="Critical PHI Leakage: 1 unauthorized chunk returned.",
    )
    assert violation.violation_type == "hard_gate"

    result = DriftGateResult(
        verdict="GO",
        passed=True,
        total_metrics_evaluated=1,
        violation_count=0,
        violations=(),
        comparisons=(comp,),
        git_sha_baseline="528541f",
        git_sha_candidate="d7b198f",
    )
    assert result.verdict == "GO"


def test_drift_detector_passes_on_identical_metrics() -> None:

    data = {
        "unauthorized_evidence_count": 0,
        "wrong_patient_citations_count": 0,
        "recall_at_5": 1.0,
        "mrr": 1.0,
        "faithfulness_rate": 0.9640,
        "answer_relevance_rate": 0.9480,
        "citation_precision": 0.9520,
        "decimal_misread_count": 0,
        "mean_latency_seconds": 0.28,
    }
    result = evaluate_metric_drift(candidate_summary=data, baseline_summary=data)
    assert result.verdict == "GO"
    assert result.passed is True
    assert result.violation_count == 0


def test_drift_detector_fails_on_phi_leakage() -> None:
    baseline = {"unauthorized_evidence_count": 0, "faithfulness_rate": 0.96}
    candidate = {"unauthorized_evidence_count": 1, "faithfulness_rate": 0.96}
    result = evaluate_metric_drift(candidate_summary=candidate, baseline_summary=baseline)
    assert result.verdict == "NO-GO"
    assert result.violation_count == 1
    assert result.violations[0].metric_name == "unauthorized_evidence_count"


def test_drift_detector_fails_on_faithfulness_drop() -> None:
    baseline = {"faithfulness_rate": 0.9640}
    candidate = {"faithfulness_rate": 0.8800}
    result = evaluate_metric_drift(candidate_summary=candidate, baseline_summary=baseline)
    assert result.verdict == "NO-GO"
    assert result.violations[0].metric_name == "faithfulness_rate"


def test_drift_detector_fails_on_ocr_decimal_misread() -> None:
    baseline = {"decimal_misread_count": 0}
    candidate = {"decimal_misread_count": 1}
    result = evaluate_metric_drift(candidate_summary=candidate, baseline_summary=baseline)
    assert result.verdict == "NO-GO"
    assert result.violations[0].metric_name == "decimal_misread_count"


def test_drift_detector_fails_on_latency_spike() -> None:
    baseline = {"mean_latency_seconds": 1.0}
    candidate = {"mean_latency_seconds": 1.5}
    result = evaluate_metric_drift(candidate_summary=candidate, baseline_summary=baseline)
    assert result.verdict == "NO-GO"
    assert result.violations[0].metric_name == "mean_latency_seconds"


def test_drift_detector_handles_missing_keys_gracefully() -> None:
    baseline = {"faithfulness_rate": 0.96}
    candidate = {}
    result = evaluate_metric_drift(candidate_summary=candidate, baseline_summary=baseline)
    assert result.verdict == "NO-GO"


def test_verify_ai_regression_cli_execution(tmp_path: Path) -> None:
    baseline_file = tmp_path / "baseline.json"
    candidate_file = tmp_path / "candidate.json"
    report_file = tmp_path / "drift_report.json"

    data = {
        "unauthorized_evidence_count": 0,
        "faithfulness_rate": 0.96,
        "recall_at_5": 1.0,
    }
    baseline_file.write_text(json.dumps(data), encoding="utf-8")
    candidate_file.write_text(json.dumps(data), encoding="utf-8")

    cmd = [
        sys.executable,
        "scripts/verify_ai_regression.py",
        "--candidate",
        str(candidate_file),
        "--baseline",
        str(baseline_file),
        "--output-report",
        str(report_file),
    ]
    res = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0
    assert report_file.exists()
    report = json.loads(report_file.read_text(encoding="utf-8"))
    assert report["verdict"] == "GO"
