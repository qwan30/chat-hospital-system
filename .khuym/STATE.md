# STATE
focus: Kotaemon-first chat assistant UI completion
phase: phase-1-and-2-executed
last_updated: 2026-04-28

## Current State

Skill: executing
Feature: kotaemon-chat-assistant-ui
Epic: `br-dyy`
Plan Gate: approved by user in the 2026-04-28 execution request
Execution Gate: Phase 1 and Phase 2 complete
Current Phase To Prepare Next: Phase 3 - Connect the first HMS-backed data slice

Phase 1 live frontend wiring is complete: the root chat workspace loads persisted backend threads, uses explicit backend URL and bearer-token controls, maps thread details into one active workspace state, and wires create, rename, archive, share, and thread-message submission actions.

Phase 2 safe general hospital knowledge is complete for curated approved non-PHI sources: general chat-thread messages use a backend service that does not query patient chunks, returns cited approved sources when evidence matches, and returns an honest no-evidence answer otherwise.

## Artifacts Updated

- `app/frontend/src/components/chat/AssistantShell.tsx`
- `app/frontend/src/lib/chat-assistant/api.ts`
- `app/backend/src/hospital_ai/services/chat_threads.py`
- `app/backend/src/hospital_ai/services/general_knowledge.py`
- `app/backend/tests/test_chat_thread_messages_api.py`
- `app/frontend/scripts/verify-chat-workspace-state.mjs`
- `history/kotaemon-chat-assistant-ui/discovery.md`
- `history/kotaemon-chat-assistant-ui/approach.md`
- `history/kotaemon-chat-assistant-ui/phase-plan.md`

## Verification Summary

- Backend: `python -m pytest` passed with `48 passed, 2 skipped`.
- Backend compile: `python -m compileall src tests` passed.
- Frontend workspace contract: `npm run test:workspace` passed with `12` tests.
- Frontend: `npm run typecheck`, `npm run lint`, and `npm run build` passed.
- Browser smoke: Playwright loaded `http://localhost:3000` with no console warnings/errors.

## Tooling Notes

- `gkg index D:\projects\chatbot-hospital-system` was attempted, but `gkg` is not on PATH.
- `br.exe` and `bv.exe` are on PATH.
- `br ready --json` still fails with `JSON_ERROR` because the Beads store expects a missing `jsonl_export` field.
- `bv --robot-next --graph-root br-dyy` works and reports no actionable items.

## Remaining Gaps

- HMS integration remains unimplemented.
- Final Khuym review, UAT, browser evidence against a seeded live backend, and release docs remain pending.
- Production auth/session handling is not implemented; the frontend uses explicit dev bearer-token configuration.

## Next

Prepare Phase 3 with validation before implementation. Choose one HMS-backed data family, define fields and exclusions, prove permission/evidence lineage, then implement that slice.
