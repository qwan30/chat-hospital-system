# Review — Codebase Audit 2026-05

**Execute outcome:** 3 findings closed, 15 filed for follow-up. Backend suite: **238 passed, 2 skipped**.

## Fixes Landed

| ID | Severity | Change | Tests |
|---|---|---|---|
| **F-RAG-001** | P1 | `chat_stream._generate_sse_events` now buffers the full LLM output, validates citations against the authorized evidence set, and either flushes the answer + only-cited evidence or emits a safe refusal with `validation=failed`. | `test_streaming_rejects_answer_with_hallucinated_citation`, `test_streaming_emits_only_cited_evidence_when_validated` |
| **F-RAG-002** | P1 | New helper `meets_evidence_threshold(item, mode, threshold)` in `chat_utils`. Hybrid mode now compares against the underlying retriever scores stored in `score_list_*` metadata (preserved by RRF), unblocking hybrid retrieval. Wired into both `chat.py` and `chat_stream.py`. | 5 unit tests covering vector/bm25/hybrid with and without metadata |
| **F-SEC-004** | P2 | SSE error events no longer carry `str(exc)`. `AppError` subclasses surface sanitized `code`+`message`; anything else becomes `INTERNAL_ERROR` + "Stream failed due to an internal error." Full trace logged server-side. | `test_streaming_error_event_does_not_leak_exception_string` |

## Files Touched

```
app/backend/src/hospital_ai/services/chat_utils.py       (+30 lines — helper)
app/backend/src/hospital_ai/services/chat.py             (±5 lines — helper import + threshold call-site)
app/backend/src/hospital_ai/api/routes/chat_stream.py    (~110 lines — buffer/validate/sanitize + hybrid dispatch)
app/backend/tests/test_audit_2026_05.py                  (new, 8 tests, all pass)
history/codebase-audit-2026-05/                          (feature history; findings + approach + review)
```

## Verification

```
cd app/backend && python -m pytest tests/test_audit_2026_05.py -v     # 8/8 passed
cd app/backend && python -m pytest --no-header -q                      # 238 passed, 2 skipped
python -m compileall src tests scripts -q                              # clean
```

## Behavioral Notes for Reviewers

- **Streaming UX change (F-RAG-001):** The SSE endpoint no longer emits tokens as the LLM generates them. It now buffers the full answer, validates citations, then flushes the answer as line-sized token events. Perceived latency increases by roughly the LLM's generation time (rather than time-to-first-token). This is an explicit safety-over-UX trade-off. Frontends continue to work unchanged because the event shape is preserved.
- **Hybrid retrieval now functional (F-RAG-002):** Any deployment with `HOSPITAL_AI_RETRIEVAL_MODE=hybrid` was silently receiving `SAFE_NO_EVIDENCE_ANSWER` for every query. Those deployments will now return grounded answers.
- **Citation filtering (F-RAG-001):** Streaming now emits only the chunks the LLM cited, matching the non-streaming `ChatResponse` contract. Previously it dumped all retrieved chunks.

## Deferred to Follow-up Beads

All 15 remaining findings are scoped, severity-tagged, and triaged in `findings.md`. Recommended bead slicing:

1. **`hospital-bead-audit-P2-stream-audit`** — F-RAG-004 (stream endpoint persists no `RetrievedEvidence` rows, no success audit).
2. **`hospital-bead-audit-P2-dev-tokens`** — F-SEC-001 (refuse committed dev tokens when `environment != "local"`).
3. **`hospital-bead-audit-P2-graph-rag-patient-isolation`** — F-RAG-003 + F-STRUCT-001 combined (add `patient_id` filter to `find_related_entities`; delete or correctly wire `GraphEnhancedQAPipeline`).
4. **`hospital-bead-audit-P2-streaming-e2e-tests`** — F-TEST-001 (replace placeholder streaming tests with httpx-driven SSE tests; folds naturally into bead 1).
5. **`hospital-bead-audit-P3-cleanup`** — F-SEC-002 / F-SEC-003 / F-SEC-005 / F-BUG-001 / F-BUG-002 / F-BUG-003 / F-STRUCT-002 / F-RAG-005 / F-TEST-004.

Beads 1 and 3 most benefit from running in Codex CLI where `gitnexus_impact` is available before editing `find_related_entities` and the SSE handler.
