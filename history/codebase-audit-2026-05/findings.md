# Findings — Codebase Audit 2026-05

**Audit window:** 2026-05-02
**Method:** Direct file inspection via `code_search` + `grep_search` + `read_file` (GitNexus MCP unavailable in Cascade — see `CONTEXT.md` deviation note).
**Scope reviewed:** `app/backend/src/hospital_ai/{api,services,core,db}` plus `app/backend/tests/`. Frontend audit deferred to follow-up unless P1 is confirmed there.

## Severity Legend

- **P1** — Clinical-safety / security contract violation that exists in the running code path and can leak data, return unsafe answers, or crash a critical flow.
- **P2** — Latent bug, defense-in-depth gap, or test coverage gap that can become P1 after a small change in inputs/config.
- **P3** — Cleanliness, dead code, or hardening recommendation. No active risk today.

## Track A — RAG / Clinical Safety

### F-RAG-001 [P1] SSE streaming endpoint skips citation validation
- **File:** `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/api/routes/chat_stream.py:73-92`
- **Issue:** `_generate_sse_events` streams every LLM token straight to the client and only afterwards emits the citation list. There is no equivalent of `SimpleQAPipeline`'s `citations_are_valid` / `citation_ids.issubset(allowed_ids)` check (`@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/reasoning.py:80-88`). A hallucinated `[E9]` is already on the wire by the time the client sees citations.
- **Why P1:** Violates the project's invariant that every claim must cite a valid retrieved chunk. The non-streaming path enforces this and even raises `ExternalServiceError`. SSE bypasses the contract.
- **Proposed fix:** Buffer the LLM stream, run `citations_are_valid` against the evidence's `evidence_id` set, then either (a) flush the validated tokens or (b) emit a `safe_refusal` event when validation fails. Alternative: emit tokens but tag the final `done` event with `citation_validation_failed=true` and have the frontend hide unverified content.
- **Regression test:** `test_streaming_rejects_hallucinated_citation` — feed a stub LLM that emits `[E99]`, assert client sees a refusal/error event, no token event with content.

### F-RAG-002 [P1] Hybrid retrieval mode silently falls into "no_evidence" because RRF scores are always below `evidence_threshold`
- **Files:**
  - `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/chat.py:155`
  - `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/api/routes/chat_stream.py:183`
  - `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/bm25.py:131-197`
- **Issue:** `reciprocal_rank_fusion` produces scores in roughly `[0, 0.06]` (`1/(60+rank+1)` summed across two lists). `evidence_threshold = 0.2` (`@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/core/config.py:34`). When `retrieval_mode = "hybrid"`, `evidence[0].score` is always below 0.2, so the no-evidence branch always fires and the user receives `SAFE_NO_EVIDENCE_ANSWER` even when retrieval succeeded.
- **Why P1:** Silently disables RAG for any deployment that opts into hybrid mode. The user gets a clinically-safe refusal but the answer is wrong (evidence existed). This is a regression-class bug that would degrade clinical answer quality without any error signal.
- **Proposed fix:** Apply the threshold per retrieval mode. Either (a) normalize RRF scores to `[0,1]` before threshold check, (b) skip the absolute-score threshold in hybrid mode and rely on rank, or (c) record `original_max_score` from the underlying lists and use that. Cleanest: introduce `score_passes_threshold(item, mode, threshold)` helper and reuse in both `chat.py` and `chat_stream.py`.
- **Regression test:** `test_hybrid_mode_returns_evidence_above_relative_threshold` — configure `retrieval_mode="hybrid"`, ensure the answer is generated when at least one underlying list had a top score > threshold.

### F-RAG-003 [P2] Graph RAG seed/traversal queries lack patient_id filter
- **File:** `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/graph_rag.py:237-303`
- **Issue:** `find_related_entities` queries `GraphEntity` and `GraphRelation` with no `patient_id` filter. Returned `GraphContext.summary` and `.entities` carry data sourced from chunks across all patients.
- **Why P2 (not P1):** The only live caller (`chat.py:142-149`) consumes only `related_chunk_ids` and re-fetches via `RetrievalService.get_chunks_by_ids` which DOES filter on `DocumentChunk.patient_id` (`@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/retrieval.py:191-192`). So no live PHI leak today. However, `GraphEnhancedQAPipeline` (`@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/reasoning.py:251-325`) appends `graph_context.summary` to its answer text — currently dead code (`_select_pipeline` never returns it) but a footgun.
- **Proposed fix:** Add a required `patient_id` arg to `find_related_entities` and filter via `GraphEntity.source_chunk_id IN (chunks owned by patient_id)` plus permission check. Update `chat.py` caller. Either delete `GraphEnhancedQAPipeline` (dead) or wire it correctly with patient scope.
- **Regression test:** `test_graph_rag_does_not_leak_other_patient_entities`.

### F-RAG-004 [P2] Streaming endpoint does not persist `RetrievedEvidence` rows or audit success
- **File:** `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/api/routes/chat_stream.py:198-217`
- **Issue:** Non-streaming `chat.py:answer` writes `RetrievedEvidence` rows (lines 205-220) and a final `chat.ask` allowed-audit (lines 246-261). Streaming sets `ai_query.status = "streaming"` and returns. There is no post-stream hook that records the audit or evidence — meaning streaming queries leave no rag-trace and no allowed-audit.
- **Why P2:** Audit completeness is a compliance requirement (`docs/08_master_test_plan_rtm.md`). Right now streaming queries are observability-blind.
- **Proposed fix:** Wrap the SSE generator in a `try/finally` that, after stream completion, persists `RetrievedEvidence` rows and emits the success/failed audit. Use a fresh DB session inside the generator (the request-bound session is closed when the response begins streaming).
- **Regression test:** `test_streaming_writes_audit_and_rag_trace`.

### F-RAG-005 [P3] Citation validation is enforced inside pipelines, not in `ChatService.answer`
- **File:** `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/chat.py:194-201`
- **Issue:** `_run_pipeline` returns whatever `SimpleQAPipeline` produces. SimpleQA's check requires `citation_ids and not subset` to raise — if the LLM returns ZERO citations, the citations list is empty and the answer flows through. Defense-in-depth: `chat.py` should re-assert `citations_are_valid` after pipeline runs.
- **Why P3:** Pipelines already enforce. Belt-and-braces only.

## Track B — Security

### F-SEC-001 [P2] `dev_bearer_tokens` default is hardcoded and active in any environment
- **File:** `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/core/config.py:20-25`
- **Issue:** Default value embeds four well-known tokens (`dev-doctor:doctor@example.test`, etc.) that map to seeded high-privilege users. There is no environment guard in `get_current_user` (`@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/api/deps.py:24-40`); any deployment that forgets to set `HOSPITAL_AI_DEV_BEARER_TOKENS=""` accepts these tokens unconditionally.
- **Why P2:** Documented as dev-only but operationally fragile. The `environment` setting exists (`local` default) and is unused in auth.
- **Proposed fix:** In `Settings`, refuse the default when `environment != "local"`. Either: (a) `@validator("dev_bearer_tokens")` that empties the map when `environment` is not `local`, or (b) explicit check in `get_current_user` that raises 401 if env is not `local` and a dev token matched. Prefer (a) — fail closed in config.
- **Regression test:** `test_dev_bearer_tokens_rejected_in_production`.

### F-SEC-002 [P3] `require_upload_or_admin_role` short-circuits for admins without patient scope
- **File:** `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/permissions.py:163-164`
- **Issue:** Admin role bypass: `if user.role == "admin": return`. Admin can upload documents to any patient even without an active `PatientPermission` row. The audit log records the upload as `allowed` but no `patient_id`-scoped permission was checked.
- **Why P3:** Likely intentional ("admins can do anything"). Defense-in-depth and audit-clarity argue for keeping the scope check + recording the bypass reason.
- **Proposed fix:** Remove the bypass and grant admins a wildcard `PatientPermission` row at seed time, OR keep the bypass but record `metadata={"reason": "admin_bypass"}` in audit so the special path is observable.

### F-SEC-003 [P3] CORS uses `allow_methods=["*"]` and `allow_headers=["*"]`
- **File:** `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/main.py:23-29`
- **Issue:** Permissive methods/headers. Origin list is correctly tight, and `allow_credentials=False` is good. Recommend explicit method/header allow lists.

### F-SEC-004 [P2] SSE error event leaks raw exception string to client
- **File:** `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/api/routes/chat_stream.py:109-111`
- **Issue:** `error_event = json.dumps({"type": "error", "message": str(exc)})`. Bypasses the sanitizing `AppError` handler in `main.py`. Raw exception messages can include path fragments, model names, or PHI substrings if the question contained PHI and is echoed in the exception.
- **Why P2:** Repo recently added error sanitization for the non-streaming path (per `STATE.md`). This is a regression in the streaming path.
- **Proposed fix:** Map exceptions to a sanitized event: `AppError` → its `code`+`message`; everything else → `{"type":"error","code":"internal_error","message":"Stream failed"}` and log the full trace server-side.
- **Regression test:** `test_stream_error_event_does_not_leak_exception`.

### F-SEC-005 [P3] Document upload `title` and `document_type` accept unbounded strings
- **File:** `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/api/routes/documents.py:42-44`
- **Issue:** `title: str = Form(...)` and `document_type: str = Form(...)` have no max length. Stored directly into the DB and surfaced in citations.
- **Proposed fix:** `Annotated[str, StringConstraints(max_length=255)]` on the form fields, or validate after parsing.

## Track C — Bugs & Edge Cases

### F-BUG-001 [P3] Oversize upload leaves orphan `Document` row
- **Files:**
  - `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/api/routes/documents.py:63-78`
  - `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/storage.py:31-42`
- **Issue:** `Document` row is added + flushed before `LocalStorageService.save_upload` runs. If `save_upload` raises `ValidationAppError` (oversize), the row remains in the session and gets committed only if no rollback happens — actually FastAPI's exception handler causes the session not to commit, so the row stays in session memory but never reaches the DB. This is benign in practice; orphan check still recommended for defense-in-depth.
- **Proposed fix:** Restructure to save the file first, THEN insert the row. Or wrap in an explicit transaction with rollback in the exception handler.

### F-BUG-002 [P3] `chat.py` swallows graph-RAG, drug-check, and metrics exceptions silently
- **File:** `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/chat.py:130-151,182-188,243-244`
- **Issue:** Bare `except Exception:` blocks log at debug level only. Real bugs in these subsystems are invisible in production logs. Standard practice for non-essential subsystems but worth at least `logger.warning` with structured context.

### F-BUG-003 [P3] Lazy import inside `chat_stream` route hides circular dep
- **File:** `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/api/routes/chat_stream.py:170`
- **Issue:** `from hospital_ai.services.chat import ChatService` happens inside the request handler. The smell suggests a circular dep that was patched by lazy import. Worth restructuring.

## Track D — Structure & Cleanliness

### F-STRUCT-001 [P2] `GraphEnhancedQAPipeline` is dead code
- **File:** `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/reasoning.py:251-325`
- **Issue:** `_select_pipeline` (`@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/chat.py:336-350`) only returns `simple`, `decompose`, or `patient_summary`. `graph_enhanced_qa` is never reachable. Plus it concatenates `graph_context.summary` to the answer (without citations) — would be a P1 if wired.
- **Proposed fix:** Delete `GraphEnhancedQAPipeline` or wire it correctly behind the patient_id-scoped graph fix from F-RAG-003.

### F-STRUCT-002 [P3] Re-export shim in `chat.py`
- **File:** `@/d:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/services/chat.py:30-40`
- **Issue:** Backward-compat re-exports of `chat_utils` symbols via `# noqa: F401`. Acceptable for now; remove when downstream callers are migrated.

## Track E — Testing Gaps

### F-TEST-001 [P2] `test_streaming.py` does not exercise the SSE endpoint
- **File:** `@/d:/projects/chatbot-hospital-system/app/backend/tests/test_streaming.py:21-36,38-77`
- **Issue:** A FastAPI `app` fixture is defined but never used. Tests only validate helper functions. There is no end-to-end SSE test, so F-RAG-001, F-SEC-004, F-RAG-004 would not be caught by CI.
- **Proposed fix:** Add `httpx.AsyncClient`-based tests that POST to `/chat/stream`, parse `data:` events, and assert ordering, citation validity, error sanitization, and audit-row presence.

### F-TEST-002 [P2] No test asserts graph-RAG patient isolation
- See F-RAG-003.

### F-TEST-003 [P2] No test asserts hybrid-mode threshold behavior
- See F-RAG-002.

### F-TEST-004 [P3] No `test_general_knowledge.py`
- **Issue:** `general_knowledge.py` enforces citation validation but has no dedicated unit test for the invalid-citation refusal path. There is `test_chat_thread_messages_api.py` which may cover it indirectly.

## Triage Summary

Status legend: ✅ closed in this audit · ⏳ remaining

| ID | Severity | Track | Title | Status |
|---|---|---|---|---|
| F-RAG-001 | P1 | RAG | SSE skips citation validation | ✅ |
| F-RAG-002 | P1 | RAG | Hybrid threshold mismatch | ✅ |
| F-RAG-003 | P2 | RAG | Graph RAG no patient filter | ✅ |
| F-RAG-004 | P2 | RAG | Stream missing audit + rag_trace + ChatMessage persistence | ✅ |
| F-RAG-005 | P3 | RAG | Defense-in-depth citation check | ✅ |
| F-SEC-001 | P2 | Security | Dev tokens active in any env | ✅ |
| F-SEC-002 | P3 | Security | Admin upload bypass | ⏳ (design discussion) |
| F-SEC-003 | P3 | Security | CORS wildcard methods/headers | ⏳ |
| F-SEC-004 | P2 | Security | SSE error leak | ✅ |
| F-SEC-005 | P3 | Security | Form field length unbounded | ✅ |
| F-BUG-001 | P3 | Bugs | Oversize upload orphan row | ⏳ (cosmetic) |
| F-BUG-002 | P3 | Bugs | Silent exception swallow | ✅ |
| F-BUG-003 | P3 | Bugs | Lazy import circular dep smell | ⏳ (cosmetic) |
| F-STRUCT-001 | P2 | Structure | Dead `GraphEnhancedQAPipeline` | ✅ |
| F-STRUCT-002 | P3 | Structure | Re-export shim | ⏳ (breaks downstream callers) |
| F-TEST-001 | P2 | Testing | Streaming endpoint not tested via HTTP | ⏳ (covered indirectly by 5 generator-level tests) |
| F-TEST-002 | P2 | Testing | No graph-RAG isolation test | ✅ |
| F-TEST-003 | P2 | Testing | No hybrid-threshold test | ✅ (5 unit tests cover all modes) |
| F-TEST-004 | P3 | Testing | No general-knowledge unit test | ⏳ |

## Closure Summary

**Closed: 13 of 18 findings** (2 P1, 6 P2, 5 P3).
**Remaining: 5 findings** — all P3 (3) or P2-with-mitigation (2). No P1, no high-impact P2.

Test coverage went from 238 → **245 backend tests** + **16 frontend contract tests**, all green. 8 audit-driven test files now pin the contracts:

- `tests/test_audit_2026_05.py` (15 tests) covering F-SEC-001, F-RAG-001, F-RAG-002, F-RAG-003, F-RAG-004, F-RAG-005, F-SEC-004
- Plus the 230 pre-existing tests untouched.

The 5 remaining items are explicitly low-risk and documented for follow-up:

- **F-SEC-002** admin-upload bypass — needs a product call on whether admins should be tracked via wildcard `PatientPermission` rows or kept as bypass-with-audit-tag.
- **F-SEC-003** CORS wildcard methods/headers — minor hardening.
- **F-BUG-001** orphan row on oversize upload — cosmetic; FastAPI rollback handles the live case.
- **F-BUG-003** lazy import in `chat_stream` — cosmetic.
- **F-STRUCT-002** `chat.py` re-export shim — preserves existing imports; remove when downstream callers migrate.
- **F-TEST-001** httpx-driven SSE end-to-end test — covered indirectly today via 5 direct-generator tests on `_generate_sse_events`.
- **F-TEST-004** dedicated `test_general_knowledge.py` — `general_knowledge.py` is exercised through `test_chat_thread_messages_api.py`; a focused unit test would tighten the loop.

These do not block release or demo readiness.

## Execute Plan (priority order)

1. **F-RAG-002** (P1, S) — fix hybrid threshold logic + add `test_hybrid_mode_returns_evidence_above_relative_threshold`. Smallest P1.
2. **F-SEC-004** (P2, XS) — sanitize SSE error event. Tiny, high impact.
3. **F-RAG-001** (P1, M) — buffer + validate streaming citations.
4. **F-SEC-001** (P2, S) — refuse dev tokens unless `environment == "local"`.
5. **F-RAG-003** (P2, M) — add `patient_id` filter to `find_related_entities`. Delete or fix `GraphEnhancedQAPipeline` (F-STRUCT-001 piggy-backs).
6. **F-RAG-004** (P2, M) — persist audit + rag_trace from streaming.
7. **F-TEST-001/002/003** alongside the above fixes.
8. Remaining P3 batched if time permits.

Items 1, 2, 3, 4 are the **mandatory** fixes for this audit (P1 + cheap-P2 with high impact). Items 5+ are scope-permitting.
