# Phase Plan - Kotaemon-First Chat Assistant UI

**Feature:** kotaemon-chat-assistant-ui
**Date:** 2026-04-28
**Skill:** khuym:planning
**Plan Gate:** approved by user on 2026-04-28

## Feature Summary

This feature turns the application into a Kotaemon-style collaborative hospital assistant. Users should open the app directly into a chat workspace, ask general hospital or patient-linked questions, inspect cited evidence, and understand when patient data is blocked by permissions.

Kotaemon guides the interaction model. The hospital-management-system repo guides the data/domain model. This repository owns the assistant UI, backend contracts, permission-aware retrieval, and safe integration plan.

## Phase 1 - Make The First Screen A Kotaemon-Style Chat Workspace

### What changes for users

Opening the app shows a dense chat workspace instead of a dashboard. Staff see a conversation sidebar, central chat transcript, prompt composer, patient/context gate, answer citations, and a source/evidence panel. Any data that is not connected to a real backend contract is visibly marked as local/mock.

### Why this comes first

The current app opens into a dashboard, which is the largest mismatch with the locked direction. A correct chat workspace lets the team review the product shape before risky backend thread and HMS integration work begins.

### Stories

| Story | What happens | Done looks like |
|---|---|---|
| 1. Align docs and contract inventory | The docs and implementation plan say the same thing: Kotaemon-first, chat-first, Phase 1 scope only | `docs/04`, `docs/10`, discovery, and approach reflect D1-D12 |
| 2. Build the React chat workspace shell | The Next.js first screen becomes a Kotaemon-like shell | `page.tsx` renders chat workspace regions with responsive layout |
| 3. Add conversation, patient gate, and evidence states | The UI shows shared-thread affordances, patient permission state, citations, and source inspection | User can see general vs patient-linked scope and no mock is presented as real hospital data |
| 4. Verify the first-screen experience | Build/typecheck/design review confirm the screen is usable and not dashboard-first | Verification output records build results, responsive issues, and remaining backend gaps |

### Simplest demo

Start the frontend, open the root page, and land directly in the assistant workspace. Open a sample shared thread, switch between general and patient-linked scope, view an answer with citations, open a source in the evidence panel, and see any missing backend pieces labeled as local/mock.

### Unlocks next

The team can now validate the exact backend APIs needed for real shared threads and general/patient-scoped chat.

## Phase 2 - Make Shared Chat Threads Real And Safe

### What changes for users

Conversations are no longer just UI state. Staff can create, rename, delete, reopen, and share conversation threads with correct access controls and audit behavior.

### Why this comes after Phase 1

The UI shell defines what the thread model needs to support. Building persistence second avoids designing storage around the old dashboard prototype.

### Stories

| Story | What happens | Done looks like |
|---|---|---|
| 1. Define thread and message contract | Backend schema and API shape are explicit | Contract covers thread metadata, messages, sharing, patient context, and audit identifiers |
| 2. Persist and reload conversations | Threads survive page reload and can be selected from the sidebar | API tests cover create/list/read/update/delete |
| 3. Enforce sharing and PHI boundaries | Shared thread access is allowed only where safe | Unauthorized users cannot read patient-linked messages or citations |
| 4. Connect frontend to real thread APIs | Mock thread data is removed or kept only for dev fallback | UI uses real data for thread list and history |

### Simplest demo

Staff user A creates a thread and shares it. Staff user B with access can open the thread. A user without patient permission can see only allowed thread metadata or a blocked state, not patient evidence.

### Unlocks next

The system can safely attach real hospital knowledge and patient-linked data to collaborative conversations.

## Phase 3 - Connect Hospital Knowledge And HMS Data Safely

### What changes for users

The assistant can answer from real supported hospital knowledge and selected patient-linked data families, using HMS as the domain/reference source without depending on removed HMS AI endpoints.

### Why this comes after shared threads

Patient-linked answers and citations become more sensitive when saved and shared. The collaboration boundary should be safe before richer HMS data enters the assistant flow.

### Stories

| Story | What happens | Done looks like |
|---|---|---|
| 1. Map first HMS data families | Decide which HMS data can support assistant answers first | Mapping names exact HMS sources, permissions, fields, and excluded data |
| 2. Build the integration/import contract | Data reaches the chatbot backend through an explicit safe path | No dependency on removed HMS internal-assistant APIs |
| 3. Connect answer and citation UI to real evidence | UI shows real sources for supported data | Evidence panel displays source metadata from real indexed/linked records |
| 4. Prove permission and retrieval safety | Adversarial tests cover revoked, expired, mismatched, and unauthorized cases | No unauthorized chunks or patient data reach the LLM context |

### Simplest demo

Ask a general hospital question and receive cited evidence. Select an authorized patient and ask about supported records, labs, or appointment context. Then try the same patient-linked question without permission and see a blocked, audited state.

### Unlocks next

The assistant has the safe data foundation needed for broader Kotaemon-like management surfaces.

## Phase 4 - Expand Kotaemon Surfaces Beyond Chat

### What changes for users

After the chat assistant is real, later Kotaemon-like surfaces can be added: knowledge-base management, document indexing/upload, settings, and admin/metrics dashboards.

### Why this comes last

These surfaces are explicitly out of scope for Phase 1. They are useful only after the core assistant, collaboration, and patient-data safety are working.

### Stories

| Story | What happens | Done looks like |
|---|---|---|
| 1. Add knowledge/document management | Users can manage indexed sources through the UI | Upload/indexing UI has queue states and safety rules |
| 2. Add settings and workspace controls | Admins can configure assistant behavior and access rules | Settings are permission-protected and audited |
| 3. Add metrics and operational dashboards | Product owners can inspect usage, savings, and safety metrics | Dashboard uses real metric events and no fake ROI claims |
| 4. Run full UX review | The full UI is checked against Kotaemon and healthcare workflows | Findings are documented and fixed or tracked |

### Simplest demo

Upload or manage a knowledge source, ask a question using it, inspect usage metrics, and confirm admin-only controls remain protected.

## Recommended Next Preparation

Prepare Phase 1 first. It closes the most visible product gap, keeps the scope bounded, and gives validating a concrete UI and contract surface to inspect before backend persistence or HMS data integration begins.

Phase plan approved. Planning continues by preparing Phase 1 for validation.
