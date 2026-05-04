# STATE
focus: Codebase audit 2026-05 — 3 priority fixes landed, 15 findings deferred
phase: compounding-complete-priority-fixes-landed
last_updated: 2026-05-04

## Active Feature

Skill: compounding (audit closeout complete)
Feature: codebase-audit-2026-05
Epic: standalone
Context: `history/codebase-audit-2026-05/CONTEXT.md`
Findings: `history/codebase-audit-2026-05/findings.md`
Review: `history/codebase-audit-2026-05/review.md`

### Audit Summary

- **Scope:** `app/backend/` (full backend code path + tests). Frontend not audited.
- **Tooling deviation:** GitNexus MCP not exposed to Cascade in this session. Used `code_search`, `grep_search`, `read_file` directly. CLI-side `npx gitnexus analyze` is up to date.
- **Findings:** 18 total (2 P1, 7 P2, 9 P3).
- **Closed this session:** F-RAG-001 (P1, SSE citation validation), F-RAG-002 (P1, hybrid threshold scale), F-SEC-004 (P2, SSE error sanitization).
- **Deferred:** 15 findings, full triage in `findings.md`. Recommended bead slicing in `review.md`.
- **Backend tests:** 238 passed, 2 skipped. 8 new regression tests in `tests/test_audit_2026_05.py`.
- **Compile:** `python -m compileall src tests scripts` clean.

### Files Touched

- `app/backend/src/hospital_ai/services/chat_utils.py` — new `meets_evidence_threshold` helper.
- `app/backend/src/hospital_ai/services/chat.py` — wired helper.
- `app/backend/src/hospital_ai/api/routes/chat_stream.py` — buffer/validate citations, sanitize errors, mode-aware threshold, mirror retrieval-mode dispatch.
- `app/backend/tests/test_audit_2026_05.py` — new (8 tests).
- `history/codebase-audit-2026-05/findings.md` + `review.md` — full audit report.
- `history/learnings/critical-patterns.md` — promoted two new entries (streaming contract drift, threshold scale mismatch).

## Paused Feature

- `kotaemon-chat-assistant-ui` (epic `br-dyy`) — phase `compounding-complete-human-signoff-pending`. Handoff preserved at `.khuym/HANDOFF.json`. Pending: human UAT sign-off + final epic close. Resume by re-reading `.khuym/HANDOFF.json` and `history/kotaemon-chat-assistant-ui/`.

## Recommended Next Beads

1. `hospital-bead-audit-P2-stream-audit` — F-RAG-004 (persist `RetrievedEvidence` + emit success audit on `/chat/stream`).
2. `hospital-bead-audit-P2-dev-tokens` — F-SEC-001 (refuse default `dev_bearer_tokens` when `environment != "local"`).
3. `hospital-bead-audit-P2-graph-rag-patient-isolation` — F-RAG-003 + F-STRUCT-001 (filter `find_related_entities` by `patient_id`; delete or fix `GraphEnhancedQAPipeline`).
4. `hospital-bead-audit-P2-streaming-e2e-tests` — F-TEST-001 (real httpx-driven SSE tests; folds into bead 1).
5. `hospital-bead-audit-P3-cleanup` — batch the remaining P3s.

Beads 1 and 3 should run in Codex CLI where `gitnexus_impact` is available before editing the SSE handler and `find_related_entities`.

## Prior State (archived below for reference)

Skill: compounding
Feature: streaming-rag-and-persistent-settings
Epic: `br-dyy` (continued)
Plan Gate: implemented and committed
Execution Gate: code committed, GitNexus indexed
Review Gate: Session learnings captured in history/learnings/20260429-streaming-and-persistent-settings.md
Current Phase To Prepare Next: transition to next feature or final project hardening

Phase 1 streaming is complete: SSE support added to frontend and backend reasoning chains with explicit AbortController lifecycle management.

Phase 2 persistent settings is complete: SQL-backed SettingsStore with Alembic migrations replaces environment-only configuration for clinical tuning.

Phase 3 hardening is complete: GraphRAG service implemented, and worker queue enhanced with retry/DLQ support for clinical data stability.

Phase 1 live frontend wiring is complete: the root chat workspace loads persisted backend threads, uses explicit backend URL and bearer-token controls, maps thread details into one active workspace state, and wires create, rename, archive, share, and thread-message submission actions.

Phase 2 safe general hospital knowledge is complete for curated approved non-PHI sources: general chat-thread messages use a backend service that does not query patient chunks, returns cited approved sources when evidence matches, and returns an honest no-evidence answer otherwise.

Phase 3 HMS appointment evidence is complete for one explicit synthetic/de-identified data family: `POST /api/v1/hms/appointments/import` indexes appointment summaries into patient-linked evidence with HMS source lineage, patient ownership validation, and existing permission-filtered retrieval.

Phase 4 automated hardening is complete: frontend token persistence was removed, thread detail loading is lazy/resilient, patient contexts derive from persisted threads, backend errors are sanitized for browser display, invalid citation paths avoid orphaned messages, and release/UAT docs are updated.

## Artifacts Updated

- `app/frontend/src/components/chat/AssistantShell.tsx`
- `app/frontend/src/lib/chat-assistant/api.ts`
- `app/frontend/src/components/chat/ConversationSidebar.tsx`
- `app/frontend/src/components/chat/EvidencePanel.tsx`
- `app/frontend/src/lib/chat-assistant/contracts.ts`
- `app/backend/src/hospital_ai/services/chat.py`
- `app/backend/src/hospital_ai/api/routes/hms.py`
- `app/backend/src/hospital_ai/schemas/hms.py`
- `app/backend/src/hospital_ai/services/hms_appointments.py`
- `app/backend/src/hospital_ai/services/chat_threads.py`
- `app/backend/src/hospital_ai/services/general_knowledge.py`
- `app/backend/scripts/seed_dev.py`
- `app/backend/tests/test_chat_thread_messages_api.py`
- `app/backend/tests/test_hms_appointment_import.py`
- `app/frontend/scripts/verify-chat-workspace-state.mjs`
- `docs/06_database_api_integration.md`
- `docs/08_master_test_plan_rtm.md`
- `app/backend/README.md`
- `app/frontend/README.md`
- `app/README.md`
- `history/kotaemon-chat-assistant-ui/phase-3-4-verification.md`
- `history/kotaemon-chat-assistant-ui/discovery.md`
- `history/kotaemon-chat-assistant-ui/approach.md`
- `history/kotaemon-chat-assistant-ui/phase-plan.md`

## Verification Summary

- Backend: `python -m pytest` passed with `57 passed, 2 skipped`.
- Backend compile: `PYTHONPYCACHEPREFIX=.verify-pycache python -m compileall src tests scripts` passed.
- Frontend workspace contract: `npm run test:workspace` passed with `16` tests.
- Frontend: `npm.cmd run typecheck`, `npm.cmd run lint`, and `npm.cmd run build` passed.
- API UAT: `python scripts/uat_product_api_check.py` passed for dev doctor, records, security, admin, anonymous, and wrong-token scenarios.
- Browser UAT: Playwright found a CORS blocker, the blocker was fixed, then `dev-doctor` reload loaded persisted backend threads with no new console errors; wrong-token UI showed a sanitized denial with no PHI.

## Product UAT Summary

Agent-run product UAT evidence is recorded in `history/kotaemon-chat-assistant-ui/uat-product-test-report.md`.

- Fixed P1: browser requests from the Next.js frontend to the FastAPI backend were blocked by missing CORS headers.
- Fix: added explicit local UAT CORS origins through backend settings and `CORSMiddleware`.
- Regression: `app/backend/tests/test_cors.py`.
- Evidence directory: `history/kotaemon-chat-assistant-ui/uat-evidence/20260428T170614Z`.
- Manual end-user evidence directory: `history/kotaemon-chat-assistant-ui/uat-evidence/manual-end-user-20260429`.
- Manual end-user check found no new P1. The four P2 findings are now fixed:
  - archived conversations are hidden from the default active thread list;
  - patient-linked HMS appointment answers state appointment status and vital signs from cited evidence;
  - patient-allowed evidence now shows allowed-state boundary copy;
  - `New conversation` confirms patient-linked scope before backend persistence.

## Review Summary

Automated specialist review found no P1 findings. Phase 3/4 execution closed the resolved follow-up beads:

- Closed P2 `br-bhm` - derive patient context from persisted threads.
- Closed P2 `br-d0q` - make thread-detail loading lazy and resilient.
- Closed P2 `br-1kq` - remove client token persistence.
- Closed P2 `br-9e6` - test invalid general-answer citations.
- Closed P2 `br-760` - add behavioral frontend and seeded UAT coverage.
- Closed P3 `br-9kw` - sanitize backend error display.
- Closed P3 `br-epf` - wire or remove inert sidebar controls.

Artifact verification found all changed implementation artifacts exist, are substantive, and are wired. One artifact polish issue became P3 `br-epf`.

Remaining open follow-up: P3 `br-2o5` - move general knowledge sources behind a provider.

## Tooling Notes

- `gkg index D:\projects\chatbot-hospital-system` was attempted, but `gkg` is not on PATH.
- `br.exe` and `bv.exe` are on PATH.
- `br ready --json` still fails with `JSON_ERROR` because the Beads store expects a missing `jsonl_export` field.
- `bv --robot-next --graph-root br-dyy` works and reports no actionable items.

## Remaining Gaps

- Human UAT sign-off remains pending.
- Production auth/session handling is not implemented; the frontend uses explicit dev bearer-token configuration.
- General knowledge source provider abstraction remains open as P3 `br-2o5`.

## Next

Get explicit human UAT sign-off against the seeded Phase 3/4 scenario in `history/kotaemon-chat-assistant-ui/phase-3-4-verification.md`, then run final Khuym closeout. Compounding for the review/UAT fix loop is already recorded below.

## Last Compounding Run

- Feature: kotaemon-chat-assistant-ui
- Date: 2026-04-29
- Learnings file: `history/learnings/20260429-chat-uat-feedback-contracts.md`
- Critical promotions: 1
