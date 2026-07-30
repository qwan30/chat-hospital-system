# 45 Graph Benchmark Cases & Retrieval Ablation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 45 Graph RAG benchmark cases to achieve a 100% pass rate (45/45), integrate `graph` retrieval mode into the ablation harness alongside Vector, BM25, and Hybrid, measure Precision/Recall/Latency/Leakage, and output certified reports on branch `test/graph-rag-benchmark-45-v1`.

**Architecture:** Extend `run_ai_evaluation.py` CLI and `ProductRetrievalAdapter` to support `--retrieval-mode graph`, fix 2-hop relation edge traversal in `hospital_ai/services/graph_rag.py`, and execute evaluation suites to generate artifacts.

**Tech Stack:** Python 3.12, SQLAlchemy (Async SQLite/PostgreSQL), Pytest, Pydantic v2, Git.

## Global Constraints

- All implementation and execution must take place on branch `test/graph-rag-benchmark-45-v1`.
- Retain existing `synthetic-100-v2` dataset and `rag_benchmark_v2.jsonl` benchmark suite (no dataset expansion).
- Enforce Zero Patient-Scope Leakage (`retrieval_leakage = 0`).
- Enforce 100% Graph Node, Edge, and Path Recall (`= 1.0`).

---

### Task 1: Create Branch & Environment Verification

**Files:**
- Modify: Git Branch context

**Interfaces:**
- Consumes: Current git repository state
- Produces: Active git branch `test/graph-rag-benchmark-45-v1`

- [ ] **Step 1: Create and checkout branch `test/graph-rag-benchmark-45-v1`**

```bash
git checkout -b test/graph-rag-benchmark-45-v1
```

- [ ] **Step 2: Verify existing evaluation tests pass**

```bash
cd app/backend && python -m pytest tests/evaluation/ -v
```
Expected: All existing evaluation unit tests pass.

- [ ] **Step 3: Commit branch setup**

```bash
git status
```

---

### Task 2: Fix Graph RAG Multi-Hop Path Traversal

**Files:**
- Modify: `app/backend/src/hospital_ai/services/graph_rag.py:70-130`
- Modify: `app/backend/src/hospital_ai/evaluation/product_graph_adapter.py:80-115`
- Test: `app/backend/tests/evaluation/test_evaluation_runner.py`

**Interfaces:**
- Consumes: `find_related_entities(session, entity_names, patient_id)`
- Produces: Unbroken multi-hop graph path tuples with exact case-insensitive normalized relation strings

- [ ] **Step 1: Write failing unit test reproducing the 2-hop path disconnection**

```python
# Add to app/backend/tests/evaluation/test_evaluation_runner.py
@pytest.mark.asyncio
async def test_graph_multi_hop_path_normalization(tmp_path: Path) -> None:
    # Test that multi-hop relations matching required_edges return complete path_ids
    ...
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd app/backend && python -m pytest tests/evaluation/test_evaluation_runner.py -k test_graph_multi_hop_path_normalization -v
```
Expected: FAIL (path matching mismatch or edge disconnection).

- [ ] **Step 3: Fix 2-hop traversal logic and relation string formatting**

In `app/backend/src/hospital_ai/services/graph_rag.py`, ensure `find_related_entities` enforces `patient_id` on both initial entity lookup and relation target lookup. In `app/backend/src/hospital_ai/evaluation/product_graph_adapter.py`, normalize edge IDs to lowercase `source_name|relation_type|target_name`.

- [ ] **Step 4: Verify test passes**

```bash
cd app/backend && python -m pytest tests/evaluation/test_evaluation_runner.py -k test_graph_multi_hop_path_normalization -v
```
Expected: PASS.

- [ ] **Step 5: Commit changes**

```bash
git add app/backend/src/hospital_ai/services/graph_rag.py app/backend/src/hospital_ai/evaluation/product_graph_adapter.py app/backend/tests/evaluation/test_evaluation_runner.py
git commit -m "fix(graph-rag): resolve multi-hop path traversal edge normalization"
```

---

### Task 3: Integrate `graph` Mode into Retrieval Ablation Harness

**Files:**
- Modify: `app/backend/scripts/run_ai_evaluation.py:86-90`
- Modify: `app/backend/src/hospital_ai/evaluation/product_retrieval_adapter.py:30-80`
- Test: `app/backend/tests/evaluation/test_product_retrieval_adapter.py`

**Interfaces:**
- Consumes: `ProductRetrievalAdapter(source_root, retrieval_mode="graph")`
- Produces: Retrieval observations containing combined graph-expanded and hybrid retrieved chunks

- [ ] **Step 1: Write failing unit test for `retrieval_mode="graph"`**

```python
# Add to app/backend/tests/evaluation/test_product_retrieval_adapter.py
@pytest.mark.asyncio
async def test_product_retrieval_adapter_supports_graph_mode(tmp_path: Path) -> None:
    adapter = ProductRetrievalAdapter(tmp_path, retrieval_mode="graph")
    assert adapter._retrieval_mode == "graph"
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd app/backend && python -m pytest tests/evaluation/test_product_retrieval_adapter.py -k test_product_retrieval_adapter_supports_graph_mode -v
```
Expected: FAIL (`ValueError: retrieval_mode must be vector|bm25|hybrid`).

- [ ] **Step 3: Update `run_ai_evaluation.py` CLI and `ProductRetrievalAdapter`**

In `run_ai_evaluation.py`:
Change `choices=("vector", "bm25", "hybrid")` to `choices=("vector", "bm25", "hybrid", "graph")`.

In `ProductRetrievalAdapter`:
Allow `retrieval_mode="graph"` and when `retrieval_mode == "graph"`, execute entity extraction and graph expansion, appending unique graph-discovered chunk IDs to the retrieved evidence.

- [ ] **Step 4: Verify unit test passes**

```bash
cd app/backend && python -m pytest tests/evaluation/test_product_retrieval_adapter.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit changes**

```bash
git add app/backend/scripts/run_ai_evaluation.py app/backend/src/hospital_ai/evaluation/product_retrieval_adapter.py app/backend/tests/evaluation/test_product_retrieval_adapter.py
git commit -m "feat(eval): add graph mode to retrieval ablation harness"
```

---

### Task 4: Execute 45 Graph Benchmark Suite & Generate Artifacts

**Files:**
- Create: `docs/09-testing/graph-rag-benchmark-45-and-ablation-20260723.md`
- Create: `app/backend/evaluation-artifacts/graph-45/summary.md`
- Create: `app/backend/evaluation-artifacts/graph-45/run.json`

**Interfaces:**
- Consumes: `python scripts/run_ai_evaluation.py --suite release --lane deterministic --components graph`
- Produces: Verified 45/45 Graph evaluation report with Node/Edge/Path recall, Latency p50/p95, and zero leakage verification

- [ ] **Step 1: Execute 45 Graph Benchmark Release Suite**

```bash
cd app/backend && python scripts/run_ai_evaluation.py --suite release --lane deterministic --components graph --output-dir evaluation-artifacts/graph-45
```
Expected: Output `AI evaluation passed: .../evaluation-artifacts/graph-45`. All 45/45 cases pass.

- [ ] **Step 2: Run Unified Retrieval Ablation for Vector, BM25, Hybrid, and Graph**

```bash
cd app/backend && python scripts/run_ai_evaluation.py --suite smoke --lane deterministic --components retrieval --retrieval-mode vector --output-dir evaluation-artifacts/ablation-vector
cd app/backend && python scripts/run_ai_evaluation.py --suite smoke --lane deterministic --components retrieval --retrieval-mode bm25 --output-dir evaluation-artifacts/ablation-bm25
cd app/backend && python scripts/run_ai_evaluation.py --suite smoke --lane deterministic --components retrieval --retrieval-mode hybrid --output-dir evaluation-artifacts/ablation-hybrid
cd app/backend && python scripts/run_ai_evaluation.py --suite smoke --lane deterministic --components retrieval --retrieval-mode graph --output-dir evaluation-artifacts/ablation-graph
```
Expected: Artifact summaries generated for all 4 retrieval modes.

- [ ] **Step 3: Write Markdown Evaluation Report**

Write `docs/09-testing/graph-rag-benchmark-45-and-ablation-20260723.md` summarizing:
- 45/45 Graph Cases Pass Rate (100% Node, Edge, Path Recall).
- Precision, Recall@5, MRR, nDCG@5, Latency, and Zero Leakage table comparing Vector vs BM25 vs Hybrid vs Graph.

- [ ] **Step 4: Verify and commit report**

```bash
git add docs/09-testing/graph-rag-benchmark-45-and-ablation-20260723.md app/backend/evaluation-artifacts/
git commit -m "docs(eval): publish 45 graph benchmark and retrieval ablation report"
```
