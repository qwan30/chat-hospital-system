# Design Spec: Automated CI Baseline Regression & Drift Detector

**Date:** July 24, 2026  
**Status:** Approved  
**Author:** AI Engineering & QA Team  
**Target Branch:** `feat/ci-baseline-regression-drift-detector`  
**Related Requirements:** [`docs/09-testing/test-plan.md`](file:///d:/projects/chatbot-hospital-system/docs/09-testing/test-plan.md), [`docs/superpowers/specs/2026-07-24-ocr-evaluation-harness-design.md`](file:///d:/projects/chatbot-hospital-system/docs/superpowers/specs/2026-07-24-ocr-evaluation-harness-design.md)

---

## 1. Executive Summary & Problem Statement

### 1.1 Context & Background
The AI-Powered Hospital Knowledge Assistant relies on a 5-component evaluation suite:
1. **Corpus Inventory:** 100 gold text pages (`CorpusManifestV2`).
2. **Retrieval Ablations:** BM25, Dense Vector, and Hybrid modes.
3. **Graph RAG:** Multi-hop relation path traversal & entity linking.
4. **Chat & LLM Judge:** PHI Redactor, Citation Parser, LLM Judge (Faithfulness & Relevance), Safe Refusals.
5. **OCR Evaluation Harness:** 10 image degradation variants, Clinical Field Exactness, and Decimal Misread Risk detection.

Currently, evaluation benchmarks run offline via `scripts/run_ai_evaluation.py` or manually via GitHub Actions `workflow_dispatch`.

### 1.2 The Problem
In AI/LLM and RAG systems, standard unit tests (`pytest`) pass even when prompt modifications, chunking changes, or model version updates introduce **Silent AI Quality Regressions**:
- Faithfulness drops from 96.4% to 70.0% without syntax or runtime errors.
- Citation precision degrades, causing hallucinated medical citations.
- Patient PHI leakage occurs across multi-tenant sessions.
- OCR decimal misreads (`1.0 mg` -> `10 mg`) slip into production without triggering code failures.

### 1.3 Proposed Solution
Implement **Automated CI Baseline Regression & Drift Detector**:
1. **Baseline Store:** Locked, version-controlled baseline JSON snapshots stored in `app/backend/data/evaluation/baselines/`.
2. **Drift Detector Module (`hospital_ai.evaluation.drift_detector`):** Programmatic metric comparator evaluating candidates against baselines using both **Hard Quality Gates** (absolute thresholds) and **Relative Drift Tolerances** (percentage degradation limits).
3. **CLI Verification Entrypoint (`app/backend/scripts/verify_ai_regression.py`):** Executive CLI tool returning exit code `0` on `GO` and `1` on `NO-GO` / `BLOCKED`.
4. **GitHub Actions Integration (`.github/workflows/ci.yml`):** Automated PR gate step executing regression verification on every Pull Request, publishing a rich GitHub Step Summary report and blocking PR merges on quality regressions.

---

## 2. Core Architecture & Data Contracts

```
+-----------------------------------------------------------------------------------+
|                            GitHub Actions PR Pipeline                             |
|              (Triggered on git push / pull_request to main/master)                |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                        1. Run Deterministic AI Evaluation                         |
|      (python scripts/run_ai_evaluation.py --suite release --lane deterministic)   |
|         ---> Generates candidate_summary.json & candidate_metrics.json            |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                       2. Execute Drift Detector Verification                      |
|       (python scripts/verify_ai_regression.py --candidate candidate_summary.json)  |
+------------------------------------------+----------------------------------------+
                                           |
                    +----------------------+----------------------+
                    |                                             |
                    v                                             v
+---------------------------------------+     +---------------------------------------+
|        Hard Quality Gates             |     |      Relative Drift Tolerances        |
| - Zero PHI Leakage (0 Chunks)         |     | - Faithfulness drop <= 2.0%           |
| - Recall@5 >= 0.90                    |     | - Relevance drop <= 2.0%               |
| - Faithfulness >= 90.0%               |     | - Retrieval Recall drop <= 0.0%       |
| - OCR Decimal Misread = 0             |     | - Latency increase <= 20.0%           |
+---------------------------------------+     +---------------------------------------+
                    |                                             |
                    +----------------------+----------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                     3. Output Drift Report & GitHub Summary                       |
|  - Writes drift_report.json                                                       |
|  - Appends Markdown table to $GITHUB_STEP_SUMMARY                                 |
|  - Exit 0 (GO / PASS)  |  Exit 1 (NO-GO / BLOCKED -> Fails PR CI Step)           |
+-----------------------------------------------------------------------------------+
```

---

## 3. Data Contracts & Type Schemas

New data models added to `app/backend/src/hospital_ai/evaluation/contracts.py`:

```python
from typing import Literal
from pydantic import BaseModel, Field


class MetricDriftComparison(BaseModel):
    metric_name: str
    baseline_value: float
    candidate_value: float
    delta: float
    tolerance: float
    hard_gate_min: float | None = None
    hard_gate_max: float | None = None
    status: Literal["passed", "failed_drift", "failed_hard_gate"]

    class Config:
        frozen = True


class DriftViolation(BaseModel):
    metric_name: str
    violation_type: Literal["hard_gate", "relative_drift"]
    baseline_value: float
    candidate_value: float
    message: str

    class Config:
        frozen = True


class DriftGateResult(BaseModel):
    verdict: Literal["GO", "NO-GO"]
    passed: bool
    total_metrics_evaluated: int
    violation_count: int
    violations: tuple[DriftViolation, ...]
    comparisons: tuple[MetricDriftComparison, ...]
    git_sha_baseline: str
    git_sha_candidate: str

    class Config:
        frozen = True
```

---

## 4. Evaluation Metrics & Gate Threshold Rules

### 4.1 Hard Quality Gates (Absolute Thresholds)
Every candidate evaluation run MUST pass the following non-negotiable hard gates regardless of baseline:

| Component | Metric Name | Target / Boundary | Failure Action |
|---|---|---|---|
| **Safety** | `unauthorized_evidence_count` | **Must be 0** | **BLOCKED (Critical PHI Violation)** |
| **Safety** | `wrong_patient_citations_count` | **Must be 0** | **BLOCKED (Patient Misattribution)** |
| **Retrieval** | `recall_at_5` | **$\ge 0.9000$** | **BLOCKED (Recall Failure)** |
| **Retrieval** | `mrr` | **$\ge 0.8500$** | **BLOCKED (Ranking Failure)** |
| **Graph RAG** | `graph_path_recall` | **$= 1.0000$** | **BLOCKED (Graph Traversal Failure)** |
| **Chat** | `faithfulness_rate` | **$\ge 0.9000$ (90.0%)** | **BLOCKED (Hallucination Risk)** |
| **Chat** | `answer_relevance_rate` | **$\ge 0.9000$ (90.0%)** | **BLOCKED (Irrelevant Answer)** |
| **Chat** | `citation_precision` | **$\ge 0.9500$ (95.0%)** | **BLOCKED (Citation Error)** |
| **OCR** | `decimal_misread_count` | **Must be 0** | **BLOCKED (Medical Dosage Risk)** |
| **OCR** | `clinical_field_accuracy` | **$\ge 0.9500$ (95.0%)** | **BLOCKED (Field Extraction Error)** |

### 4.2 Relative Drift Tolerances (Degradation Limits vs Baseline)
The candidate run is compared against `baseline-release.json`:

$$\Delta = \text{Candidate Value} - \text{Baseline Value}$$

| Metric | Max Allowed Negative Drift ($\Delta$) | Rationale |
|---|---|---|
| `faithfulness_rate` | **$-0.0200$ ($-2.0\%$)** | Small prompt variances allowed, major drop blocked |
| `answer_relevance_rate` | **$-0.0200$ ($-2.0\%$)** | Protects user query alignment |
| `recall_at_5` | **$-0.0000$ ($0.0\%$)** | Zero degradation allowed for document retrieval recall |
| `mrr` | **$-0.0100$ ($-1.0\%$)** | Minimal ranking position shift allowed |
| `citation_precision` | **$-0.0100$ ($-1.0\%$)** | Strict citation integrity enforcement |
| `mean_latency_seconds` | **$+20.0\%$ increase** | Latency regression protection |

---

## 5. Script & CLI Specification

### 5.1 CLI Tool: `app/backend/scripts/verify_ai_regression.py`

#### Arguments:
- `--candidate` (required): Path to candidate `summary.json` generated by `run_ai_evaluation.py`.
- `--baseline` (optional): Path to baseline JSON file (default: `app/backend/data/evaluation/baselines/baseline-release.json`).
- `--output-report` (optional): Path to write machine-readable `drift_report.json`.
- `--github-summary` (optional, boolean): If true, appends GitHub Actions Markdown step summary to `$GITHUB_STEP_SUMMARY`.
- `--strict` (optional, boolean): Exit code `1` on any `NO-GO` verdict (default: `True`).

#### Example Usage:
```bash
python scripts/verify_ai_regression.py \
  --candidate evaluation-artifacts/deterministic/summary.json \
  --baseline data/evaluation/baselines/baseline-release.json \
  --output-report evaluation-artifacts/deterministic/drift_report.json \
  --github-summary
```

### 5.2 Terminal & GitHub Step Summary Markdown Output Format

```markdown
# 🛡️ AI Baseline Regression & Drift Detector Report

**Verdict:** 🔴 **NO-GO / BLOCKED**  
**Candidate Commit:** `d7b198f` | **Baseline Commit:** `528541f`  
**Evaluated Metrics:** 12 | **Violations:** 2  

### 🔴 Violations
- ❌ **`faithfulness_rate`**: Candidate `0.8750` vs Baseline `0.9640` (Delta `-0.0890` exceeds max tolerance `-0.0200`)
- ❌ **`unauthorized_evidence_count`**: Candidate `1` vs Hard Gate `0` (Critical PHI Leakage Violation)

### 📊 Full Metric Drift Comparison
| Metric Name | Baseline | Candidate | Delta | Status |
| :--- | :---: | :---: | :---: | :---: |
| `faithfulness_rate` | 0.9640 | 0.8750 | -0.0890 | 🔴 FAILED (Drift) |
| `answer_relevance_rate` | 0.9480 | 0.9500 | +0.0020 | 🟢 PASSED |
| `recall_at_5` | 1.0000 | 1.0000 | 0.0000 | 🟢 PASSED |
| `unauthorized_evidence_count` | 0 | 1 | +1 | 🔴 FAILED (Hard Gate) |
| `ocr_decimal_misread_count` | 0 | 0 | 0 | 🟢 PASSED |
```

---

## 6. GitHub Actions Workflow Integration (`.github/workflows/ci.yml`)

Add a dedicated quality gate step in `.github/workflows/ci.yml` under `rag-evaluation` job:

```yaml
      - name: Run deterministic AI evaluation
        run: |
          python scripts/run_ai_evaluation.py \
            --suite "$AI_EVAL_SUITE" \
            --lane deterministic \
            --components corpus,ocr,retrieval,graph,chat \
            --output-dir evaluation-artifacts/deterministic

      - name: Verify AI Baseline Regression & Drift Gate
        if: always()
        run: |
          python scripts/verify_ai_regression.py \
            --candidate evaluation-artifacts/deterministic/summary.json \
            --baseline data/evaluation/baselines/baseline-release.json \
            --output-report evaluation-artifacts/deterministic/drift_report.json \
            --github-summary
```

---

## 7. Verification Plan & Test Suite Strategy

### 7.1 Automated Unit & Integration Tests (`tests/evaluation/test_drift_detector.py`)
1. **`test_drift_detector_pass_on_identical_candidate()`:** Verify `GO` verdict when candidate metrics match or exceed baseline.
2. **`test_drift_detector_fails_on_faithfulness_drop()`:** Verify `NO-GO` verdict when candidate faithfulness drops > 2.0%.
3. **`test_drift_detector_fails_on_phi_leakage()`:** Verify instant hard-gate failure when `unauthorized_evidence_count > 0`.
4. **`test_drift_detector_fails_on_ocr_decimal_misread()`:** Verify instant hard-gate failure when `decimal_misread_count > 0`.
5. **`test_verify_ai_regression_cli_exit_codes()`:** Verify CLI exit code `0` for `GO` and exit code `1` for `NO-GO`.

### 7.2 Manual & CI Verification
- Execute `python scripts/verify_ai_regression.py --candidate ...` on local mock files.
- Verify GitHub Actions workflow execution on PR branch.

---

## 8. Summary of Files To Be Created / Modified

| Action | File Path | Purpose |
|---|---|---|
| **[MODIFY]** | [`app/backend/src/hospital_ai/evaluation/contracts.py`](file:///d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/evaluation/contracts.py) | Add `DriftGateResult`, `MetricDriftComparison`, `DriftViolation` Pydantic models. |
| **[NEW]** | [`app/backend/src/hospital_ai/evaluation/drift_detector.py`](file:///d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/evaluation/drift_detector.py) | Pure comparison engine for hard gates and relative drift tolerances. |
| **[NEW]** | [`app/backend/scripts/verify_ai_regression.py`](file:///d:/projects/chatbot-hospital-system/app/backend/scripts/verify_ai_regression.py) | Executive CLI entrypoint for local and CI drift verification. |
| **[NEW]** | [`app/backend/data/evaluation/baselines/baseline-release.json`](file:///d:/projects/chatbot-hospital-system/app/backend/data/evaluation/baselines/baseline-release.json) | Version-locked official baseline dataset metrics snapshot. |
| **[NEW]** | [`app/backend/tests/evaluation/test_drift_detector.py`](file:///d:/projects/chatbot-hospital-system/app/backend/tests/evaluation/test_drift_detector.py) | Unit and integration test suite for drift detection and CLI gates. |
| **[MODIFY]** | [`.github/workflows/ci.yml`](file:///d:/projects/chatbot-hospital-system/.github/workflows/ci.yml) | Integrate `verify_ai_regression.py` step into GitHub Actions PR pipeline. |
