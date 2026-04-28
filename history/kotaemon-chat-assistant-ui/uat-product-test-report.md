# Product UAT Report - Kotaemon Chat Assistant UI

**Date:** 2026-04-28
**Runner:** Codex product UAT pass
**Runtime:** FastAPI on `http://127.0.0.1:8000`, existing Next.js dev server on `http://localhost:3000`
**Data:** synthetic/de-identified seed data only

## Verdict

Agent-run product UAT is pass after one scoped P1 fix.

| Severity | Count | Status |
|---|---:|---|
| P1 block | 1 found, 1 fixed | Clear |
| P2 fix before sign-off | 4 manual end-user findings, 4 fixed | Clear |
| P3 follow-up | 1 existing + 3 manual end-user findings | `br-2o5` general knowledge provider abstraction remains deferred; manual UX follow-ups recorded |

Human sign-off is still the final external gate. After the manual end-user pass on 2026-04-29, the P2 feedback below was fixed and covered by targeted regression checks.

## Manual End-User Browser Feedback - 2026-04-29

Manual Chrome/Playwright review was run as a hospital end user against `http://localhost:3000` with the FastAPI backend on `http://127.0.0.1:8000`, using synthetic UAT data and `dev-doctor`.

Evidence screenshots are in `history/kotaemon-chat-assistant-ui/uat-evidence/manual-end-user-20260429/`.

| Severity | Feedback | Evidence | Expected before sign-off |
|---|---|---|---|
| P2 fix before sign-off | The Archive action succeeds at the API level, but the archived thread remains visible in the active conversation list as `Backend persisted` and remains selected after refresh. | `manual-feedback-archive-still-visible.png`; API response shows the thread status is `archived`. | Archived threads should be removed from the default active list or clearly labeled and moved out of the active workflow. |
| P2 fix before sign-off | Patient-linked answers cite HMS appointment evidence, but the assistant answer itself is generic: "relevant clinical details in [E1]" instead of directly answering appointment status and vital signs. | `manual-feedback-doctor-alice-hms.png` | The answer should summarize the status and vital signs from the cited appointment evidence, with the citation still visible. |
| P2 fix before sign-off | The patient-allowed state still shows a red warning that "Patient-linked evidence remains gated" and says evidence is unavailable, even while authorized HMS evidence is visible. | `manual-feedback-doctor-alice-hms.png` | The warning should switch to an allowed-state message once patient permission is validated, or only appear for denied/pending states. |
| P2 fix before sign-off | Clicking `New conversation` while a patient scope is active immediately creates a persisted patient-linked thread with a technical title, without confirming scope. | `manual-feedback-archive-still-visible.png` | New conversation should make the target scope explicit before creating patient-linked persisted data. |
| P3 follow-up | The unauthenticated and wrong-token screens still show local sample patient labels such as Alice and Bob. These are synthetic, but the screen feels like it is exposing patient context before login. | `manual-feedback-initial-no-token.png`, `manual-feedback-wrong-token.png` | Production auth should hide patient examples until authenticated, or label them as demo-only in a non-production build. |
| P3 follow-up | Mobile layout is usable and has no incoherent overlap, but the conversation list and evidence panel are far below the chat composer. Switching threads on mobile is slow. | `manual-feedback-mobile.png` | Consider a mobile drawer or tabs for conversations and evidence. |
| P3 follow-up | Wrong-token attempts create expected browser console/network 401 errors. The user-facing error is sanitized and no token is persisted. | Browser console/network capture | Acceptable for UAT; noisy for QA but not user-visible. |

Manual end-user verdict: no new P1 blocker was found. The P2 items above were fixed in the follow-up pass below.

## Issue Found And Fixed

| Severity | Finding | Evidence | Fix | Rerun result |
|---|---|---|---|---|
| P1 block | Browser requests from `http://localhost:3000` to `http://localhost:8000` were blocked by CORS, so the frontend could not load persisted backend threads. | Playwright console showed `No 'Access-Control-Allow-Origin' header` on `/api/v1/chat-threads`. | Added FastAPI `CORSMiddleware` with explicit local UAT origins and documented `HOSPITAL_AI_CORS_ORIGINS`. | Browser refresh with `dev-doctor` loaded persisted backend threads with no new console errors. |
| P2 fix before sign-off | Archived conversations remained visible in the default active conversation list after archive. | `manual-feedback-archive-still-visible.png` | Backend `list_threads` and frontend thread hydration now keep the default list to `active` threads. | `tests/test_chat_thread_messages_api.py::test_archived_threads_are_hidden_from_default_thread_list` passed. |
| P2 fix before sign-off | Stub patient-linked HMS answers cited appointment evidence but did not state the requested status and vital signs. | `manual-feedback-doctor-alice-hms.png` | Stub grounded answers now extract `Status` and `Vital signs` lines from authorized evidence and cite them. | `tests/test_hms_appointment_import.py::test_hms_appointment_import_becomes_permission_filtered_patient_evidence` passed. |
| P2 fix before sign-off | Allowed patient context showed contradictory red gated-evidence warning while authorized evidence was visible. | `manual-feedback-doctor-alice-hms.png` | Evidence panel boundary copy now switches by permission state and shows `Patient evidence allowed` for allowed contexts. | `npm.cmd run test:workspace` passed. |
| P2 fix before sign-off | `New conversation` could create a patient-linked persisted thread without explicit scope confirmation. | `manual-feedback-archive-still-visible.png` | Patient-linked thread creation now asks for explicit confirmation before backend persistence. | `npm.cmd run test:workspace` passed. |

## API UAT Scenarios

Source artifact: `history/kotaemon-chat-assistant-ui/uat-evidence/20260428T170614Z/api-uat-summary.md`

| Scenario | Roles | Result |
|---|---|---|
| Auth and no-token boundary | anonymous, wrong token, `dev-doctor`, `dev-records`, `dev-security`, `dev-admin` | Pass |
| General knowledge thread answer | `dev-doctor` | Pass |
| HMS appointment import role boundary | `dev-records`, `dev-doctor` | Pass |
| Patient-linked HMS appointment answer | `dev-doctor` | Pass |
| Denied patient access and audit trace | `dev-records`, `dev-security`, `dev-doctor` | Pass |
| Shared thread rename, share, reload, archive | `dev-doctor`, `dev-admin` | Pass |

## Browser UAT Evidence

Artifacts are in `history/kotaemon-chat-assistant-ui/uat-evidence/20260428T170614Z/`.

| Artifact | Scenario | Result |
|---|---|---|
| `uat-desktop-thread-load.png` | Desktop doctor reload after CORS fix | Persisted threads load; patient-linked HMS evidence is visible for authorized doctor context |
| `uat-desktop-general-answer.png` | Desktop general knowledge message | Approved non-PHI citation is visible in transcript and source panel |
| `uat-mobile-general-answer.png` | Mobile responsive smoke | Chat, sidebar, composer, and evidence panel remain usable without incoherent overlap |
| `uat-desktop-wrong-token-denied.png` | Wrong token denied state | UI shows sanitized auth failure and no seeded PHI terms; token remains memory-only |

## Verification Commands

```bash
cd app/backend
python -m compileall src tests scripts
python -m pytest

cd app/frontend
npm run test:workspace
npm run typecheck
npm run lint
npm run build
```

Additional targeted rerun after the CORS fix:

```bash
cd app/backend
python -m pytest tests/test_cors.py
```

Additional targeted rerun after the manual P2 fixes:

```bash
cd app/backend
python -m pytest tests/test_chat_thread_messages_api.py tests/test_hms_appointment_import.py

cd app/frontend
npm.cmd run test:workspace
```

## Remaining Follow-Up

- `br-2o5` remains P3: move approved general knowledge sources behind a provider or repository boundary before expanding source families.
- Production auth/session handling remains outside this UAT wave; current validation uses explicit dev bearer tokens.
