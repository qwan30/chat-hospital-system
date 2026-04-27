# Approach - Kotaemon-First Chat Assistant UI

**Feature:** kotaemon-chat-assistant-ui
**Date:** 2026-04-28
**Skill:** khuym:planning
**Status:** Ready for phase-plan approval

## Gap Analysis

| Requirement | Current reality | Gap | Risk |
|---|---|---|---|
| First screen is chat-first assistant | `page.tsx` renders `HospitalDashboard` | Replace first screen with a Kotaemon-style chat workspace | Medium |
| Kotaemon-like conversation layout | No React chat shell exists | Build sidebar, transcript, composer, evidence panel, and patient context gate | Medium |
| Shared chat threads | Backend stores individual `AiQuery` records only | Need thread/message model and sharing rules in a later phase | High |
| General hospital knowledge | Current chat schema requires `patient_id` | Need general-scope request path or UI-only marked mock until backend contract exists | High |
| Permission-gated patient data | Backend has strong patient permission and retrieval filters | UI must expose permission state and avoid presenting blocked evidence as available | Medium |
| Direct Kotaemon reuse | Kotaemon is Python/Gradio | Rebuild interaction model in React; reuse only compatible concepts/assets/CSS ideas | High |
| HMS data integration | HMS is separate Spring Boot system with removed internal assistant endpoints | Need explicit data mapping/import/API plan; do not depend on removed AI endpoints | High |
| Docs aligned before implementation | Docs were dashboard-first | `docs/04` and `docs/10` updated in planning; additional docs may need follow-up per phase | Low |
| Khuym tool graph | `gkg`, `br`, `bv`, `cass`, `cm` unavailable | Continue with durable state and local inspection; bead creation blocked until tooling works | Medium |

## Recommended Approach

Build the feature in slices that first make the product feel correct, then make collaboration and hospital data real.

Phase 1 should turn the opening app into a believable Kotaemon-style assistant workspace using the existing Next.js frontend and clearly marked local data for missing backend pieces. This is first because the user corrected the product direction toward Kotaemon UI/function, and the current dashboard-first screen is the largest visible mismatch. The backend already has strong patient-scoped permission patterns, so the UI should represent those states correctly without inventing fake hospital data.

Shared thread persistence and HMS data integration should come after the UI contract is visible. They are higher risk because they affect storage, permissions, audit behavior, and PHI leakage boundaries. Validating should spike those contracts before execution.

## Key Decisions

| Decision | Rationale |
|---|---|
| Rebuild Kotaemon in React rather than embedding Gradio | The local Kotaemon reference is Python/Gradio and cannot be dropped into a Next.js frontend. |
| Replace the dashboard entry with a chat workspace | Locked D2 requires the first screen to be chat-first. |
| Keep Phase 1 scoped to chat, citations, evidence, patient gate, and shared-thread affordances | Locked D5 and D11 defer KB management, upload/indexing, settings, and admin dashboards. |
| Use real backend contracts only where verified | Current patient-scoped `/chat` is real; shared threads and general knowledge are not yet real. |
| Make mock/local data visible as mock | Locked D6 forbids presenting local placeholders as real hospital data. |
| Treat HMS as domain/integration source, not frontend source | Locked D3 separates data reference from UI reference. |

## Verified Contract Inventory

The executable frontend inventory lives in `app/frontend/src/lib/chat-assistant/contracts.ts`. It separates fields and UI states into `verified-backend`, `local-sample-only`, and `documented-gap` categories so later shell and state beads do not present missing backend behavior as real.

| Capability | Current status | Verified source | Implementation boundary |
|---|---|---|---|
| Patient-scoped chat request/response | Verified backend | `app/backend/src/hospital_ai/api/routes/chat.py`, `app/backend/src/hospital_ai/schemas/chat.py` | Only call with selected `patient_id`; request fields are `patient_id`, `question`, `top_k`; response fields are `query_id`, `answer`, `citations`, `confidence`, `disclaimer`. |
| Citation evidence fields | Verified backend | `app/backend/src/hospital_ai/schemas/documents.py`, `app/backend/src/hospital_ai/services/retrieval.py` | UI may render returned evidence IDs, document IDs, document titles, pages, chunk IDs, scores, content, and metadata. |
| Patient permission expectation | Verified backend | `app/backend/src/hospital_ai/services/permissions.py`, `app/backend/src/hospital_ai/services/chat.py` | Patient-linked answers and citations stay blocked until read permission is allowed; denied state records audit and must not expose PHI evidence. |
| Shared conversation threads | Local/sample only | No current thread/message API or persistence contract | Sidebar/history/share affordances must be labeled local/sample until Phase 2 creates real persistence and sharing rules. |
| General hospital knowledge path | Documented gap | Current `ChatRequest` requires `patient_id` | General mode may exist as UI state only; no real backend citations should be implied until a general-scope API exists. |
| HMS integration data | Documented gap | HMS repo is a domain reference, not a connected source | HMS-derived patient, appointment, lab, prescription, or role details must be unavailable or marked local/sample until integration is verified. |

## Alternatives Considered

| Alternative | Rejected because |
|---|---|
| Copy Kotaemon frontend directly | Kotaemon uses Gradio/Python UI, not React/Next. Direct reuse is limited to assets, styling ideas, and behavior translation. |
| Extend the existing dashboard prototype | It conflicts with the chat-first first-screen requirement and would keep the wrong information architecture. |
| Build every Kotaemon surface now | Knowledge-base management, settings, upload/indexing, and admin dashboards are explicitly out of scope for Phase 1. |
| Integrate with HMS internal assistant endpoints | HMS docs mark those AI/internal-assistant endpoints as removed/deprecated. |
| Implement backend thread schema before any UI | The biggest visible product mismatch is UI direction, and a UI contract helps validate the exact backend shape needed. |

## Risk Map

| Component | Risk | Why | Validating action |
|---|---|---|---|
| Shared conversation threads | High | New persistence and sharing can leak patient-linked evidence if scoped badly | Spike thread/message contract and access rules before backend implementation |
| General plus patient-scoped chat contract | High | Current backend requires `patient_id`, while the product needs general hospital knowledge too | Spike API shape for general scope vs patient scope |
| HMS data integration | High | Separate system, different domain model, removed AI endpoints, possible PHI exposure | Map first supported HMS data families and permissions before implementation |
| Kotaemon-to-React translation | High | Interaction model is useful but implementation stack differs | Prototype component map and asset reuse list |
| Patient evidence display | Medium | Backend safety exists, UI must not imply unauthorized source availability | Add denied/no-evidence/loading states and tests |
| Docs alignment | Low | Docs are now corrected for the two primary UI docs | Keep future docs updated when backend contracts are prepared |
| Build/test pipeline | Medium | Frontend has typecheck/lint/build commands, but no UI E2E baseline yet | Run typecheck/build and add Playwright review when implementation starts |

## Proposed File Structure

Phase 1 should keep implementation in the frontend and docs:

```text
app/frontend/src/app/page.tsx
app/frontend/src/components/chat/AssistantShell.tsx
app/frontend/src/components/chat/ConversationSidebar.tsx
app/frontend/src/components/chat/ChatTranscript.tsx
app/frontend/src/components/chat/ChatComposer.tsx
app/frontend/src/components/chat/EvidencePanel.tsx
app/frontend/src/components/chat/PatientContextGate.tsx
app/frontend/src/components/chat/SourceCitation.tsx
app/frontend/src/components/chat/ThreadShareControls.tsx
app/frontend/src/lib/chat-assistant/types.ts
app/frontend/src/lib/chat-assistant/mock-data.ts
app/frontend/src/lib/chat-assistant/api.ts
docs/04_ui_ux_design_package.md
docs/10_design_system_and_metrics.md
history/kotaemon-chat-assistant-ui/*
```

Later backend phases may add:

```text
app/backend/src/hospital_ai/api/routes/conversations.py
app/backend/src/hospital_ai/schemas/conversation.py
app/backend/src/hospital_ai/services/conversations.py
app/backend/src/hospital_ai/db/models.py
app/backend/migrations/*
app/backend/tests/test_conversations.py
app/backend/tests/test_chat_general_scope.py
```

## Dependency Order

1. Align docs and phase plan so implementation is no longer dashboard-first.
2. Build the chat workspace shell and component boundaries in React.
3. Add typed local data/adapters that distinguish real contracts from mock gaps.
4. Add patient context and evidence states that mirror backend permission behavior.
5. Validate shared-thread and general-knowledge backend contracts before persistence work.
6. Integrate HMS data families only after the permission and thread model is explicit.

## Institutional Learnings Applied

| Learning | Applied decision |
|---|---|
| RAG evidence needs full join-chain authorization | Patient-linked citations must remain blocked until evidence has passed backend permission filtering. |
| Raw SQL permission policy needs an executable contract | Any new backend query for thread/citation history must reuse or test permission predicates. |
| Migration chains need one schema source of truth | Shared-thread and metric migrations should be forward-only and tested. |
| Optional production-path tests are not enough for PHI boundaries | PostgreSQL/pgvector or production-like tests should be required for backend retrieval changes even if local tests skip them. |
| Degraded Khuym runs need durable state | Planning records missing `gkg` and bead tooling in history and `.khuym` state. |
