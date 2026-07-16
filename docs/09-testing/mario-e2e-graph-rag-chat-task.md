# Mario E2E QA Task — Graph RAG and Chat

**Date:** 2026-07-16  
**Scope:** Local-only, synthetic-data QA campaign for Graph RAG, `/chat`, `/chat/stream`, and the browser chat/graph experience.  
**Delivery type:** Tests, reproducible evidence, defects, and release verdict. Product fixes are out of scope.

## Acceptance contract

| Area | Release condition |
|---|---|
| Graph RAG | The graph relation evaluator proves exact patient isolation; traversal and graph evidence exclude deleted, stale, and unauthorized sources. |
| Non-stream chat | Authorization precedes all retrieval/generation work; every substantive answer is supported by authorized citations; graph evidence is deterministic and within `top_k`. |
| SSE chat | `/chat/stream` has the same authorization, evidence, citation, audit, and Graph RAG behavior as `/chat`; terminal events are safe and ordered. |
| Browser | A serial live-backend Playwright run with seeded roles proves API-authoritative access control, stream abort/retry, and cited-answer usefulness. Mocked tests are fast checks only. |

## Executed work

- Added `app/backend/tests/test_graph_rag_chat_release_gates.py`.
  - A passing scope test seeds Alice and Bob with the same entity and asserts exact per-patient chunk sets.
  - Strict expected-failure gates retain confirmed product gaps for page lifecycle filtering, re-index replacement, required citations, Graph RAG `top_k`, and `/chat`/`/chat/stream` graph-only parity.
- Strengthened `app/backend/scripts/run_rag_eval.py` so `graph_relation_scope` seeds both patients and requires exactly Alice's chunk rather than merely checking Alice inclusion.
- Ran the synthetic evaluator and focused backend/browser checks. See `graph-rag-chat-qa-report.md` for results and artifact locations.

## Exit rule

This task remains open until the synthetic evaluator passes 6/6, every strict release gate can be converted to a passing assertion, the live browser contract passes, and no P0/P1 chat or Graph RAG defect remains.

