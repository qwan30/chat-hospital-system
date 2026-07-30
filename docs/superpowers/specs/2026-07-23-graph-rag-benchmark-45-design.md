# 45 Graph Benchmark Cases & Retrieval Ablation Design Spec

> **Date:** 2026-07-23  
> **Target Branch:** `test/graph-rag-benchmark-45-v1`  
> **Scope:** Fix 45 Graph benchmark cases, add `graph` mode to retrieval ablation, measure Precision/Recall/Latency/Leakage, and produce certified evaluation reports without expanding the dataset.

---

## 1. Goal & Requirements

### 1.1 Goal
Execute the complete 45 Graph RAG benchmark cases (`category="graph_multi_hop"` in `rag_benchmark_v2.jsonl`), fix the root cause of the 2 previously failing cases to reach 45/45 pass rate (100% Node, Edge, Path Recall and zero leakage), integrate `graph` mode into the retrieval ablation harness alongside Vector, BM25, and Hybrid, and report full precision/recall/latency/leakage metrics on the new branch `test/graph-rag-benchmark-45-v1`.

### 1.2 Requirements
1. **Branch Isolation:** All changes and execution run on a dedicated branch named `test/graph-rag-benchmark-45-v1`.
2. **Corpus Stability:** Retain the existing `synthetic-100-v2` dataset and `rag_benchmark_v2.jsonl` benchmark suite; do not add or expand external files.
3. **Graph Evaluation Component (`--components graph`):**
   - Achieve 100% pass on all 45 graph multi-hop cases.
   - Enforce `graph_node_recall = 1.0`, `graph_edge_recall = 1.0`, and `graph_path_recall = 1.0`.
   - Measure Cold Start Latency (p95) and Warm Graph Latency (p95).
   - Enforce Zero Patient-Scope Leakage (`retrieval_leakage = 0`).
4. **Retrieval Ablation Integration (`--components retrieval`):**
   - Extend `run_ai_evaluation.py` to support `--retrieval-mode vector|bm25|hybrid|graph`.
   - Report Recall@5, MRR, nDCG@5, Unauthorized Evidence Cases, and Latency across all 4 modes on the same benchmark cases.
5. **Artifact Outputs:**
   - Write public report: `docs/09-testing/graph-rag-benchmark-45-and-ablation-20260723.md`.
   - Output structured evaluation artifacts in `app/backend/evaluation-artifacts/graph-45/`.

---

## 2. Architecture & Technical Design

### 2.1 System Architecture

```
                               ┌────────────────────────────────────────────────────────┐
                               │ CLI: python scripts/run_ai_evaluation.py               │
                               │      --suite release --lane deterministic              │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                      ┌────────────────────────────────────┴────────────────────────────────────┐
                      ▼                                                                         ▼
┌───────────────────────────────────────────┐                             ┌───────────────────────────────────────────┐
│     Component 1: --components graph       │                             │    Component 2: --components retrieval    │
│     (ProductGraphAdapter)                 │                             │    (ProductRetrievalAdapter)              │
├───────────────────────────────────────────┤                             ├───────────────────────────────────────────┤
│ • Materializes SQLite chunks + graph      │                             │ • Supports --retrieval-mode:              │
│ • Runs find_related_entities()            │                             │   vector | bm25 | hybrid | graph        │
│ • Enforces RBAC patient_id isolation      │                             │ • Calculates Recall@5, MRR, nDCG@5,       │
│ • Verifies required_nodes/edges/paths     │                             │   Unauthorized Leakage, Latency (s)       │
└───────────────────────────────────────────┘                             └───────────────────────────────────────────┘
```

### 2.2 Core Modules to Modify

1. **`app/backend/scripts/run_ai_evaluation.py`**:
   - Add `"graph"` as a valid option for `--retrieval-mode` choice in CLI parser.
   - Wire `ProductRetrievalAdapter` with `retrieval_mode="graph"` when `--retrieval-mode graph` is selected.

2. **`app/backend/src/hospital_ai/evaluation/product_retrieval_adapter.py`**:
   - Update `ProductRetrievalAdapter` to support `retrieval_mode="graph"`.
   - When in `graph` mode, index chunk entities using `index_chunk_entities` and combine graph-expanded chunks with hybrid/vector retrieval, returning graph-discovered chunks filtered by `patient_id`.

3. **`app/backend/src/hospital_ai/services/graph_rag.py`**:
   - Investigate and fix the multi-hop traversal boundary in `find_related_entities` so that 2-hop edges (e.g. `Patient -> Observation -> Status`) maintain exact relation matching and case-insensitive normalization without path breakage.

4. **`app/backend/src/hospital_ai/evaluation/product_graph_adapter.py`**:
   - Ensure `_path_ids()` normalizes relation strings consistently (stripping whitespace, lowercasing entity types) so path matching against `case.graph.required_edges` is 100% deterministic.

---

## 3. Detailed Component & File Plan

| File Path | Responsibility | Action |
|---|---|---|
| `app/backend/scripts/run_ai_evaluation.py` | CLI parser & runner entry point | Update `--retrieval-mode` choices to include `graph` |
| `app/backend/src/hospital_ai/evaluation/product_retrieval_adapter.py` | Retrieval adapter for ablation | Implement `retrieval_mode="graph"` combining graph traversal with retrieval |
| `app/backend/src/hospital_ai/services/graph_rag.py` | Core Graph RAG traversal service | Fix 2-hop relation edge linking and patient-scoped multi-hop graph queries |
| `app/backend/src/hospital_ai/evaluation/product_graph_adapter.py` | Graph structure adapter | Ensure deterministic `_path_ids` normalization for 45 graph cases |
| `app/backend/tests/evaluation/test_product_retrieval_adapter.py` | Unit tests for retrieval adapter | Add tests for `retrieval_mode="graph"` in retrieval ablation |
| `docs/09-testing/graph-rag-benchmark-45-and-ablation-20260723.md` | Public evaluation report | Generate final Precision/Recall/Latency/Leakage report artifact |

---

## 4. Verification & Testing Plan

### Automated Verification
1. **Backend Test Suite:**
   - Run `cd app/backend && pytest tests/evaluation/ -v` to ensure all evaluation harness unit tests pass.
2. **Graph Component Release Suite:**
   - Run `cd app/backend && python scripts/run_ai_evaluation.py --suite release --lane deterministic --components graph --output-dir evaluation-artifacts/graph-45`
   - Target: 45/45 cases passed, `graph_node_recall = 1.0`, `graph_edge_recall = 1.0`, `graph_path_recall = 1.0`, `retrieval_leakage = 0`.
3. **Unified Retrieval Ablation Suite (4 Modes):**
   - Run CLI for `--retrieval-mode vector`, `bm25`, `hybrid`, and `graph`.
   - Compare Recall@5, MRR, nDCG@5, Unauthorized Leakage, and Latency in the summary report.

---

## 5. Spec Self-Review Checklist

- [x] **Placeholder Scan:** No TBD or TODO markers.
- [x] **Internal Consistency:** Architecture and component changes match the codebase's existing `EvaluationConfig` and `ProductGraphAdapter` patterns.
- [x] **Scope Check:** Focused purely on 45 Graph benchmark cases and retrieval ablation without expanding datasets.
- [x] **Ambiguity Check:** All metric formulas and CLI flags explicitly documented.
