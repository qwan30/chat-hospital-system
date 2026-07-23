# Corrected Retrieval Ablation Baseline — 2026-07-23

## Verdict

**CONDITIONAL — BM25 is the selected retrieval candidate, not yet the production default.**

The corrected benchmark removes internal source IDs and patient UUIDs from questions.
It now asks with clinical source terms and uses single clinically meaningful terms
verified absent from both patient sources for safe-no-evidence cases.

The retrieval component passes its deterministic quality and authorization gates for
BM25 and hybrid. The overall evaluation run remains blocked only by the independent
sentinel-review requirement; it is not a retrieval failure.

## Controlled comparison

All three runs used Git SHA `377a7fe49f253b04bf21e27ea200c5f532c1ec2e`, dataset
`synthetic-100-v2`, the deterministic 50-case smoke sentinel, 39 answer-policy
cases for aggregate quality, and zero model tokens.

| Mode | Recall@5 | MRR | nDCG@5 | Unauthorized evidence cases | Runtime | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Vector | 0.025641 | 0.025641 | 0.025641 | 0 | 3.971 s | Fails quality gates |
| BM25 | 1.000000 | 1.000000 | 1.000000 | 0 | 3.822 s | Retrieval candidate |
| Hybrid | 1.000000 | 1.000000 | 1.000000 | 0 | 3.968 s | Passes, but slower |

Required gates are Recall@5 >= 0.90, MRR >= 0.85, nDCG@5 >= 0.85, and zero
unauthorized evidence cases.

## Evidence

- [Vector run 30002518534](https://github.com/qwan30/chat-hospital-system/actions/runs/30002518534)
- [BM25 run 30001765964](https://github.com/qwan30/chat-hospital-system/actions/runs/30001765964)
- [Hybrid run 30002311838](https://github.com/qwan30/chat-hospital-system/actions/runs/30002311838)
- Machine-readable baseline: `app/backend/data/evaluation/baselines/retrieval-smoke-377a7fe.json`

## Remaining release gates

- Two independent reviewers must approve each selected sentinel case.
- Chat and SSE must be run under BM25 to prove authorization and safety parity.
- The image OCR lane requires its configured OCR engine.
- Graph multi-hop evaluation remains a separate failing component.

## CV-safe statement

Built a source-backed healthcare RAG evaluation harness with deterministic
authorization gates and vector/BM25/hybrid ablations. After correcting benchmark
questions to use clinical source terms, BM25 achieved Recall@5, MRR, and nDCG@5 of
1.000 across 39 answer-policy cases with zero unauthorized evidence; the product
default remains unchanged pending chat and SSE validation.
