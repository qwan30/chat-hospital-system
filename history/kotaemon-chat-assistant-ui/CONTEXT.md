# Kotaemon-First Chat Assistant UI - Context

**Feature slug:** kotaemon-chat-assistant-ui
**Date:** 2026-04-28
**Exploring session:** complete
**Scope:** Standard

---

## Feature Boundary

Build the Phase 1 frontend direction for a Kotaemon-like collaborative hospital chatbot: a chat-first assistant workspace that can answer from general hospital knowledge and permission-gated patient-linked data, while deferring broader knowledge-base management and admin surfaces.

**Domain type(s):** SEE

---

## Locked Decisions

These are fixed. Planning must implement them exactly. No creative reinterpretation.

### Source of Truth and Product Direction

- **D1** The frontend is Kotaemon-first for UI structure, layout, interaction model, and chatbot behavior.
  *Rationale: The user explicitly corrected the direction away from HMS UI reuse and toward Kotaemon as the complete frontend reference.*

- **D2** The main first screen is a chat-first assistant workspace, not a dashboard, upload page, or document-management screen.
  *Rationale: Users should open directly into asking hospital or clinical questions with visible citations and source evidence.*

- **D3** `D:\projects\hospital-management-system` is the hospital data and domain integration reference, not the UI reference.
  *Rationale: The chatbot must support information saved in the HMS database, while Kotaemon guides function and frontend experience.*

- **D4** Planning must use the local Kotaemon repo at `D:\projects\kotaemon` as the direct UI reference.
  *Rationale: The user selected a local folder source over remote GitHub or screenshots-only references.*

- **D12** Planning may directly copy/adapt Kotaemon UI code and assets where practical.
  *Rationale: Compatible Kotaemon UI code/assets should be reused when useful; incompatible pieces should be rebuilt to fit this repo's stack and hospital requirements.*

### Phase 1 Scope

- **D5** The long-term direction is to adapt the full Kotaemon UI experience, but Phase 1 is limited to the chat workspace: conversation layout, prompt input, answer rendering, citations, and source/evidence panels.

- **D8** Phase 1 should support shared chat threads: multiple staff users can view or use the same conversation history.
  *Rationale: Collaboration means shared chat threads in this slice, not full team/workspace knowledge administration.*

- **D11** Phase 1 explicitly excludes knowledge-base management screens, settings, admin dashboards, and document upload/indexing UI.
  *Rationale: These are later slices and must not expand the first implementation plan.*

### Data and Permission Behavior

- **D6** Phase 1 uses a hybrid data strategy: real API contracts where available or verifiable, with clearly marked local mock data only for missing backend/HMS pieces.
  *Rationale: The UI can progress before all integrations are complete, but no mock may be presented as real hospital data.*

- **D9** The assistant may answer from both general hospital knowledge and patient-linked clinical data, but patient-linked data must be visibly permission-gated.
  *Rationale: General knowledge can be searched normally; patient data requires explicit patient/context selection and permission validation before answers or citations include it.*

### Design and Documentation

- **D7** Planning must verify and edit relevant project docs before implementation.
  *Rationale: `docs/design` and affected feature docs must be aligned with the Kotaemon-first direction before execution starts.*

- **D10** Use a balanced visual direction: Kotaemon defines structure and interactions; Linear guides the dark shell and density; Notion-lite guides answer/source reading surfaces; Vercel dashboard styling is deferred for later admin or metrics screens.

### Agent's Discretion

Planning may decide the exact component breakdown, routing shape, responsive breakpoints, and which Kotaemon code/assets are practical to copy, as long as those choices preserve D1-D12 and do not add out-of-scope screens.

---

## Specific Ideas & References

- The desired app should feel like a Kotaemon-style collaborative chatbot rather than a hospital dashboard.
- The chat workspace should make citations and source/evidence inspection first-class, because hospital answers need traceable evidence.
- The UI should use this repo's `docs/design` as a quality layer, not as a replacement for Kotaemon's interaction model.
- The HMS repo supplies hospital domain information and database concepts that the chatbot should eventually support.

---

## Existing Code Context

From the quick codebase scout during exploring.
Downstream agents: read these files before planning to avoid reinventing existing patterns.

### Current Chatbot-Hospital Frontend

- `app/frontend/src/app/page.tsx` - currently renders `HospitalDashboard` as the only app screen.
- `app/frontend/src/components/hospital-dashboard.tsx` - current dashboard-style prototype with patient worklist, query form, metrics, chart, and cited answer draft. This is not the desired Kotaemon-first structure, but it shows existing shadcn-style components and dependencies already in use.
- `app/frontend/src/components/ui/` - existing local primitives for button, card, input, label, table, and badge.
- `app/frontend/package.json` - Next.js 16, React 19, Tailwind CSS v4, shadcn-style primitives, TanStack Table, React Hook Form, Zod, Recharts, Motion, and Lucide are already available.

### Current Chatbot-Hospital Backend

- `app/backend/src/hospital_ai/api/routes/chat.py` - current POST chat endpoint that accepts a patient-scoped question and returns an answer.
- `app/backend/src/hospital_ai/schemas/chat.py` - current chat request/response shape with `patient_id`, `question`, `top_k`, `answer`, `citations`, `confidence`, and disclaimer.
- `app/backend/src/hospital_ai/services/chat.py` - current answer-generation service.
- `app/backend/src/hospital_ai/services/retrieval.py` - retrieval path that feeds evidence into chat.
- `app/backend/src/hospital_ai/services/permissions.py` - permission checks that matter for D9.

### Kotaemon Local Reference

- `D:\projects\kotaemon\libs\ktem\ktem\pages\chat\__init__.py` - main Kotaemon chat page assembly, including chat panels, info panels, suggestions, citations/PDF interactions, and conversation behavior.
- `D:\projects\kotaemon\libs\ktem\ktem\pages\chat\control.py` - conversation control surface with chat sessions, share-conversation option, rename/delete/new actions, dark-mode toggle, and expansion controls.
- `D:\projects\kotaemon\libs\ktem\ktem\pages\chat\chat_panel.py` - chat panel component reference.
- `D:\projects\kotaemon\libs\ktem\ktem\app.py` - app shell lifecycle and asset loading.
- `D:\projects\kotaemon\libs\ktem\ktem\assets\css\main.css` - Kotaemon layout and chat-area styling.
- `D:\projects\kotaemon\libs\ktem\ktem\assets\icons\` - reusable icon assets for conversation controls if compatible.

### Hospital-Management-System Reference

- `D:\projects\hospital-management-system\docs\HMS_PRD.md` - product roles and journeys to verify hospital domain intent.
- `D:\projects\hospital-management-system\docs\HMS_SRS.md` - functional requirements to verify supported clinical and operational data.
- `D:\projects\hospital-management-system\docs\API_ENDPOINTS_COMPREHENSIVE.md` - API capability inventory for integration planning.
- `D:\projects\hospital-management-system\API_CONTRACT.md` - integration contract reference.
- `D:\projects\hospital-management-system\backend\` - backend source to verify actual patient, permission, record, appointment, lab, prescription, role, and auth behavior when docs conflict.

---

## Canonical References

Downstream agents MUST read these before planning or implementing.

- `D:\projects\kotaemon` - primary frontend UI, layout, interaction, and chatbot behavior reference.
- `docs/design/README.md` - local design-reference map.
- `docs/design/core-ui-linear.md` - shell density, dark product workspace, spacing, and interaction polish reference.
- `docs/design/document-notion-lite.md` - answer/source reading surface reference.
- `docs/design/dashboard-vercel.md` - dashboard/admin/metrics reference only for later slices, not Phase 1 chat workspace.
- `D:\projects\hospital-management-system\docs\HMS_PRD.md` - hospital domain intent.
- `D:\projects\hospital-management-system\docs\HMS_SRS.md` - hospital functional requirement reference.
- `D:\projects\hospital-management-system\docs\API_ENDPOINTS_COMPREHENSIVE.md` - HMS API inventory.
- `D:\projects\hospital-management-system\API_CONTRACT.md` - HMS contract reference.
- `history/learnings/critical-patterns.md` - RAG/permission safety patterns that must shape patient-linked answer UX and validation.

---

## Outstanding Questions

### Resolve Before Planning

No product decisions remain unresolved from exploring.

### Deferred to Planning

- [ ] Determine which Kotaemon UI code/assets are directly reusable in a Next.js/Tailwind frontend and which must be rebuilt.
- [ ] Verify the current `chatbot-hospital-system` backend contract against the Phase 1 shared-thread and permission-gated patient-data requirements.
- [ ] Verify the HMS database/domain information that should be exposed to the chatbot in Phase 1, and update affected docs before implementation.
- [ ] Decide the exact docs to edit so `docs/design` and feature documentation reflect D1-D12 before execution starts.
- [ ] Resolve the Khuym/gkg tooling gap before gkg-backed planning if possible. `gkg` was not found on PATH during exploring.

---

## Deferred Ideas

- Full Kotaemon app shell beyond chat workspace - later slice after Phase 1.
- Knowledge-base management screens - later slice.
- Settings screens - later slice.
- Admin dashboards and metrics - later slice, where `docs/design/dashboard-vercel.md` can become relevant.
- Document upload/indexing UI - later slice unless planning proves a minimal control is required for Phase 1 testing.
- Team-level knowledge collections and advanced workspace permissions - later collaboration slice.

---

## Handoff Note

CONTEXT.md is the single source of truth for this feature.

- **planning** reads: locked decisions, code context, canonical refs, deferred-to-planning questions
- **validating** reads: locked decisions to verify plan-checker coverage
- **reviewing** reads: locked decisions for UAT verification

Decision IDs (D1-D12) are stable. Reference them by ID in all downstream artifacts.
