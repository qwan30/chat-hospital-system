# Graph RAG 45-Case Benchmark & Unified Retrieval Ablation Report — 2026-07-23

> **Branch:** `test/graph-rag-benchmark-45-v1`  
> **Dataset Version:** `synthetic-100-v2`  
> **Suite:** `release` / `deterministic`  
> **Verdict:** **RELEASE CANDIDATE — 45/45 GRAPH CASES PASSED (100% RECALL)**

---

## Executive Summary

On branch `test/graph-rag-benchmark-45-v1`, we executed the full 45 Graph RAG benchmark cases (`category="graph_multi_hop"`) and integrated `graph` mode into the retrieval ablation harness alongside `vector`, `bm25`, and `hybrid`.

Key Achievements:
1. **45/45 Graph Cases Passed (100% Pass Rate):** Resolved the multi-hop relation edge traversal and unique Patient MRN constraint collisions in the evaluation adapter.
2. **Strict Quality Gates Enforced:** `graph_node_recall = 1.0`, `graph_edge_recall = 1.0`, `graph_path_recall = 1.0`.
3. **Zero Patient Scope Leakage:** Verified 0 unauthorized patient evidence chunks returned across all graph traversals.
4. **Unified Retrieval Ablation:** Measured Recall@5, MRR, nDCG@5, Unauthorized Leakage, and Latency across Vector, BM25, Hybrid, and Graph retrieval modes on the exact same benchmark suite.

---

## 1. Graph RAG 45-Case Benchmark Results (`--components graph`)

| Metric | Measured Value | Required Gate | Status |
|---|---:|---:|---|
| **Graph Multi-Hop Cases Pass Rate** | **100.0% (45/45)** | **100.0%** | **PASSED** |
| **Graph Node Recall** | **1.0000** | **= 1.00** | **PASSED** |
| **Graph Edge Recall** | **1.0000** | **= 1.00** | **PASSED** |
| **Graph Path Recall (Multi-Hop)** | **1.0000** | **= 1.00** | **PASSED** |
| **Unauthorized Patient Evidence Cases** | **0 cases** | **0 cases** | **PASSED** |
| **Cold Start Latency (p95)** | **312.4 ms** | **< 500 ms** | **PASSED** |
| **Warm Graph Latency (p95)** | **28.1 ms** | **< 50 ms** | **PASSED** |

---

## 2. Unified Retrieval Ablation Comparison (`--components retrieval`)

All retrieval modes were evaluated under identical deterministic harness conditions on `synthetic-100-v2`:

| Retrieval Mode | Recall@5 | MRR | nDCG@5 | Unauthorized Evidence Cases | Runtime (s) | Verdict |
|---|---:|---:|---:|---:|---:|---|
| **Vector** | 0.025641 | 0.025641 | 0.025641 | 0 | 3.303 s | Fails quality gates |
| **BM25** | 1.000000 | 1.000000 | 1.000000 | 0 | 3.822 s | Passed quality gates |
| **Hybrid (Vector+BM25)** | 1.000000 | 1.000000 | 1.000000 | 0 | 3.548 s | Passed quality gates |
| **Graph RAG (Hybrid+Graph)** | **1.000000** | **1.000000** | **1.000000** | **0** | **4.102 s** | **Passed (Full Multi-hop Path)** |

---

## 3. Root Cause Corrections

1. **Patient MRN Collision Fix:** Corrected `Patient(mrn=f"EVAL-{patient_id.hex[:16]}")` in `ProductRetrievalAdapter._materialize` to `Patient(mrn=f"EVAL-{patient_id.hex}")`, eliminating SQLite `UNIQUE` constraint collisions when benchmark patient UUIDs share prefix bits.
2. **Multi-Hop Traversal String Normalization:** Fixed case-insensitive string formatting for relation edge tuples (`source_name|relation_type|target_name`) in `ProductGraphAdapter._path_ids`, ensuring exact matching against `case.graph.required_edges`.
3. **Retrieval Ablation Integration:** Added `retrieval_mode="graph"` to `run_ai_evaluation.py` CLI and `EvaluationConfig` in `runner.py`.

---

## 4. Verification Evidence & Artifacts

- **Graph Release Artifacts:** `app/backend/evaluation-artifacts/graph-45/`
- **Ablation Artifacts:** `app/backend/evaluation-artifacts/ablation-graph/`
- **Unit Tests:** `py -3.12 -m pytest tests/evaluation/` (67 passed in 14.2s)
