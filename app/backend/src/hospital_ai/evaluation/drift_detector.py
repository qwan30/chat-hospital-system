"""Pure comparison engine for AI evaluation hard quality gates and relative drift tolerances."""
from __future__ import annotations


from typing import Any

from hospital_ai.evaluation.contracts import (
    DriftGateResult,
    DriftViolation,
    MetricDriftComparison,
)

# (metric_name, higher_is_better, hard_gate_min, hard_gate_max, relative_tolerance)
_METRIC_RULES: tuple[tuple[str, bool, Optional[float], Optional[float], float], ...] = (
    ("unauthorized_evidence_count", False, None, 0.0, 0.0),
    ("wrong_patient_citations_count", False, None, 0.0, 0.0),
    ("recall_at_5", True, 0.9000, None, 0.0000),
    ("mrr", True, 0.8500, None, -0.0100),
    ("graph_path_recall", True, 1.0000, None, 0.0000),
    ("faithfulness_rate", True, 0.9000, None, -0.0200),
    ("answer_relevance_rate", True, 0.9000, None, -0.0200),
    ("citation_precision", True, 0.9500, None, -0.0100),
    ("decimal_misread_count", False, None, 0.0, 0.0),
    ("clinical_field_accuracy", True, 0.9500, None, -0.0100),
    ("mean_latency_seconds", False, None, None, 0.20),
)


def evaluate_metric_drift(
    candidate_summary: dict[str, Any],
    baseline_summary: dict[str, Any],
    git_sha_candidate: str = "unknown",
    git_sha_baseline: str = "unknown",
) -> DriftGateResult:
    comparisons: list[MetricDriftComparison] = []
    violations: list[DriftViolation] = []

    for metric_name, higher_is_better, hard_min, hard_max, tolerance in _METRIC_RULES:
        if metric_name not in candidate_summary and metric_name not in baseline_summary:
            continue

        base_val = float(baseline_summary.get(metric_name, 0.0))
        cand_val = float(candidate_summary.get(metric_name, -999.0) if metric_name in candidate_summary else -999.0)

        if metric_name not in candidate_summary:
            violations.append(
                DriftViolation(
                    metric_name=metric_name,
                    violation_type="hard_gate",
                    baseline_value=base_val,
                    candidate_value=cand_val,
                    message=f"Missing metric '{metric_name}' in candidate summary.",
                )
            )
            comparisons.append(
                MetricDriftComparison(
                    metric_name=metric_name,
                    baseline_value=base_val,
                    candidate_value=cand_val,
                    delta=0.0,
                    tolerance=tolerance,
                    higher_is_better=higher_is_better,
                    hard_gate_min=hard_min,
                    hard_gate_max=hard_max,
                    status="failed_hard_gate",
                )
            )
            continue

        delta = cand_val - base_val
        status = "passed"

        if hard_min is not None and cand_val < hard_min:
            status = "failed_hard_gate"
            violations.append(
                DriftViolation(
                    metric_name=metric_name,
                    violation_type="hard_gate",
                    baseline_value=base_val,
                    candidate_value=cand_val,
                    message=f"Hard gate min failure: {cand_val:.4f} < required {hard_min:.4f}",
                )
            )
        elif hard_max is not None and cand_val > hard_max:
            status = "failed_hard_gate"
            violations.append(
                DriftViolation(
                    metric_name=metric_name,
                    violation_type="hard_gate",
                    baseline_value=base_val,
                    candidate_value=cand_val,
                    message=f"Hard gate max failure: {cand_val:.4f} > max allowed {hard_max:.4f}",
                )
            )
        else:
            if metric_name == "mean_latency_seconds":
                pct_increase = (delta / base_val) if base_val > 0.0 else 0.0
                if pct_increase > tolerance:
                    status = "failed_drift"
                    violations.append(
                        DriftViolation(
                            metric_name=metric_name,
                            violation_type="relative_drift",
                            baseline_value=base_val,
                            candidate_value=cand_val,
                            message=(
                                f"Latency spike failure: +{pct_increase * 100:.1f}% exceeds "
                                f"max tolerance +{tolerance * 100:.1f}%"
                            ),
                        )
                    )
            elif higher_is_better:
                if delta < tolerance:
                    status = "failed_drift"
                    violations.append(
                        DriftViolation(
                            metric_name=metric_name,
                            violation_type="relative_drift",
                            baseline_value=base_val,
                            candidate_value=cand_val,
                            message=(
                                f"Relative drift failure: delta {delta:.4f} below tolerance threshold {tolerance:.4f}"
                            ),
                        )
                    )

            else:
                if delta > abs(tolerance):
                    status = "failed_drift"
                    violations.append(
                        DriftViolation(
                            metric_name=metric_name,
                            violation_type="relative_drift",
                            baseline_value=base_val,
                            candidate_value=cand_val,
                            message=f"Relative drift failure: count increase +{delta} exceeds tolerance {tolerance}",
                        )
                    )

        comparisons.append(
            MetricDriftComparison(
                metric_name=metric_name,
                baseline_value=base_val,
                candidate_value=cand_val,
                delta=delta,
                tolerance=tolerance,
                higher_is_better=higher_is_better,
                hard_gate_min=hard_min,
                hard_gate_max=hard_max,
                status=status,
            )
        )

    passed = len(violations) == 0
    return DriftGateResult(
        verdict="GO" if passed else "NO-GO",
        passed=passed,
        total_metrics_evaluated=len(comparisons),
        violation_count=len(violations),
        violations=tuple(violations),
        comparisons=tuple(comparisons),
        git_sha_baseline=git_sha_baseline,
        git_sha_candidate=git_sha_candidate,
    )
