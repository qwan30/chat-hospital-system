# Retrieval Ablation Baseline — 2026-07-23

> Superseded by the [corrected source-question baseline](retrieval-ablation-baseline-377a7fe-20260723.md).
> This report is retained as historical evidence of the benchmark-design defect that was corrected.

## Outcome

No retrieval mode is accepted yet. Vector retrieval preserved the hard authorization
gate but retrieved almost no expected evidence. BM25 and hybrid improved retrieval
quality substantially but returned forbidden evidence in four safe-refusal cases.

These are observed source-backed measurements, not production-readiness claims.

## Controlled comparison

All runs used:

- Git SHA `e40ad9ce2c069ec4f0b7f757c1a66cd03cd27e65`.
- Dataset `synthetic-100-v2`.
- The deterministic 50-case smoke sentinel.
- 39 answer-policy cases for aggregate retrieval quality.
- The same evidence threshold and source-backed temporary database adapter.
- Zero model tokens; no LLM judge contributed to these metrics.

| Mode | Recall@5 | MRR | nDCG@5 | Unauthorized evidence cases | Runtime |
|---|---:|---:|---:|---:|---:|
| Vector | 0.025641 | 0.025641 | 0.025641 | 0 | 3.303 s |
| BM25 | 0.692308 | 0.692308 | 0.692308 | 4 | 4.125 s |
| Hybrid | 0.692308 | 0.692308 | 0.692308 | 4 | 3.548 s |

Required initial gates are Recall@5 >= 0.90, MRR >= 0.85, nDCG@5 >= 0.85,
and zero unauthorized evidence.

## Evidence

- [Vector run 29999858740](https://github.com/qwan30/chat-hospital-system/actions/runs/29999858740)
- [BM25 run 29999570824](https://github.com/qwan30/chat-hospital-system/actions/runs/29999570824)
- [Hybrid run 29999052393](https://github.com/qwan30/chat-hospital-system/actions/runs/29999052393)
- Machine-readable baseline:
  `app/backend/data/evaluation/baselines/retrieval-smoke-e40ad9c.json`

The four BM25/hybrid safety failures are `safe_no_evidence` cases with no allowed
evidence and one forbidden source each. The lexical modes matched generic query
language strongly enough to return those sources. This is a reranking or
evidence-validation problem; lowering gates or hiding those cases is not an
acceptable remediation.

## Decision

Keep the current vector product default while the project remains in evaluation.
Do not advertise a retrieval pass. The next bounded improvement should combine
lexical recall with a deterministic safe-no-evidence validation or a calibrated
reranker, then rerun the same three immutable cases and compare against this
baseline.

## CV-safe statement

Implemented a source-backed healthcare RAG evaluation harness with deterministic
authorization gates and vector/BM25/hybrid ablations over a 50-case sentinel.
Measured a lexical retrieval improvement from 0.026 to 0.692 Recall@5 while
detecting four safety violations that prevented release.
