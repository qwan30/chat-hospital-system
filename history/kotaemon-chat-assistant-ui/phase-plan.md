# Phase Plan - Complete Kotaemon-First Hospital Assistant

**Feature:** kotaemon-chat-assistant-ui
**Date:** 2026-04-28
**Skill:** khuym:planning
**Plan Gate:** approved by user and executed through Phase 2 on 2026-04-28
**Based on:**
- `history/kotaemon-chat-assistant-ui/CONTEXT.md`
- `history/kotaemon-chat-assistant-ui/discovery.md`
- `history/kotaemon-chat-assistant-ui/approach.md`
- `.khuym/HANDOFF.json`
- `.khuym/STATE.md`

---

## 1. Feature Summary

The project is now past the first hospital-data turn: the root frontend is a Kotaemon-style chat workspace, the backend has patient-scoped permission-filtered chat, shared chat thread APIs, safe general knowledge answers, and one HMS appointment evidence import path. Remaining work is human UAT sign-off and non-blocking follow-up hardening, not missing Phase 1-4 implementation.

Completion happened through four phases: persisted thread wiring, safe general knowledge, HMS appointment evidence, and automated hardening/docs verification. The project still must not be described as production-ready until human UAT and production auth/session work are handled.

---

## 2. Current Completed State

| Capability | Current state | Evidence |
|---|---|---|
| Chat-first first screen | Complete for Phase 1 | `AssistantShell` is the root experience and Phase 1 verification artifacts exist |
| Central active workspace state | Complete for sample data | `AssistantShell` owns active thread, patient context, transcript, and evidence source derivation |
| Patient-scoped backend chat | Complete for verified patient-linked questions | Backend `/api/v1/chat` and `ChatService` enforce permission-before-retrieval |
| Shared chat thread backend | Mostly complete | `/api/v1/chat-threads` supports create/list/read/update/archive, messages, participants, audit, and patient permission guards |
| Frontend persisted-thread adapter | Complete and used by the shell | `AssistantShell` loads backend threads and calls typed thread/message/participant API helpers |
| General hospital knowledge chat | Complete for approved non-PHI sources | General chat-thread messages use `GeneralKnowledgeService` and safety tests prove patient chunks are not returned |
| HMS integration | Complete for first appointment slice | `POST /api/v1/hms/appointments/import` indexes synthetic/de-identified appointment summaries as patient-linked evidence |
| Release review/UAT | Complete for automated Phase 4 gate; human UAT sign-off still external | Backend/frontend verification and release docs are recorded in `phase-3-4-verification.md` |

---

## 3. Why This Breakdown

- The live frontend wiring must happen first because the product still looks more complete than it behaves: the UI has persisted-thread adapters, but users are still seeing sample threads.
- General hospital knowledge comes after live thread wiring because D9 requires general hospital answers, and the app needs one reliable conversation storage path before another answer mode is added.
- HMS integration comes after the general path because patient-linked HMS data increases the PHI blast radius; permission and citation boundaries must be proven before richer data enters the assistant.
- Final review and UAT come last because the project cannot be called complete until tests, browser evidence, docs, and Khuym review gates all agree there are no blocking P1 findings.

---

## 4. Phase Overview Table

| Phase | What Changes In Real Life | Why This Phase Exists Now | Demo Walkthrough | Unlocks Next |
|---|---|---|---|---|
| Phase 1: Wire persisted chat threads into the frontend | Staff open the chat workspace and see real backend threads, messages, and sharing state instead of sample-only conversations | Backend APIs and frontend adapters already exist, but the shell does not call them | Start backend and frontend, sign in with a dev token, load persisted threads, open a thread, submit a patient-linked question, and see the saved assistant answer with citations after reload | General chat can reuse the same live thread flow |
| Phase 2: Add safe general hospital knowledge chat | Staff can ask non-patient hospital questions through a real backend path with citations or an honest no-evidence response | The product contract says general knowledge is supported, but current backend chat requires patient scope | Create a general thread, ask a hospital policy question, receive a cited answer from approved non-PHI knowledge, and confirm no patient permission state is required | HMS integration can add richer data without overloading the general path |
| Phase 3: Connect the first HMS-backed data slice | The assistant can answer from one explicitly supported HMS-derived data family with patient permission and evidence traceability | HMS is currently only a reference; real value needs one safe integration path | Select an authorized synthetic patient, ask about the chosen HMS data family, inspect citations, then revoke permission and confirm the same answer is blocked | Final project review can test end-to-end hospital usefulness |
| Phase 4: Hardening, review, UAT, and release docs | The project has proof that the assistant works, blocks unsafe access, documents its limits, and passes final Khuym review | The project is not finished until verification and docs catch up with implementation | Run backend/frontend tests, browser QA, permission adversarial checks, docs review, and UAT; fix P1 issues before closing | Project can be marked complete or handed off with known non-blocking future work |

---

## 5. Phase Details

### Phase 1: Wire Persisted Chat Threads Into The Frontend

- **Status:** Complete in this execution pass.
- **What Changes In Real Life:** The existing chat workspace stops being sample-first. A staff user can load persisted backend threads, switch between them, send a patient-linked question through the thread API, and see the saved answer survive reload.
- **Why This Phase Exists Now:** This is the narrowest path from current state to real product behavior. The backend and adapter are already in place; the missing piece is live shell state, auth/base URL handling, and no-fake fallback behavior.
- **Stories Inside This Phase:**
  - Story 1: Runtime API configuration and dev auth - the frontend has an explicit backend base URL and token source, with visible unauthenticated/error states.
  - Story 2: Persisted thread loading and active state - the sidebar, transcript, evidence panel, patient gate, and sharing controls all derive from one backend-loaded active thread model.
  - Story 3: Thread actions and patient-linked submit - create, rename, archive, participant display/share actions, and `askBackendThreadMessage` are wired without bypassing permission guards.
  - Story 4: Live wiring verification - adapter/unit checks plus browser smoke prove reload persistence, denied states, and citation/evidence fidelity.
- **Demo Walkthrough:** Run the backend with seed data and start the frontend with a dev API token. Open the app, load persisted threads, create a patient-linked thread for an authorized synthetic patient, ask a question, see the assistant response and citations, reload, and confirm the same thread/messages return from the backend.
- **Unlocks Next:** General hospital knowledge can be added as another real thread/message mode instead of a separate sample-only UI path.

### Phase 2: Add Safe General Hospital Knowledge Chat

- **Status:** Complete in this execution pass for curated approved non-PHI sources.
- **What Changes In Real Life:** Staff can ask hospital policy or operational questions that are not tied to a patient. The answer path is real, cites approved non-PHI sources, and does not require a patient permission gate.
- **Why This Phase Exists After Phase 1:** General chat should reuse the same persisted thread experience. Adding it before live thread wiring would create another disconnected path and make completion harder to verify.
- **Stories Inside This Phase:**
  - Story 1: Define the general-knowledge evidence boundary - decide which documents or records are approved for non-PHI retrieval and how they are marked.
  - Story 2: Backend general chat contract - allow general threads to accept messages through a real service path that cannot retrieve patient-linked evidence.
  - Story 3: Frontend general mode wiring - remove the documented-gap copy for general scope only after the backend contract exists.
  - Story 4: Safety tests - prove general chat never returns patient chunks and patient chat still requires permission.
- **Demo Walkthrough:** Create a general thread, ask a synthetic hospital policy question, and receive an answer with citations from approved general documents. Then attempt to retrieve patient-linked evidence through the general path and confirm it is refused or absent.
- **Unlocks Next:** The assistant now supports both top-level modes from D9, so HMS integration can focus on the first valuable patient-linked data slice.

### Phase 3: Connect The First HMS-Backed Data Slice

- **What Changes In Real Life:** The assistant can answer from one real HMS-derived data family, such as appointments, lab summaries, prescriptions, or a deliberately selected low-risk patient record slice, using synthetic or de-identified data in development.
- **Why This Phase Exists After General Chat:** HMS data introduces cross-system mapping and PHI rules. It should land after both conversation storage and general retrieval boundaries are already working.
- **Stories Inside This Phase:**
  - Story 1: Choose and document the first HMS data family - name the exact HMS source, fields, roles, exclusions, and permission requirement.
  - Story 2: Build import or API contract - move data into this backend through an explicit path; do not depend on removed HMS internal-assistant endpoints.
  - Story 3: Index and cite HMS-derived evidence - preserve source identity, patient identity, document/page/chunk lineage where applicable, and UI evidence fidelity.
  - Story 4: Permission adversarial tests - cover revoked permission, mismatched patient ownership, deleted source records, and unauthorized sharing.
- **Demo Walkthrough:** Load synthetic HMS-derived records for one patient, ask an authorized patient-linked question, inspect the cited evidence, then remove permission and confirm the same question creates no answer and no LLM evidence context.
- **Unlocks Next:** The project has a real hospital-data story instead of only UI and generic RAG capability.

### Phase 4: Hardening, Review, UAT, And Release Docs

- **What Changes In Real Life:** The project has evidence that it works end to end, knows its remaining limits, and is safe enough to present as complete for this milestone.
- **Why This Phase Closes The Feature:** Final review must happen after the real paths are implemented; otherwise the project can pass tests while the most important workflows are still mock-only.
- **Stories Inside This Phase:**
  - Story 1: Verification gate - run backend tests, frontend workspace tests, typecheck, lint, build, compile, and any available PostgreSQL/pgvector checks.
  - Story 2: Browser and accessibility QA - capture desktop/mobile evidence for chat, persistence, general mode, patient mode, denied states, and evidence panels.
  - Story 3: Docs and runbooks - update README, backend/frontend env instructions, API notes, safety limitations, and UAT checklist.
  - Story 4: Khuym review and fix loop - run review, fix P1 findings, record P2/P3 follow-ups, and only then close the completion milestone.
- **Demo Walkthrough:** A reviewer starts the stack from docs, signs in with a seeded token, completes the general and patient-linked demos, sees correct refusal behavior, verifies persisted history, and can trace every citation to allowed evidence.
- **Unlocks Next:** Later Kotaemon surfaces like knowledge management, uploads, settings, admin dashboards, and metrics can become separate follow-up epics.

---

## 6. Phase Order Check

- [x] Phase 1 is obviously first because the frontend already has adapters but does not use them.
- [x] Each later phase depends on or benefits from the one before it.
- [x] No phase is only a technical bucket; each phase changes what a staff user or reviewer can actually prove.
- [x] The plan preserves D1-D12: Kotaemon-first UI, chat-first entry, HMS as data/domain reference, visible patient gating, and no fake real hospital data.

---

## 7. Approval Summary

- **Current phase status:** Phase 1 through Phase 4 automated execution is complete.
- **What the user should picture now:** the chat workspace uses real backend thread data, saved patient-linked answers, safe general hospital knowledge answers, and one HMS appointment summary evidence path with permission-filtered citations.
- **What remains outside code execution:** human UAT sign-off, production auth/session replacement for dev bearer tokens, and non-blocking source-provider follow-up work.

Planning has broken the remaining work into phases and stories. Phase 1 and Phase 2 have now been executed from this plan.

## 8. Execution Update - 2026-04-28

- [x] Phase 1 complete: the frontend shell now loads persisted backend threads, exposes runtime backend URL and bearer-token configuration, creates/renames/archives/shares threads, and submits questions through `askBackendThreadMessage`.
- [x] Phase 2 complete: general chat-thread messages now use approved non-PHI general hospital knowledge, return citations when evidence matches, and return an honest no-evidence answer otherwise.
- [x] Safety verification added: backend tests prove general chat stores no patient ID, creates no `AiQuery`, marks citations as approved non-PHI, and does not return patient-linked chunks when patient documents exist.
- [x] Phase 3 complete: HMS appointment summaries are imported through an explicit backend contract, indexed as patient-linked evidence, and cited only after permission-filtered retrieval.
- [x] Phase 4 complete for automated hardening: backend/frontend verification passed, release docs were updated, review follow-up fixes were applied, and seeded UAT steps were recorded.
- [ ] Human UAT sign-off remains external to code execution.

## 9. Execution Update - 2026-04-28 Phase 3/4

- [x] Selected first HMS data family: appointment summaries from the HMS appointment API/entity surface.
- [x] Added `POST /api/v1/hms/appointments/import` for synthetic/de-identified appointment summaries.
- [x] Preserved source lineage in citation metadata: HMS source system, source family, source record ID, source path, lifecycle state, and permission requirement.
- [x] Added adversarial tests for patient ownership mismatch, revoked permission, deleted HMS source records, invalid citations, and no orphaned messages.
- [x] Hardened frontend token handling, thread detail loading, derived patient contexts, safe client errors, and inert controls.
- [x] Updated backend/frontend docs, API integration docs, test plan, and seeded UAT evidence.
