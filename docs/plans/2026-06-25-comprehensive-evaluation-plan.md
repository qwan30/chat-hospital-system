# Comprehensive Evaluation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Establish a comprehensive evaluation suite for the chatbot-hospital-system, measuring RAG accuracy and UAT flows.

**Architecture:** Extend current testing with a statistical evaluation script for retrieval/citations, expand synthetic RAG test cases, and create an E2E Playwright UAT test.

**Tech Stack:** Python (pytest, sqlalchemy, slowapi), TypeScript (Playwright, TanStack Start).

---

### Task 1: Fix Existing Test Failures

**Files:**
- Modify: [test_audit_2026_05.py](file:///d:/projects/chatbot-hospital-system/app/backend/tests/test_audit_2026_05.py#L26-L39)
- Modify: [graph_rag.py](file:///d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/graph_rag.py#L146-L202)
- Test: `pytest tests/test_audit_2026_05.py -k test_token_user_map_refuses_default_in_production` and `pytest tests/test_graph_rag_integration.py -k test_extract_mentioned_with_drug_condition`

**Step 1: Write the failing tests**
Both tests already exist and are failing in the baseline suite.

**Step 2: Run tests to verify they fail**
Run: `python -m pytest tests/test_audit_2026_05.py -k test_token_user_map_refuses_default_in_production`
Expected: FAIL

Run: `python -m pytest tests/test_graph_rag_integration.py -k test_extract_mentioned_with_drug_condition`
Expected: FAIL

**Step 3: Write minimal implementation**
- In `test_audit_2026_05.py`, override `dev_bearer_tokens` to its default value when instantiating `Settings(environment="production")` in `test_token_user_map_refuses_default_in_production`.
- In `graph_rag.py`, add sentence-level co-occurrence checking in `extract_relations` to extract generic `mentioned_with` relations (with weight 0.3) for any entities appearing in the same sentence.

**Step 4: Run tests to verify they pass**
Run: `python -m pytest tests/`
Expected: PASS all 294 tests.

**Step 5: Commit**
```bash
git add app/backend/tests/test_audit_2026_05.py app/backend/src/hospital_ai/services/graph_rag.py
git commit -m "fix: resolve production token and graph relation extraction test failures"
```

---

### Task 2: Create Retrieval and Citation Evaluation Script

**Files:**
- Create: [eval_retrieval_citation.py](file:///d:/projects/chatbot-hospital-system/app/backend/scripts/eval_retrieval_citation.py)
- Test: `python scripts/eval_retrieval_citation.py`

**Step 1: Write the script**
Create the new file `app/backend/scripts/eval_retrieval_citation.py` which:
- Defines 100+ clinical queries with annotated relevant chunk IDs.
- Measures Recall@K, MRR, Permission Leakage Rate, and Permission False Negatives.
- Tests citation validator with 150 cases (50 correct, 50 hallucinated, 50 missing) to compute Precision, Recall, Hallucination Block Rate, and Over-citation Rate.
- Writes output to `history/portfolio-hardening-2026-06/retrieval-citation-report.json`.

**Step 2: Run the script to verify**
Run: `python scripts/eval_retrieval_citation.py`
Expected: Outputs a clean console statistical table and writes the JSON report.

**Step 3: Commit**
```bash
git add app/backend/scripts/eval_retrieval_citation.py
git commit -m "feat: add retrieval and citation validation statistical evaluation script"
```

---

### Task 3: Expand Synthetic RAG Evaluation Suite

**Files:**
- Modify: [run_rag_eval.py](file:///d:/projects/chatbot-hospital-system/app/backend/scripts/run_rag_eval.py)
- Test: `python scripts/run_rag_eval.py`

**Step 1: Write the expansion**
Modify `app/backend/scripts/run_rag_eval.py` to:
- Add 24 additional synthetic scenarios (totaling 30) spanning factual recall, multi-hop reasoning, permission boundary, negative/hallucination, and HMS context.
- Assert that every RAG response correctly cites source evidence and provides useful facts.

**Step 2: Run the evaluation**
Run: `python scripts/run_rag_eval.py`
Expected: PASS all 30 scenarios, writing report to `history/portfolio-hardening-2026-06/rag-eval-report.md`.

**Step 3: Commit**
```bash
git add app/backend/scripts/run_rag_eval.py
git commit -m "feat: expand synthetic RAG eval suite to 30 scenarios"
```

---

### Task 4: Implement Playwright E2E UAT Verification Flow

**Files:**
- Create: [eval-uat.spec.ts](file:///d:/projects/chatbot-hospital-system/app/frontend/e2e/flows/eval-uat.spec.ts)
- Test: `bun run test:e2e e2e/flows/eval-uat.spec.ts`

**Step 1: Write the test**
Create `app/frontend/e2e/flows/eval-uat.spec.ts` incorporating the UAT checklists:
- Clinician summary verification (view details, click citation chip).
- Justification override workflow (access denied -> submit justification -> access granted).
- Pharmacist medication safety (view meds & check drug-allergy / drug-drug warnings).

**Step 2: Run E2E tests**
Run: `bun run test:e2e e2e/flows/eval-uat.spec.ts`
Expected: PASS all UAT flows.

**Step 3: Commit**
```bash
git add app/frontend/e2e/flows/eval-uat.spec.ts
git commit -m "test: implement E2E UAT verification flows in Playwright"
```

---

### Task 5: Baseline Reporting and Documentation

**Files:**
- Create: [evaluation-baseline.md](file:///d:/projects/chatbot-hospital-system/docs/09-testing/evaluation-baseline.md)

**Step 1: Create baseline report**
Create `docs/09-testing/evaluation-baseline.md` with:
- Summary of evaluation metrics (Recall@K, MRR, Leakage, Precision, UAT status).
- Analysis of findings, accuracy statistics, and recommended updates.

**Step 2: Commit**
```bash
git add docs/09-testing/evaluation-baseline.md
git commit -m "docs: write evaluation baseline report"
```
