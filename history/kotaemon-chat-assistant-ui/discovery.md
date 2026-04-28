# Discovery - Kotaemon-First Chat Assistant UI

**Feature:** kotaemon-chat-assistant-ui
**Date:** 2026-04-28
**Skill:** khuym:planning
**Status:** Phase 1 and Phase 2 execution complete with degraded gkg/bd tooling

## Completion Planning Refresh - 2026-04-28

This discovery file originally supported Phase 1 planning. It has been refreshed for completion planning from the current repo state.

### Current shipped or implemented capabilities

| Area | Current state | Planning impact |
|---|---|---|
| Chat-first frontend shell | Implemented under `app/frontend/src/components/chat` and rendered from the root route | Keep the Kotaemon-first shell; do not restart from the old dashboard direction. |
| Active workspace model | `AssistantShell` owns active persisted thread, patient context, composer state, and evidence source derivation | Later phases should preserve one parent-owned active state model. |
| Frontend backend adapter | `app/frontend/src/lib/chat-assistant/api.ts` maps persisted backend threads, messages, participants, citations, and evidence | Later UI work should reuse this adapter instead of inventing a second API layer. |
| Backend chat threads | `app/backend/src/hospital_ai/api/routes/chat_threads.py` and `services/chat_threads.py` support thread CRUD, messages, participants, audit, and permission guards | Phase 2 backend persistence is no longer a blank gap; the remaining gap is frontend live wiring and general-mode support. |
| Patient-linked thread messages | Patient-linked thread message creation calls `ChatService.answer`, persists user and assistant messages, links `ai_query_id`, stores citations, and updates `last_message_at` | Patient-linked live submit is wired through the frontend shell. |
| General thread messages | `ChatThreadService.ask_thread_message` answers general threads through approved non-PHI sources | General chat is implemented; source expansion remains future work. |
| HMS integration | HMS remains only a domain/data reference and no connected import/API path exists here | A later phase must choose one supported HMS data family and preserve permission/evidence traceability. |

### Tooling refresh

`gkg index D:\projects\chatbot-hospital-system` and `gkg server start` were attempted during this planning pass, but `gkg` is not on PATH. `br.exe` exists but `br ready --json` fails with `JSON_ERROR` because the Beads store expects a missing `jsonl_export` field. `bv --robot-next --graph-root br-dyy` works and reports no actionable items available. `npx.cmd bd ready --json` and `npx.cmd gitnexus status` did not resolve their underlying binaries in this shell.

Completion planning therefore used direct file inspection and checked-in Khuym state as the discovery source. Bead creation remains blocked until the Beads CLI path/store issue is fixed or a deliberate `bd`/`br` migration is performed.

### Completion gaps found

1. HMS-derived data is not connected to the chatbot backend.
2. Final Khuym review, UAT, browser evidence for seeded live data, and release docs are not done.
3. Production auth/session handling remains separate from the current dev bearer-token flow.

## Institutional Learnings

### Critical patterns used

| Learning | Why it matters here |
|---|---|
| RAG Evidence Requires Full Join-Chain Authorization | Patient-linked answers and citation panels must not treat a patient permission check as enough. Evidence must stay permission-filtered across patient, document, page, and chunk ownership before reaching the UI or LLM context. |
| Raw SQL Permission Policy Needs an Executable Contract | Any future backend work for shared threads, citations, or HMS data import must keep raw SQL permission predicates aligned with the canonical permission helpers and tests. |
| Migration Chains Need One Schema Source of Truth | Shared-thread, metric, or conversation-history tables must be added through forward migrations only, not by back-editing base migrations. |
| Degraded Khuym Runs Need Durable State Immediately | `gkg`, `br`, `bv`, `cass`, and `cm` are unavailable in this session, so findings and blockers are written to Khuym state and history files. |

### Domain learning read

- `history/learnings/20260428-backend-permission-rag-safety.md`

This learning is directly applicable because Phase 1 exposes patient-linked evidence and later phases will persist or share conversation history that may reference patient-specific citations.

## Tooling Readiness

`node .codex/khuym_status.mjs --json` reports that this repo is supported for `gkg`, but the project is not indexed and the gkg server is unreachable. `gkg` is not available on PATH, and `npx gkg` cannot determine an executable. Discovery therefore used direct file inspection through PowerShell instead of graph-backed analysis.

The planning skill also declares `br`, `bv`, `cass`, and `cm`. These commands are not available in the current shell, so bead creation and prior-session CLI search are blocked until tooling is installed or configured. This phase stops at the phase-plan approval gate, so no beads were attempted.

## Architecture Topology

### Chatbot hospital system

| Area | Current state | Planning implication |
|---|---|---|
| `app/frontend` | Next.js 16, React 19, Tailwind 4, shadcn-style primitives, Lucide, Recharts, TanStack Table, Motion | Good base for a React rebuild of the Kotaemon chat workspace. |
| `app/frontend/src/app/page.tsx` | Renders `HospitalDashboard` as the only screen | Conflicts with D2. Phase 1 must replace the first screen with a chat workspace. |
| `app/frontend/src/components/hospital-dashboard.tsx` | Dashboard-style prototype with metrics, patient table, query form, and cited answer card | Reusable only as primitive/reference material, not as the target information architecture. |
| `app/frontend/src/components/ui` | Existing button, card, input, label, table, badge primitives | Reuse and extend rather than introduce a second UI system. |
| `app/frontend/src/app/globals.css` | Dark Linear-like CSS variables already exist | Aligns with D10 and reduces styling risk. |
| `app/backend` | FastAPI backend with patient-scoped chat, retrieval, permissions, audit, and tests | Good permission foundation, but it does not yet support shared chat threads or general non-patient questions. |

### Current backend contract

The current chat endpoint accepts a `patient_id`, `question`, and `top_k`, then returns an answer, citations, confidence, and disclaimer. The service checks patient scope before retrieval, retrieves permission-filtered evidence, validates citation markers, records query/evidence rows, and logs audit events.

Gaps against locked decisions:

- Shared conversation threads are not modeled. `AiQuery` stores individual asks, not collaborative thread/message history.
- General hospital knowledge is not a first-class request path because `patient_id` is required by the current schema.
- The frontend must clearly mark any local thread or general-knowledge data as mock until backend contracts exist.

## Existing Patterns To Reuse

| Pattern | Source | Reuse direction |
|---|---|---|
| Permission-first patient retrieval | `app/backend/src/hospital_ai/services/permissions.py` and `retrieval.py` | Preserve as the backend safety source for patient-linked evidence. |
| Citation validation | `app/backend/src/hospital_ai/services/chat.py` and tests | Keep answer blocks citation-aware and no-evidence aware. |
| Audit on denied access | Backend permission and chat tests | Surface denied states in UI and keep trace/audit language ready. |
| shadcn-style primitives | `app/frontend/src/components/ui` | Build chat components outside `ui/` and compose primitives. |
| Dark shell tokens | `app/frontend/src/app/globals.css` and `docs/design/core-ui-linear.md` | Use for dense chat workspace shell. |

## Kotaemon Reference Findings

The local Kotaemon repo at `D:\projects\kotaemon` is the primary UI/function reference, but it is a Python/Gradio application. It cannot be copied into this Next.js app as a drop-in frontend. It should be translated into React components while reusing concepts, interaction structure, CSS ideas, and compatible assets.

| Kotaemon file | Relevant behavior |
|---|---|
| `libs/ktem/ktem/pages/chat/__init__.py` | Assembles the main chat page with conversation settings panel, chat area, info panel, citation dropdown, suggestions, answer streaming, and source interactions. |
| `libs/ktem/ktem/pages/chat/control.py` | Conversation list, active conversation selection, new/delete/rename actions, dark-mode toggle, expand control, and share-conversation affordance. |
| `libs/ktem/ktem/pages/chat/chat_panel.py` | Chat transcript and multimodal prompt input pattern. |
| `libs/ktem/ktem/assets/css/main.css` | Layout conventions for chat area, info panel, citation dropdown, and message citations. |
| `libs/ktem/ktem/assets/icons` | Potential direct asset reuse for sidebar/action controls if licensing and format are acceptable. |
| `libs/ktem/ktem/db/base_models.py` | Conversation model with `is_public` and JSON `data_source`; useful conceptually for shared threads, but not a direct schema to copy. |

Kotaemon quick upload, knowledge-base management, settings, and broader admin surfaces are intentionally out of scope for Phase 1.

## HMS Reference Findings

`D:\projects\hospital-management-system` is a data/domain reference, not a UI reference. Its docs and source describe the hospital roles, operational workflows, clinical records, appointments, labs, prescriptions, inventory, finance, patient portal, and RBAC concepts that the chatbot should eventually understand.

Important boundary: current HMS documentation records that previous AI/internal assistant endpoints were removed or deprecated. The chatbot plan must not depend on removed HMS endpoints such as internal assistant APIs or admin knowledge-document APIs. HMS should inform data mapping and integration contracts, while this repository owns the chatbot assistant experience.

## Documentation Drift Found

The project docs previously described the app as dashboard-first, with Home Dashboard, Documents, Metrics, Audit, and Admin Settings in the main information architecture. That conflicts with D2 and D11.

Updated during this planning pass:

- `docs/04_ui_ux_design_package.md` now states chat-first Kotaemon direction, Phase 1 scope, deferred surfaces, patient context gate, evidence panel, and shared-thread UX.
- `docs/10_design_system_and_metrics.md` now aligns design tokens and core components with Kotaemon + Linear + Notion-lite instead of a dashboard-first system.

## Constraints

| Constraint | Impact |
|---|---|
| No real PHI or secrets | Demos and local data must remain synthetic or explicitly de-identified. |
| Permission filters before retrieval context | UI cannot imply patient evidence is available before permission validation. |
| Kotaemon stack mismatch | Rebuild in React/Next; direct code reuse is limited. |
| Shared threads absent in backend | Phase 1 must either use marked mock/local state or plan backend thread work for Phase 2. |
| General knowledge path absent in current backend schema | General hospital knowledge must be represented as a planned contract gap until implemented. |
| `gkg`, `br`, `bv`, `cass`, `cm` unavailable | Planning is degraded and bead creation is blocked until tools are installed or configured. |

## Open Questions For Validation

No product direction remains unresolved, but validation should spike these technical questions before execution:

1. What is the minimal thread/message contract that supports shared conversations without leaking patient evidence?
2. Should Phase 1 call the current patient-scoped `/chat` endpoint or stay UI-only until thread/general-knowledge contracts exist?
3. Which Kotaemon icon/CSS assets are license-compatible and practical to copy?
4. What HMS data families are safe and useful for the first real patient-linked assistant integration?
