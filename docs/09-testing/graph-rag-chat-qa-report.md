# Graph RAG & Chat QA Report

> **Historical report warning:** Verdict and pass counts below are tied to the recorded date/environment. Current CI defers Playwright without a backend service, so this report is not current-SHA browser certification. Use the full-project automation matrix for current status.

**Test date:** 2026-07-16  
**Environment:** Local isolated worktree, Python 3.12, Bun 1.3.13, synthetic/de-identified seed data only  
**Scope:** Graph RAG, non-stream chat, SSE chat, and browser chat/graph controls  
**Verdict:** **DO NOT SHIP**

## Evidence summary

| Check | Result | Evidence |
|---|---|---|
| Existing focused backend baseline | PASS | `34 passed` — `tests/test_graph_rag_integration.py`, `test_chat_citations.py`, `test_chat_stream_endpoint.py`, `test_audit_2026_05.py` |
| New Graph RAG/chat release gates | BLOCKED | `1 passed, 6 xfailed` — strict xfails deliberately retain confirmed P0/P1 defects until a reviewed product fix turns them into normal passing assertions. |
| Synthetic RAG evaluator | FAIL | `5/6`; `graph_relation_scope` returned zero chunks after the evaluator was strengthened to exclude Bob's same-entity data. Process exit code `1`. |
| Frontend type check | PASS | `bun run typecheck` |
| Focused mocked browser checks | FAIL / non-release | At least four retained failures in chat/graph interruption and patient-flow scenarios. These tests use mocked sessions/routes and do not prove live backend authorization. |

## Confirmed defects

| ID | Severity | Scope | Actual behavior |
|---|---|---|---|
| QA-GR-001 | P0 | Graph evaluator; Alice vs Bob synthetic records | `graph_relation_scope` returns no graph chunks because deterministic extraction cannot parse provider output. |
| QA-CHAT-001 | P0 | `/chat` vs `/chat/stream`; authorized doctor; Alice | `/chat/stream` bypasses Graph RAG enrichment and returns no-evidence for a graph-only answer. |
| QA-GR-002 | P1 | Graph traversal/evidence; Alice | Graph traversal and evidence retrieval admit a chunk whose page is soft-deleted. |
| QA-GR-003 | P1 | Graph indexing; Alice | Re-indexing appends duplicate graph entities/relations. |
| QA-CHAT-002 | P1 | Non-stream chat; Alice | The service boundary accepts an uncited generated answer. |
| QA-CHAT-003 | P1 | Non-stream chat; Alice | Graph enrichment can persist more evidence than requested `top_k`. |
| QA-BROWSER-001 | P1 | Mocked browser interruption | `route.fetch()` reaches unavailable `localhost:8000`; retry/resume controls do not render and graph tests remain loading. |

## Verification commands

```powershell
cd app/backend
py -3.12 -m pytest tests/test_graph_rag_integration.py tests/test_chat_citations.py tests/test_chat_stream_endpoint.py tests/test_audit_2026_05.py tests/test_graph_rag_chat_release_gates.py -q --tb=short
py -3.12 scripts/run_rag_eval.py --output-dir ../../qa-artifacts/graph-rag-chat-2026-07-16

cd ../frontend
bun run typecheck
```

## Release decision

`DO NOT SHIP`: Graph scope evaluation and stream/non-stream Graph RAG parity fail, and P0/P1 issues remain. No product remediation was applied.

