# Automated CI Baseline Regression & Drift Detector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an automated AI Quality Gate and Regression Drift Detector CLI script (`verify_ai_regression.py`) integrated into GitHub Actions CI (`ci.yml`) to compare PR evaluation runs against a version-locked baseline snapshot (`baseline-release.json`), blocking PR merges on quality regressions.

**Architecture:** Pure Python comparison engine (`drift_detector.py`) enforcing Hard Quality Gates (Zero PHI leakage, Recall $\ge 0.90$, Faithfulness $\ge 90\%$, Zero OCR Decimal Misreads) and Relative Drift Tolerances (Faithfulness drop $\le 2\%$, Latency increase $\le 20\%$). Executive CLI wrapper (`verify_ai_regression.py`) renders Markdown tables to `$GITHUB_STEP_SUMMARY` and returns exit code `0` (`GO`) or `1` (`NO-GO`).

**Tech Stack:** Python 3.12, Pydantic v2 (`ConfigDict(frozen=True)`), pytest, GitHub Actions Workflow.

## Global Constraints

- Python 3.12 compatibility
- Pydantic v2 schema compliance (`model_config = ConfigDict(frozen=True)`)
- No new external system dependencies (pure Python standard library + existing `hospital_ai.evaluation` imports)
- Zero tolerance for PHI leakage (`unauthorized_evidence_count == 0` and `wrong_patient_citations_count == 0`)
- Zero tolerance for OCR decimal misreads (`decimal_misread_count == 0`)
- Full test coverage with `pytest` in `app/backend/tests/evaluation/test_drift_detector.py`

---

## File Structure & Responsibilities

```
app/backend/
├── src/hospital_ai/evaluation/
│   ├── contracts.py                # [MODIFY] Add MetricDriftComparison, DriftViolation, DriftGateResult
│   └── drift_detector.py           # [NEW] Core comparison logic & hard/relative gate evaluator
├── scripts/
│   └── verify_ai_regression.py     # [NEW] Executive CLI entrypoint & $GITHUB_STEP_SUMMARY renderer
├── data/evaluation/baselines/
│   └── baseline-release.json       # [NEW] Official version-locked baseline dataset metrics snapshot
└── tests/evaluation/
    └── test_drift_detector.py      # [NEW] Comprehensive unit & integration test suite
.github/workflows/
└── ci.yml                          # [MODIFY] Add automated drift verification gate step
```

---

## Tasks

### Task 1: Drift Data Contracts

**Files:**
- Modify: `app/backend/src/hospital_ai/evaluation/contracts.py:100-120`
- Create: `app/backend/tests/evaluation/test_drift_detector.py`

**Interfaces:**
- Consumes: `pydantic.BaseModel`, `pydantic.ConfigDict`
- Produces: `MetricDriftComparison`, `DriftViolation`, `DriftGateResult`

- [ ] **Step 1: Write the failing test for contract instantiation**

Create `app/backend/tests/evaluation/test_drift_detector.py`:
```python
from __future__ import annotations

import pytest
from hospital_ai.evaluation.contracts import (
    DriftGateResult,
    DriftViolation,
    MetricDriftComparison,
)


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd app/backend && .venv\Scripts\python.exe -m pytest tests/evaluation/test_drift_detector.py -v`
Expected: `ImportError: cannot import name 'MetricDriftComparison' from 'hospital_ai.evaluation.contracts'`

- [ ] **Step 3: Add Pydantic contracts to `contracts.py`**

Append to `app/backend/src/hospital_ai/evaluation/contracts.py`:
```python
class MetricDriftComparison(BaseModel):
    model_config = ConfigDict(frozen=True)

    metric_name: str
    baseline_value: float
    candidate_value: float
    delta: float
    tolerance: float
    higher_is_better: bool = True
    hard_gate_min: float | None = None
    hard_gate_max: float | None = None
    status: Literal["passed", "failed_drift", "failed_hard_gate"]


class DriftViolation(BaseModel):
    model_config = ConfigDict(frozen=True)

    metric_name: str
    violation_type: Literal["hard_gate", "relative_drift"]
    baseline_value: float
    candidate_value: float
    message: str


class DriftGateResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    verdict: Literal["GO", "NO-GO"]
    passed: bool
    total_metrics_evaluated: int
    violation_count: int
    violations: tuple[DriftViolation, ...]
    comparisons: tuple[MetricDriftComparison, ...]
    git_sha_baseline: str
    git_sha_candidate: str
```

Make sure `ConfigDict` is imported from `pydantic` at top of `contracts.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd app/backend && .venv\Scripts\python.exe -m pytest tests/evaluation/test_drift_detector.py -v`
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add app/backend/src/hospital_ai/evaluation/contracts.py app/backend/tests/evaluation/test_drift_detector.py
git commit -m "feat(eval): add DriftGateResult and metric comparison contracts"
```

---

### Task 2: Pure Drift Detector Engine

**Files:**
- Create: `app/backend/src/hospital_ai/evaluation/drift_detector.py`
- Modify: `app/backend/tests/evaluation/test_drift_detector.py`

**Interfaces:**
- Consumes: `hospital_ai.evaluation.contracts` (`DriftGateResult`, `MetricDriftComparison`, `DriftViolation`)
- Produces: `evaluate_metric_drift(candidate_summary: dict, baseline_summary: dict, git_sha_candidate: str = "unknown", git_sha_baseline: str = "unknown") -> DriftGateResult`

- [ ] **Step 1: Write failing tests for Hard Gates and Relative Drift in `test_drift_detector.py`**

Append to `app/backend/tests/evaluation/test_drift_detector.py`:
```python
from hospital_ai.evaluation.drift_detector import evaluate_metric_drift


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
    candidate = {"faithfulness_rate": 0.8800}  # Drop of 0.084 > max tolerance 0.02
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
    candidate = {"mean_latency_seconds": 1.5}  # 50% increase > 20% max allowed
    result = evaluate_metric_drift(candidate_summary=candidate, baseline_summary=baseline)
    assert result.verdict == "NO-GO"
    assert result.violations[0].metric_name == "mean_latency_seconds"


def test_drift_detector_handles_missing_keys_gracefully() -> None:
    baseline = {"faithfulness_rate": 0.96}
    candidate = {}  # Empty candidate dictionary
    result = evaluate_metric_drift(candidate_summary=candidate, baseline_summary=baseline)
    assert result.verdict == "NO-GO"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd app/backend && .venv\Scripts\python.exe -m pytest tests/evaluation/test_drift_detector.py -v`
Expected: `ModuleNotFoundError: No module named 'hospital_ai.evaluation.drift_detector'`

- [ ] **Step 3: Implement `drift_detector.py`**

Create `app/backend/src/hospital_ai/evaluation/drift_detector.py`:
```python
"""Pure comparison engine for AI evaluation hard quality gates and relative drift tolerances."""

from __future__ import annotations

from typing import Any

from hospital_ai.evaluation.contracts import (
    DriftGateResult,
    DriftViolation,
    MetricDriftComparison,
)

# Metric Configuration Schema:
# (metric_name, higher_is_better, hard_gate_min, hard_gate_max, relative_tolerance_drop_or_pct)
_METRIC_RULES: tuple[tuple[str, bool, float | None, float | None, float], ...] = (
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
    ("mean_latency_seconds", False, None, None, 0.20),  # Max +20.0% increase
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
        cand_val = float(candidate_summary.get(metric_name, 0.0) if metric_name in candidate_summary else -999.0)

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

        # 1. Check Hard Gate Min
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
        # 2. Check Hard Gate Max
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
        # 3. Check Relative Drift Tolerance
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
                            message=f"Latency spike failure: +{pct_increase*100:.1f}% exceeds max tolerance +{tolerance*100:.1f}%",
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
                            message=f"Relative drift failure: delta {delta:.4f} below tolerance threshold {tolerance:.4f}",
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd app/backend && .venv\Scripts\python.exe -m pytest tests/evaluation/test_drift_detector.py -v`
Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add app/backend/src/hospital_ai/evaluation/drift_detector.py app/backend/tests/evaluation/test_drift_detector.py
git commit -m "feat(eval): implement pure drift detector engine and hard gate evaluator"
```

---

### Task 3: CLI Entrypoint `verify_ai_regression.py` & GitHub Step Summary Renderer

**Files:**
- Create: `app/backend/scripts/verify_ai_regression.py`
- Modify: `app/backend/tests/evaluation/test_drift_detector.py`

**Interfaces:**
- Consumes: CLI args `--candidate`, `--baseline`, `--output-report`, `--github-summary`, `--strict`
- Produces: JSON report file, GitHub Actions Step Summary Markdown, CLI Exit code `0` (`GO`) or `1` (`NO-GO`)

- [ ] **Step 1: Write failing CLI integration tests in `test_drift_detector.py`**

Append to `app/backend/tests/evaluation/test_drift_detector.py`:
```python
import json
import subprocess
import sys
from pathlib import Path


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
    res = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True)
    assert res.returncode == 0
    assert report_file.exists()
    report = json.loads(report_file.read_text(encoding="utf-8"))
    assert report["verdict"] == "GO"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd app/backend && .venv\Scripts\python.exe -m pytest tests/evaluation/test_drift_detector.py::test_verify_ai_regression_cli_execution -v`
Expected: `FileNotFoundError` or script not found.

- [ ] **Step 3: Implement `verify_ai_regression.py`**

Create `app/backend/scripts/verify_ai_regression.py`:
```python
"""Executive CLI entrypoint for AI Baseline Regression & Drift Detector."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT / "src"))

from hospital_ai.evaluation.drift_detector import evaluate_metric_drift


def _format_markdown_summary(result_dict: dict) -> str:
    verdict = result_dict["verdict"]
    badge = "🟢 **GO / PASSED**" if verdict == "GO" else "🔴 **NO-GO / BLOCKED**"
    lines = [
        "# 🛡️ AI Baseline Regression & Drift Detector Report",
        "",
        f"**Verdict:** {badge}",
        f"**Candidate Commit:** `{result_dict.get('git_sha_candidate', 'unknown')}` | **Baseline Commit:** `{result_dict.get('git_sha_baseline', 'unknown')}`",
        f"**Evaluated Metrics:** {result_dict['total_metrics_evaluated']} | **Violations:** {result_dict['violation_count']}",
        "",
    ]
    if result_dict["violations"]:
        lines.append("### 🔴 Violations")
        for v in result_dict["violations"]:
            lines.append(f"- ❌ **`{v['metric_name']}`**: {v['message']}")
        lines.append("")

    lines.extend(
        [
            "### 📊 Full Metric Drift Comparison",
            "",
            "| Metric Name | Baseline | Candidate | Delta | Status |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ]
    )
    for c in result_dict["comparisons"]:
        st = "🟢 PASSED" if c["status"] == "passed" else f"🔴 FAILED ({c['status']})"
        lines.append(f"| `{c['metric_name']}` | {c['baseline_value']:.4f} | {c['candidate_value']:.4f} | {c['delta']:+.4f} | {st} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--baseline", type=Path, default=BACKEND_ROOT / "data" / "evaluation" / "baselines" / "baseline-release.json")
    parser.add_argument("--output-report", type=Path)
    parser.add_argument("--github-summary", action="store_true")
    parser.add_argument("--no-strict", dest="strict", action="store_false", default=True)

    args = parser.parse_args(argv)

    if not args.candidate.exists():
        print(f"Error: Candidate summary file not found at {args.candidate}", file=sys.stderr)
        return 2

    if not args.baseline.exists():
        print(f"Error: Baseline summary file not found at {args.baseline}", file=sys.stderr)
        return 2

    candidate_data = json.loads(args.candidate.read_text(encoding="utf-8"))
    baseline_data = json.loads(args.baseline.read_text(encoding="utf-8"))

    result = evaluate_metric_drift(
        candidate_summary=candidate_data,
        baseline_summary=baseline_data,
        git_sha_candidate=candidate_data.get("git_sha", "unknown"),
        git_sha_baseline=baseline_data.get("git_sha", "unknown"),
    )

    res_dict = result.model_dump()

    if args.output_report:
        args.output_report.parent.mkdir(parents=True, exist_ok=True)
        args.output_report.write_text(json.dumps(res_dict, indent=2), encoding="utf-8")

    md_summary = _format_markdown_summary(res_dict)
    print(md_summary)

    if args.github_summary and "GITHUB_STEP_SUMMARY" in os.environ:
        summary_path = Path(os.environ["GITHUB_STEP_SUMMARY"])
        with summary_path.open("a", encoding="utf-8") as f:
            f.write(md_summary)

    return 0 if (result.passed or not args.strict) else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd app/backend && .venv\Scripts\python.exe -m pytest tests/evaluation/test_drift_detector.py -v`
Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
git add app/backend/scripts/verify_ai_regression.py app/backend/tests/evaluation/test_drift_detector.py
git commit -m "feat(eval): add verify_ai_regression.py CLI and step summary renderer"
```

---

### Task 4: Official Baseline Lock & GitHub Actions CI Workflow Integration

**Files:**
- Create: `app/backend/data/evaluation/baselines/baseline-release.json`
- Modify: `.github/workflows/ci.yml:365-405`

**Interfaces:**
- Consumes: Official baseline JSON data
- Produces: Automated CI step verification on Pull Requests

- [ ] **Step 1: Save version-locked baseline snapshot `baseline-release.json`**

Create `app/backend/data/evaluation/baselines/baseline-release.json`:
```json
{
  "git_sha": "d5e1e20",
  "unauthorized_evidence_count": 0,
  "wrong_patient_citations_count": 0,
  "recall_at_5": 1.0,
  "mrr": 1.0,
  "graph_path_recall": 1.0,
  "faithfulness_rate": 0.9640,
  "answer_relevance_rate": 0.9480,
  "citation_precision": 0.9520,
  "decimal_misread_count": 0,
  "clinical_field_accuracy": 1.0,
  "mean_latency_seconds": 0.280
}
```

- [ ] **Step 2: Integrate `verify_ai_regression.py` step into `.github/workflows/ci.yml`**

Modify `.github/workflows/ci.yml` around line 398 in `rag-evaluation` job:
```yaml
      - name: Verify AI Baseline Regression & Drift Gate
        if: always()
        run: |
          if [ -f "evaluation-artifacts/deterministic/summary.json" ]; then
            python scripts/verify_ai_regression.py \
              --candidate evaluation-artifacts/deterministic/summary.json \
              --baseline data/evaluation/baselines/baseline-release.json \
              --output-report evaluation-artifacts/deterministic/drift_report.json \
              --github-summary
          else
            echo "Candidate evaluation-artifacts/deterministic/summary.json not found; skipping drift gate check."
          fi
```

- [ ] **Step 3: Run full pytest evaluation suite**

Run: `cd app/backend && .venv\Scripts\python.exe -m pytest tests/evaluation/ -v`
Expected: All tests pass 100%.

- [ ] **Step 4: Commit**

```bash
git add app/backend/data/evaluation/baselines/baseline-release.json .github/workflows/ci.yml
git commit -m "ci(eval): lock official release baseline snapshot and add drift detector CI gate"
```

---

## Self-Review & Verification Check

1. **Spec Coverage:** Verified all contracts, drift engine, CLI, Markdown step summary, and CI pipeline rules.
2. **Placeholder Scan:** Zero placeholders, complete executable code for every file.
3. **Type Consistency:** Clean Pydantic v2 `ConfigDict` schemas matching between `contracts.py` and `drift_detector.py`.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-24-ci-baseline-regression-drift-detector.md`.

Two execution options:
1. **Subagent-Driven (recommended)** - Fresh subagent per task, review between tasks, fast iteration using `/subagent-driven-development`.
2. **Inline Execution** - Execute tasks in this session using `executing-plans`.

Which approach would you like to use?
