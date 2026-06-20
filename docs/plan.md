# HMS AI Copilot Improvement Plan

## Project Objective

Transform the current HMS AI Copilot from a hybrid portfolio demo with partially mocked frontend screens into a coherent, backend-backed portfolio product where the core flows actually work:

* Real/Demo authentication is clearly separated.
* Users cannot freely switch roles or workspaces after login.
* Chat is centralized in one global ChatGPT-like interface.
* Chat respects role, workspace, patient, document, and chunk-level permissions.
* Patient/RAG answers always provide citations or safe refusal.
* Documents upload, search, citation, and open-original flows work.
* Dashboard, charts, tables, graph, audit logs, and traces use consistent seed/backend data.
* Graph RAG becomes an explainability tool, not just a static diagram.
* All detail pages include clear back navigation.
* Session memory works within a chat thread, but does not leak across sessions.

## Plan Execution Boundary

This document is a planning artifact only. Editing this file does not authorize implementation, refactoring, migration, seed-data changes, or UI changes.

Before any execution pass:

* Re-read `AGENTS.md`, run `node .codex/khuym_status.mjs --json`, and surface unrelated `.khuym/HANDOFF.json` state without auto-resuming it.
* Read `history/learnings/critical-patterns.md` and carry its RAG, permission, streaming, and migration-chain warnings into the work plan.
* Use GitNexus or repo-local code intelligence before touching code. For symbol edits, run impact analysis first and report blast radius.
* Validate the selected phase before coding. No phase should move directly from plan text to execution.
* Keep implementation evidence source-backed. If the live source contradicts this plan, update the plan or ask for approval before changing scope.

## ECC Skill Routing

ECC guide review indicates this plan needs a small skill stack per work area, not every available skill at once. Select the smallest relevant set for the phase being planned.

| Plan Area | Primary Skills / Guides | Review Focus |
| --- | --- | --- |
| Workflow gates and plan shaping | `khuym:using-khuym`, `khuym:planning`, `planning`, `search-first` | Keep this as planning until approved; preserve Khuym gates, handoff state, and source-grounded discovery. |
| Repo discovery and impact | `gitnexus-exploring`, `gitnexus-impact-analysis`, `codebase-onboarding`, `repo-scan` | Map live FastAPI, TanStack Start, routes, API contracts, and blast radius before code edits. |
| Backend/API/data model | `backend-patterns`, `python-patterns`, `python-testing`, `api-design`, `postgres-patterns`, `database-migrations` | Auth endpoints, permissions, chat, documents, dashboard APIs, migrations, and executable backend contracts. |
| Frontend/UI flows | `frontend-patterns`, `frontend-design`, `accessibility`, `build-web-apps:react-best-practices`, `e2e-testing`, `browser-qa` | TanStack Start pages, shadcn composition, keyboard/accessibility behavior, visual states, and Playwright demo flows. |
| Healthcare security and PHI | `security-review`, `healthcare-phi-compliance`, `hipaa-compliance`, `codex-security:threat-model` | RBAC/ABAC, PHI minimization, audit trails, admin/compliance boundaries, redaction claims, and break-glass risk. |
| RAG, citations, and AI quality | `healthcare-cdss-patterns`, `healthcare-eval-harness`, `ai-regression-testing`, `eval-harness`, `iterative-retrieval` | Permission-filtered retrieval, citation fidelity, answer usefulness, no unauthorized chunks, and regression scenarios. |
| Documents and OCR | `nutrient-document-processing`, `documents:documents`, `pdf:pdf`, `healthcare-phi-compliance` | Upload, page extraction, OCR fallback, indexing states, page-level citation, and honest redaction status. |
| Dashboard, graph, and portfolio demo | `dashboard-builder`, `ui-demo`, `portfolio-case-study-writer`, `product-lens` | Backend-backed metrics, graph explainability, demo story, known limitations, and truthful portfolio presentation. |
| Verification and closeout | `validating`, `tdd-workflow`, `ai-regression-testing`, `security-review`, `git-workflow` | Phase-specific tests, contract verification, permission/security regressions, and clean change summaries. |

## Product Decision Baseline

These answers are the default product decisions for this portfolio plan unless a later approved plan revision changes them.

| Question Area | Decision |
| --- | --- |
| Authentication screen | Keep a real login path and a separate Demo Persona login path. Real login aligns `/auth/token` with `/auth/me`; Demo Persona is only for reviewer mode. |
| Role model | Use one role per account for this portfolio version. Multi-role users are documented as future work, not part of this implementation plan. |
| Workspace meaning | Treat workspace as the user's department/unit scope, such as Pharmacy Dept, Cardiology, Ward, Admin, or Compliance. It is not a separate tenant model for this portfolio version. |
| Demo role selection | Keep role selection only on the login screen. Remove in-app role/workspace switching; switching demo persona requires sign out. |
| Admin patient access | Admin can view audit/system/config and access-request metadata. Admin must not access PHI by default or bypass patient permissions by role alone. |
| Chat suggestion behavior | Clicking a suggestion fills the input only. It does not auto-send, change route, or attach patient context unless the suggestion explicitly carries context metadata. |
| Chat threads | Support multiple backend-backed chat threads. `/chat` is the canonical route; a thread can optionally carry patient or document context. |
| Patient-bound thread | Patient context is optional but allowed. It must be permission-checked on every use, including follow-up questions and old threads. |
| Follow-up memory | Follow-ups like "what about metoprolol?" may use the active thread summary and patient context only inside the same thread and only while permission remains valid. |
| Citation policy | Patient-specific, clinical, guideline, document, and RAG answers must cite approved evidence or safely refuse. General app-help or non-clinical demo explanations may answer without citations. |
| Pharmacist patient fields | Pharmacist access is limited to medication orders/list, allergies, renal labs relevant to dosing, medication-safety evidence, and medication-related document chunks. |
| Nurse guideline access | Nurse may ask general hospital guideline questions and may access assigned patient care-plan data; unrelated PHI remains blocked. |
| No patient permission | Block the patient-specific answer, reveal no PHI, log the denied attempt, and offer an access request path. |
| Access approver | Route requests to Admin/Compliance review for the portfolio version. Approval scope must be limited, expiring, audited, and unable to exceed reviewer authority. |
| Break-glass | Default `ENABLE_BREAK_GLASS=false`. Treat emergency access as planned/future unless a later phase implements justification, expiry, audit, and review. |
| Document upload scope | Normal upload goes into the backend document/knowledge-base pipeline and can be linked to a patient when context exists. Session-only attachments are future work unless explicitly implemented. |
| OCR | Use real text extraction where available: native PDF extraction first, OCR only when installed/needed, and honest processing warnings when dependencies are missing. |
| PHI redaction | Short-term portfolio default is to remove unsupported redaction claims. Implement redaction only if Phase 8 Option A is explicitly selected and verified. |
| Document search | Target hybrid keyword plus semantic search for the demo, with permission filtering before snippets or chunks are shown. |
| Citation opening | Open the original document/page when page metadata exists and the user is authorized; otherwise open document detail or show source unavailable safely. |
| Graph data | Graph must come from backend DB/seeded evidence or extracted relationships, not hardcoded frontend data. It should work for any accessible seeded patient, not only Eleanor Vance. |
| Graph interaction | Users view, filter, click nodes/edges, and export. They do not manually edit clinical graph data in this portfolio version. |
| Graph click behavior | Clicking a node or edge opens a side panel, not a separate page. |
| Graph export | Phase 1 export is PNG and JSON. PDF report export is later/planned. |
| Dashboard data | Dashboard/charts should use backend or seeded DB data, not static frontend mock files. |
| Seed data | Use deterministic synthetic seed data for the portfolio demo, with metrics that can update after user actions where practical. |
| Chart insight engine | Phase 1 insight is rule-based over aggregate non-PHI metrics. LLM insight can be added later only with audit logging and PHI controls. |
| Insight audit logging | Log chart insight generation when it uses an LLM or any persisted AI trace. Rule-based local text can remain lightweight unless connected to the audit pipeline. |
| Most important metrics | Highest priority: unauthorized chunks sent to LLM equals zero, citation rate, safe refusal rate, denied access count, document indexing success/failure, P95 latency, and query volume. |

## Pre-Execution Review Addendum

Review date: 2026-06-19.

Verdict: do not execute the full plan as-is. The plan is directionally correct, but implementation must start with a contract/security validation slice because current source has security and API-contract contradictions that can make later UI work misleading.

Current-source blockers to resolve before feature execution:

| Severity | Finding | Current Evidence | Plan Impact |
| --- | --- | --- | --- |
| P1 | Real login calls a missing backend token route. | `app/frontend/src/lib/auth-context.tsx` posts `/auth/token`; `app/backend/src/hospital_ai/api/routes/auth.py` currently exposes `/auth/me` only. | Phase 1 must align auth contract before changing login UX further. |
| P1 | Admin currently bypasses patient PHI permission checks. | `app/backend/src/hospital_ai/services/permissions.py` returns early for `user.role == "admin"`; `app/backend/src/hospital_ai/api/routes/documents.py` skips document permission filtering for admin lists. | Phase 5 and Phase 18 must treat "Admin cannot access PHI by default" as a blocking security fix. |
| P1 | Access requests currently grant temporary permission by default. | `app/backend/src/hospital_ai/api/routes/access_requests.py` creates `PatientPermission` immediately and returns "Temporary clinical access scope granted for 1 hour." | Phase 6 must replace auto-grant with pending review before demoing access workflows. |
| P1 | Chat request/response contract in the plan does not match current backend or frontend. | `app/backend/src/hospital_ai/schemas/chat.py` requires `patient_id` and `question`; plan proposes `message`, `context`, `mode`, and `safety_status`; frontend still routes patient chat through `/chat/patients/$patientId`. | Phase 3 must include a contract decision before frontend rewiring. |
| P2 | Frontend still depends heavily on static `@/data/*` files. | Current pages import `data/patients`, `data/documents`, `data/threads`, `data/metrics`, `data/graph`, `data/audit`, and related files. | Move Phase 17 API data layer earlier, before dashboard/documents/graph polish. |
| P2 | Graph API assumed by the plan is not registered as a backend route. | GitNexus route map shows no `/graph/...` backend route; current frontend graph route imports `app/frontend/src/data/graph.ts`. | Phase 12 must start with backend API design, schema, and permission tests. |
| P2 | Dashboard/search APIs are narrower than the plan assumes. | Backend exposes `/dashboard/summary` and `/search/global`; current search response is patients/documents/threads only. | Phase 10 and Phase 11 need explicit endpoint expansion or scope reduction. |
| P2 | PHI redaction and break-glass UI claims are ahead of backend enforcement. | Frontend documents/settings/audit demo text mention redaction; `BreakGlassDialog` is local UI behavior. | Phase 8 and Phase 6 must remove or disable unsupported claims before portfolio demo. |
| P2 | Streaming chat needs explicit abort/lifecycle contract. | `app/frontend/src/lib/stream-client.ts` reads SSE without an exposed `AbortController` parameter. | Phase 3/4/18 must include stream cancellation and parity tests. |

Pre-execution order change:

1. Run Phase 0 as a live audit, then promote Phase 17 API contract/data-layer planning before broad UI rewrites.
2. Fix security invariants before convenience UI: admin PHI bypass, access-request auto-grant, break-glass visibility, and PHI redaction claims.
3. Decide one canonical chat payload/response contract before changing chat routes.
4. Only after those decisions, execute feature phases in the current plan order.

## Expected Files To Edit During Execution

This table is planning-only. Before changing any function, class, route handler, or model, re-open the current file, run GitNexus impact analysis for symbol edits, and update this file map if source has moved. `app/frontend/src/routeTree.gen.ts` is generated by TanStack tooling after route changes and should not be hand-edited.

| Phase / Task | Expected files to edit or review |
| --- | --- |
| Phase 0 - Baseline Audit and Stabilization | `docs/plan.md`; `app/frontend/src/routes/*`; `app/frontend/src/components/hms/*`; `app/frontend/src/components/shell/*`; `app/frontend/src/data/*`; `app/frontend/src/lib/*`; `app/backend/src/hospital_ai/api/router.py`; `app/backend/src/hospital_ai/api/routes/*`; `app/backend/scripts/verify_contracts.py`; `app/backend/scripts/uat_product_api_check.py` |
| 1.1 Implement or Align Auth Token Flow | `app/backend/src/hospital_ai/api/routes/auth.py`; `app/backend/src/hospital_ai/schemas/auth.py`; `app/backend/src/hospital_ai/api/deps.py`; `app/backend/src/hospital_ai/core/security.py`; `app/backend/src/hospital_ai/services/jwt_auth.py`; `app/backend/tests/test_auth.py`; `app/frontend/src/lib/auth-context.tsx`; `app/frontend/src/lib/api-client.ts`; `app/frontend/src/lib/auth-context.test.tsx`; `app/frontend/src/lib/api-client.test.ts` |
| 1.2 Separate Real Login and Demo Persona Login | `app/frontend/src/routes/auth.login.tsx`; `app/frontend/src/components/shell/AuthSplitLayout.tsx`; `app/frontend/src/components/shell/ActingAsBanner.tsx`; `app/frontend/src/lib/session.tsx`; `app/frontend/src/lib/rbac.ts`; `app/frontend/src/data/mockUsers.ts`; `app/frontend/src/data/workspaces.ts` |
| 1.3 Remove In-App Role/Workspace Switching | `app/frontend/src/components/shell/Topbar.tsx`; `app/frontend/src/routes/_app.settings.workspaces.tsx`; `app/frontend/src/lib/session.tsx`; `app/frontend/src/components/shell/AppShell.tsx`; `app/frontend/src/components/shell/ActingAsBanner.tsx` |
| 1.4 Enforce Single Role Model | `app/backend/src/hospital_ai/db/models.py`; `app/backend/src/hospital_ai/schemas/auth.py`; `app/backend/src/hospital_ai/services/permissions.py`; `app/backend/tests/test_permissions.py`; `app/frontend/src/lib/rbac.ts`; `app/frontend/src/lib/session.tsx` |
| 2.1 Header Alignment | `app/frontend/src/components/shell/Topbar.tsx`; `app/frontend/src/components/shell/AppShell.tsx`; `app/frontend/src/components/ui/input.tsx`; `app/frontend/src/components/ui/button.tsx`; `app/frontend/e2e/*` |
| 2.2 Sidebar Navigation Cleanup | `app/frontend/src/components/shell/AppSidebar.tsx`; `app/frontend/src/routes/_app.screens.tsx`; `app/frontend/src/components/hms/Logo.tsx`; `app/frontend/src/lib/rbac.ts` |
| 2.3 Add Back Button to Detail Pages | `app/frontend/src/components/hms/PageHeader.tsx`; `app/frontend/src/routes/_app.audit.traces.$traceId.tsx`; `app/frontend/src/routes/_app.documents.$documentId.tsx`; `app/frontend/src/routes/_app.citations.$sourceId.tsx`; `app/frontend/src/routes/_app.access-requests.$requestId.review.tsx`; `app/frontend/src/routes/_app.graph.patients.$patientId.tsx`; `app/frontend/src/routes/_app.patients.$patientId.tsx`; `app/frontend/src/routes/_app.chat.index.tsx` |
| 2.4 Empty, Loading, and Error States | `app/frontend/src/components/hms/EmptyState.tsx`; `app/frontend/src/components/hms/ErrorState.tsx`; `app/frontend/src/lib/api-client.ts`; affected route files under `app/frontend/src/routes/` |
| 3.1 Establish One Global Chat Route | `app/frontend/src/routes/_app.chat.index.tsx`; `app/frontend/src/routes/_app.chat.patients.$patientId.tsx`; `app/frontend/src/routes/_app.chat.history.tsx`; `app/frontend/src/routes/_app.chat.new.tsx`; `app/frontend/src/lib/stream-client.ts`; generated `app/frontend/src/routeTree.gen.ts` |
| 3.2 Fix Suggestion Behavior | `app/frontend/src/routes/_app.chat.index.tsx`; `app/frontend/src/components/hms/ChatComposer.tsx`; `app/frontend/src/components/hms/ChatMessage.tsx`; `app/frontend/src/components/hms/ChatMessage.test.tsx` |
| 3.3 Add Context Selector | `app/frontend/src/routes/_app.chat.index.tsx`; `app/frontend/src/components/hms/ChatComposer.tsx`; `app/frontend/src/lib/api/chat.ts` if created; `app/frontend/src/lib/api/patients.ts` if created; `app/frontend/src/lib/session.tsx` |
| 3.4 Chat Request Payload | `app/backend/src/hospital_ai/schemas/chat.py`; `app/backend/src/hospital_ai/api/routes/chat.py`; `app/backend/src/hospital_ai/api/routes/chat_stream.py`; `app/backend/src/hospital_ai/services/chat.py`; `app/backend/tests/test_chat_endpoint.py`; `app/backend/tests/test_chat_stream_endpoint.py`; `app/frontend/src/lib/stream-client.ts`; `app/frontend/src/lib/api/chat.ts` if created |
| 3.5 Recent Threads | `app/backend/src/hospital_ai/api/routes/chat_threads.py`; `app/backend/src/hospital_ai/services/chat_threads.py`; `app/backend/src/hospital_ai/schemas/chat_threads.py`; `app/backend/tests/test_chat_threads_api.py`; `app/backend/tests/test_chat_thread_contract.py`; `app/frontend/src/routes/_app.chat.index.tsx`; `app/frontend/src/routes/_app.chat.history.tsx`; `app/frontend/src/data/threads.ts` |
| 4.1 Use Existing Thread History | `app/backend/src/hospital_ai/services/chat.py`; `app/backend/src/hospital_ai/services/chat_threads.py`; `app/backend/src/hospital_ai/api/routes/chat_threads.py`; `app/backend/tests/test_chat_thread_messages_api.py`; `app/frontend/src/routes/_app.chat.index.tsx` |
| 4.2 Add Session Memory Summary | `app/backend/src/hospital_ai/db/models.py`; new Alembic migration under `app/backend/alembic/versions/`; `app/backend/src/hospital_ai/services/chat.py`; `app/backend/src/hospital_ai/services/chat_utils.py`; `app/backend/src/hospital_ai/schemas/chat_threads.py`; `app/backend/tests/test_chat_thread_contract.py` |
| 4.3 Memory Scope Rules | `app/backend/src/hospital_ai/services/permissions.py`; `app/backend/src/hospital_ai/services/chat.py`; `app/backend/src/hospital_ai/services/chat_threads.py`; `app/backend/tests/test_permissions.py`; `app/backend/tests/test_chat_endpoint.py` |
| 4.4 Follow-up Question Support | `app/backend/src/hospital_ai/services/chat.py`; `app/backend/src/hospital_ai/services/reasoning.py`; `app/backend/src/hospital_ai/api/routes/chat_stream.py`; `app/backend/tests/test_reasoning.py`; `app/backend/tests/test_chat_endpoint.py` |
| 5.1 Define Role-Based Access Matrix | `app/backend/src/hospital_ai/core/security.py`; `app/backend/src/hospital_ai/services/permissions.py`; `app/backend/src/hospital_ai/db/models.py`; `app/backend/tests/test_permissions.py`; `app/frontend/src/lib/rbac.ts`; `app/frontend/src/routes/_app.access-policy.tsx` |
| 5.2 Enforce Permission Before Retrieval | `app/backend/src/hospital_ai/services/permissions.py`; `app/backend/src/hospital_ai/services/retrieval.py`; `app/backend/src/hospital_ai/services/bm25.py`; `app/backend/src/hospital_ai/services/chat.py`; `app/backend/src/hospital_ai/api/routes/chat_stream.py`; `app/backend/tests/test_retrieval_sql.py`; `app/backend/tests/test_retrieval_postgres_integration.py` |
| 5.3 Safe Refusal | `app/backend/src/hospital_ai/services/chat.py`; `app/backend/src/hospital_ai/api/routes/chat.py`; `app/backend/src/hospital_ai/api/routes/chat_stream.py`; `app/backend/src/hospital_ai/core/prompts/rag_system_prompt.py`; `app/backend/tests/test_safe_refusal.py`; `app/frontend/src/components/hms/SafeRefusalCard.tsx` |
| 5.4 Citation Requirement | `app/backend/src/hospital_ai/services/reasoning.py`; `app/backend/src/hospital_ai/core/prompts/citation_validation_prompt.py`; `app/backend/src/hospital_ai/services/chat.py`; `app/backend/src/hospital_ai/api/routes/chat_stream.py`; `app/backend/tests/test_chat_citations.py`; `app/backend/tests/test_rag_trace.py`; `app/frontend/src/components/hms/CitationChip.tsx`; `app/frontend/src/components/hms/EvidenceRail.tsx` |
| ✅ 6.1 Disable Auto-Grant by Default | `app/backend/src/hospital_ai/api/routes/access_requests.py`; `app/backend/src/hospital_ai/db/models.py`; new Alembic migration under `app/backend/alembic/versions/`; `app/backend/src/hospital_ai/core/config.py`; `app/backend/tests/test_access_requests.py`; `app/backend/tests/test_permissions.py` |
| ✅ 6.2 Submit Access Request | `app/frontend/src/components/hms/AccessRequestDialog.tsx`; `app/frontend/src/routes/_app.patients.index.tsx`; `app/frontend/src/routes/error.forbidden.tsx`; `app/frontend/src/lib/api/access-requests.ts` if created; `app/backend/src/hospital_ai/api/routes/access_requests.py`; `app/backend/tests/test_access_requests.py` |
| ✅ 6.3 Review Page | `app/frontend/src/routes/_app.access-requests.index.tsx`; `app/frontend/src/routes/_app.access-requests.$requestId.tsx`; `app/frontend/src/routes/_app.access-requests.$requestId.review.tsx`; `app/backend/src/hospital_ai/api/routes/access_requests.py`; `app/backend/src/hospital_ai/schemas/audit.py`; `app/backend/tests/test_access_requests.py` |
| ✅ 6.4 Approval Scope | `app/backend/src/hospital_ai/db/models.py`; `app/backend/src/hospital_ai/services/permissions.py`; `app/backend/src/hospital_ai/api/routes/access_requests.py`; new Alembic migration under `app/backend/alembic/versions/`; `app/backend/tests/test_access_requests.py`; `app/backend/tests/test_permissions.py` |
| ✅ 6.5 Audit Events | `app/backend/src/hospital_ai/services/audit.py`; `app/backend/src/hospital_ai/api/routes/audit.py`; `app/backend/src/hospital_ai/api/routes/access_requests.py`; `app/backend/tests/test_access_requests.py`; `app/backend/tests/test_audit_2026_05.py`; `app/frontend/src/routes/_app.audit.index.tsx` |
| 7.1 Upload Documents | `app/backend/src/hospital_ai/api/routes/documents.py`; `app/backend/src/hospital_ai/schemas/documents.py`; `app/backend/src/hospital_ai/services/storage.py`; `app/backend/tests/test_documents.py`; `app/frontend/src/routes/_app.documents.upload.tsx`; `app/frontend/src/lib/api/documents.ts` if created |
| 7.2 Processing Status | `app/backend/src/hospital_ai/workers/jobs.py`; `app/backend/src/hospital_ai/workers/queue.py`; `app/backend/src/hospital_ai/api/routes/documents.py`; `app/backend/src/hospital_ai/schemas/documents.py`; `app/frontend/src/routes/_app.documents.index.tsx`; `app/frontend/src/routes/_app.documents.ocr-queue.tsx`; `app/frontend/src/routes/_app.documents.$documentId.tsx` |
| 7.3 OCR and Text Extraction | `app/backend/src/hospital_ai/services/ocr.py`; `app/backend/src/hospital_ai/services/loaders/pdf_loader.py`; `app/backend/src/hospital_ai/services/loaders/text_loader.py`; `app/backend/src/hospital_ai/services/loaders/docx_loader.py`; `app/backend/src/hospital_ai/services/loaders/composite.py`; `app/backend/src/hospital_ai/workers/jobs.py`; `app/backend/tests/test_documents.py`; `app/backend/tests/test_table_parsing.py` |
| 7.4 Chunking and Embedding | `app/backend/src/hospital_ai/services/chunking.py`; `app/backend/src/hospital_ai/services/embeddings.py`; `app/backend/src/hospital_ai/services/embedding/*`; `app/backend/src/hospital_ai/services/retrieval.py`; `app/backend/src/hospital_ai/workers/jobs.py`; `app/backend/tests/test_documents.py`; `app/backend/tests/test_retrieval_sql.py` |
| 7.5 Document Search | `app/backend/src/hospital_ai/api/routes/documents.py`; `app/backend/src/hospital_ai/schemas/documents.py`; `app/backend/src/hospital_ai/services/retrieval.py`; `app/backend/src/hospital_ai/services/bm25.py`; `app/backend/tests/test_documents.py`; `app/frontend/src/routes/_app.documents.search.tsx`; `app/frontend/src/lib/api/documents.ts` if created |
| 8A Implement PHI Redaction | new `app/backend/src/hospital_ai/services/phi_redaction.py` if selected; `app/backend/src/hospital_ai/workers/jobs.py`; `app/backend/src/hospital_ai/services/chat.py`; `app/backend/src/hospital_ai/core/prompts/rag_system_prompt.py`; `app/backend/tests/test_documents.py`; `app/backend/tests/test_chat_endpoint.py`; `app/frontend/src/routes/_app.settings.ai.tsx` |
| 8B Remove Unsupported PHI Redaction Claim | `app/frontend/src/routes/_app.documents.index.tsx`; `app/frontend/src/routes/_app.settings.ai.tsx`; `app/frontend/src/routes/_app.settings.index.tsx`; `app/frontend/src/data/audit.ts`; `app/frontend/src/components/hms/SafetyFooter.tsx`; `README.md` if present or created |
| ✅ 9.1 Replace Mock Citation Data | `app/frontend/src/data/citations.ts`; `app/frontend/src/components/hms/CitationChip.tsx`; `app/frontend/src/components/hms/EvidenceRail.tsx`; `app/frontend/src/routes/_app.citations.$sourceId.tsx`; `app/backend/src/hospital_ai/schemas/chat.py`; `app/backend/src/hospital_ai/schemas/documents.py` |
| ✅ 9.2 Citation Panel in Chat | `app/frontend/src/components/hms/ChatMessage.tsx`; `app/frontend/src/components/hms/CitationChip.tsx`; `app/frontend/src/components/hms/EvidenceRail.tsx`; `app/frontend/src/routes/_app.chat.index.tsx`; `app/frontend/src/routes/_app.chat.patients.$patientId.tsx` |
| ✅ 9.3 Open Original | `app/backend/src/hospital_ai/api/routes/documents.py`; `app/backend/src/hospital_ai/schemas/documents.py`; `app/frontend/src/routes/_app.documents.$documentId.tsx`; `app/frontend/src/routes/_app.citations.$sourceId.tsx`; `app/frontend/src/lib/api/documents.ts` if created |
| ✅ 9.4 Download Source | `app/backend/src/hospital_ai/api/routes/documents.py`; `app/backend/src/hospital_ai/services/storage.py`; `app/backend/tests/test_documents.py`; `app/frontend/src/routes/_app.documents.$documentId.tsx`; `app/frontend/src/routes/_app.citations.$sourceId.tsx` |
| ✅ 9.5 Copy Citation | `app/frontend/src/components/hms/CitationChip.tsx`; `app/frontend/src/routes/_app.citations.$sourceId.tsx`; `app/frontend/src/components/ui/button.tsx`; frontend unit tests near citation components |
| ✅ 10.1 Create Global Search API | `app/backend/src/hospital_ai/api/routes/search.py`; `app/backend/src/hospital_ai/schemas/search.py`; `app/backend/src/hospital_ai/api/router.py`; `app/backend/tests/test_search.py`; `app/frontend/src/lib/api/search.ts` if created |
| ✅ 10.2 Role-Aware Search Results | `app/backend/src/hospital_ai/services/permissions.py`; `app/backend/src/hospital_ai/api/routes/search.py`; `app/backend/tests/test_search.py`; `app/frontend/src/components/shell/Topbar.tsx`; `app/frontend/src/lib/rbac.ts` |
| ✅ 10.3 Frontend Search UI | `app/frontend/src/components/shell/Topbar.tsx`; `app/frontend/src/components/ui/command.tsx`; `app/frontend/src/lib/api/search.ts` if created; `app/frontend/src/routes/_app.search.tsx` if created; `app/frontend/e2e/*` |
| ✅ 11.1 Create Consistent Seed Data | `app/backend/scripts/seed_dev.py`; `app/backend/scripts/seed_data.py`; `app/backend/scripts/demo_setup.py`; `app/backend/src/hospital_ai/db/migrations.py`; `app/backend/src/hospital_ai/db/models.py`; `app/backend/tests/conftest.py` |
| ✅ 11.2 Backend-Backed Dashboard | `app/backend/src/hospital_ai/api/routes/dashboard.py`; `app/backend/src/hospital_ai/schemas/dashboard.py`; `app/backend/src/hospital_ai/services/metrics.py`; `app/backend/tests/test_dashboard.py`; `app/frontend/src/routes/_app.dashboard.index.tsx`; `app/frontend/src/lib/api/dashboard.ts` if created |
| ✅ 11.3 Important Metrics | `app/backend/src/hospital_ai/services/metrics.py`; `app/backend/src/hospital_ai/api/routes/feedback.py`; `app/backend/src/hospital_ai/schemas/dashboard.py`; `app/backend/tests/test_metrics.py`; `app/frontend/src/routes/_app.metrics.index.tsx`; `app/frontend/src/routes/_app.metrics.*.tsx` |
| ✅ 11.4 AI Analyze Button Under Charts | `app/frontend/src/routes/_app.dashboard.index.tsx`; `app/frontend/src/components/hms/MetricCard.tsx`; `app/backend/src/hospital_ai/services/metrics.py`; `app/backend/src/hospital_ai/services/audit.py` if persisted or LLM-backed; `app/backend/tests/test_dashboard.py` |
| 12.1 Connect Graph to Backend | new `app/backend/src/hospital_ai/api/routes/graph.py`; `app/backend/src/hospital_ai/api/router.py`; new `app/backend/src/hospital_ai/schemas/graph.py`; `app/backend/src/hospital_ai/services/graph_rag.py`; `app/backend/tests/test_graph_rag_integration.py`; `app/frontend/src/routes/_app.graph.patients.$patientId.tsx`; `app/frontend/src/lib/api/graph.ts` if created; `app/frontend/src/data/graph.ts` |
| 12.2 Node Types | `app/backend/src/hospital_ai/db/models.py`; new Alembic migration under `app/backend/alembic/versions/`; new `app/backend/src/hospital_ai/schemas/graph.py`; `app/backend/src/hospital_ai/services/graph_rag.py`; `app/backend/tests/test_graph_rag_integration.py`; `app/frontend/src/components/hms/GraphCanvas.tsx` |
| 12.3 Edge Types | `app/backend/src/hospital_ai/db/models.py`; new Alembic migration under `app/backend/alembic/versions/`; `app/backend/src/hospital_ai/services/graph_rag.py`; `app/backend/tests/test_graph_rag_integration.py`; `app/frontend/src/components/hms/GraphCanvas.tsx` |
| 12.4 Node Detail Side Panel | `app/frontend/src/components/hms/GraphCanvas.tsx`; `app/frontend/src/routes/_app.graph.patients.$patientId.tsx`; `app/frontend/src/components/ui/sheet.tsx`; `app/frontend/src/components/ui/dialog.tsx`; `app/frontend/src/lib/api/graph.ts` if created |
| 12.5 Edge Detail | `app/frontend/src/components/hms/GraphCanvas.tsx`; `app/frontend/src/routes/_app.graph.patients.$patientId.tsx`; new `app/backend/src/hospital_ai/schemas/graph.py`; `app/backend/src/hospital_ai/services/graph_rag.py` |
| 12.6 Graph Controls | `app/frontend/src/components/hms/GraphCanvas.tsx`; `app/frontend/src/routes/_app.graph.patients.$patientId.tsx`; `app/frontend/src/components/ui/toggle-group.tsx`; `app/frontend/src/components/ui/select.tsx` |
| 12.7 Export and Share | `app/frontend/src/components/hms/GraphCanvas.tsx`; `app/frontend/src/routes/_app.graph.patients.$patientId.tsx`; `app/backend/src/hospital_ai/services/audit.py` if exporting PHI; `app/backend/src/hospital_ai/api/routes/audit.py` |
| 13.1 Audit Log Search | `app/backend/src/hospital_ai/api/routes/audit.py`; `app/backend/src/hospital_ai/schemas/audit.py`; `app/backend/tests/test_audit_2026_05.py`; `app/frontend/src/routes/_app.audit.index.tsx`; `app/frontend/src/lib/api/audit.ts` if created |
| 13.2 Audit Export | `app/backend/src/hospital_ai/api/routes/audit.py`; `app/backend/src/hospital_ai/services/audit.py`; `app/backend/tests/test_audit_2026_05.py`; `app/frontend/src/routes/_app.audit.export.tsx`; `app/frontend/src/routes/_app.audit.index.tsx` |
| 13.3 View Signed Digest | `app/backend/src/hospital_ai/api/routes/audit.py`; new digest service if selected under `app/backend/src/hospital_ai/services/`; `app/backend/tests/test_audit_2026_05.py`; `app/frontend/src/routes/_app.audit.compliance-summary.tsx`; `app/frontend/src/routes/_app.audit.index.tsx` |
| 13.4 Trace Detail Page | `app/backend/src/hospital_ai/api/routes/rag_trace.py`; `app/backend/src/hospital_ai/schemas/chat.py`; `app/backend/tests/test_rag_trace.py`; `app/frontend/src/routes/_app.audit.traces.$traceId.tsx`; `app/frontend/src/components/hms/TraceTimeline.tsx`; `app/frontend/src/data/traces.ts` |
| 13.5 Trace Span Detail | `app/frontend/src/components/hms/TraceTimeline.tsx`; `app/frontend/src/routes/_app.audit.traces.$traceId.tsx`; `app/backend/src/hospital_ai/api/routes/rag_trace.py`; `app/backend/src/hospital_ai/services/chat.py`; `app/backend/tests/test_rag_trace.py` |
| 14.1 Patients API Integration | `app/backend/src/hospital_ai/api/routes/patients.py`; `app/backend/src/hospital_ai/schemas/patients.py`; `app/backend/tests/test_patients.py`; `app/backend/tests/test_patient_bff.py`; `app/frontend/src/routes/_app.patients.index.tsx`; `app/frontend/src/lib/api/patients.ts` if created; `app/frontend/src/data/patients.ts` |
| 14.2 Add Patient | `app/backend/src/hospital_ai/api/routes/patients.py`; `app/backend/src/hospital_ai/schemas/patients.py`; `app/backend/src/hospital_ai/db/models.py`; new Alembic migration under `app/backend/alembic/versions/` if model fields change; `app/backend/tests/test_patients.py`; `app/frontend/src/routes/_app.patients.index.tsx`; new `app/frontend/src/routes/_app.patients.new.tsx` if route option is selected |
| 14.3 Open Chat from Patient Row | `app/frontend/src/routes/_app.patients.index.tsx`; `app/frontend/src/routes/_app.patients.$patientId.tsx`; `app/frontend/src/routes/_app.chat.index.tsx`; `app/frontend/src/components/hms/AccessRequestDialog.tsx`; `app/frontend/src/lib/api/chat.ts` if created |
| 14.4 Patient Detail | `app/backend/src/hospital_ai/api/routes/patients.py`; `app/backend/src/hospital_ai/schemas/patients.py`; `app/backend/tests/test_patient_bff.py`; `app/frontend/src/routes/_app.patients.$patientId.tsx`; `app/frontend/src/routes/_app.patients.$patientId.overview.tsx`; `app/frontend/src/routes/_app.patients.$patientId.documents.tsx`; `app/frontend/src/routes/_app.patients.$patientId.medications.tsx`; `app/frontend/src/routes/_app.patients.$patientId.labs.tsx` |
| 15.1 Phase 1 Attachment Behavior | `app/frontend/src/components/hms/ChatComposer.tsx`; `app/frontend/src/routes/_app.chat.index.tsx`; `app/backend/src/hospital_ai/api/routes/documents.py`; `app/backend/src/hospital_ai/api/routes/chat.py`; `app/backend/src/hospital_ai/services/chat.py`; `app/backend/tests/test_documents.py`; `app/backend/tests/test_chat_endpoint.py` |
| 15.2 UI | `app/frontend/src/components/hms/ChatComposer.tsx`; `app/frontend/src/components/hms/ChatMessage.tsx`; `app/frontend/src/routes/_app.chat.index.tsx`; `app/frontend/src/components/ui/progress.tsx`; `app/frontend/src/components/ui/alert.tsx` |
| 15.3 Backend Integration | `app/frontend/src/lib/api/documents.ts` if created; `app/frontend/src/lib/api/chat.ts` if created; `app/backend/src/hospital_ai/api/routes/documents.py`; `app/backend/src/hospital_ai/schemas/documents.py`; `app/backend/src/hospital_ai/services/retrieval.py`; `app/backend/tests/test_documents.py` |
| 15.4 Future Session-Only Attachments | `docs/plan.md`; `README.md` if present or created; no application code unless this future scope is explicitly approved. |
| Phase 16 - Medication Safety Page | `app/frontend/src/routes/_app.pharmacy.review-queue.tsx`; `app/frontend/src/routes/_app.medication-conflicts.$conflictId.tsx`; `app/frontend/src/routes/_app.patients.$patientId.medication-review.tsx`; `app/frontend/src/data/conflicts.ts`; `app/backend/src/hospital_ai/services/drug_check.py`; `app/backend/src/hospital_ai/core/prompts/drug_check_prompt.py`; `app/backend/tests/test_drug_check.py`; `app/frontend/src/lib/api/medication-safety.ts` if created |
| 17.1 Central API Client | `app/frontend/src/lib/api-client.ts`; `app/frontend/src/lib/api-client.test.ts`; new files under `app/frontend/src/lib/api/`; `app/frontend/src/lib/auth-context.tsx`; `app/frontend/src/lib/errors.ts` |
| 17.2 API Modules | new files under `app/frontend/src/lib/api/` such as `auth.ts`, `chat.ts`, `patients.ts`, `documents.ts`, `citations.ts`, `search.ts`, `graph.ts`, `audit.ts`, `access-requests.ts`, `dashboard.ts`, and `metrics.ts`; related tests under `app/frontend/src/lib/` |
| 17.3 Replace Mock Imports | all route/component files importing `@/data/*`; `app/frontend/src/data/patients.ts`; `app/frontend/src/data/documents.ts`; `app/frontend/src/data/threads.ts`; `app/frontend/src/data/metrics.ts`; `app/frontend/src/data/graph.ts`; `app/frontend/src/data/audit.ts`; `app/frontend/src/data/accessRequests.ts`; `app/frontend/src/data/citations.ts` |
| 17.4 Mock Fallback Policy | `app/frontend/src/lib/api-client.ts`; new `app/frontend/src/lib/api/*`; `app/frontend/src/lib/errors.ts`; `app/frontend/src/components/hms/ErrorState.tsx`; `app/frontend/src/components/hms/EmptyState.tsx`; affected routes under `app/frontend/src/routes/` |
| 18.1 Unit Tests | `app/backend/tests/test_permissions.py`; `app/backend/tests/test_chat_citations.py`; `app/backend/tests/test_metrics.py`; `app/backend/tests/test_search.py`; `app/backend/tests/test_access_requests.py`; `app/frontend/src/lib/*.test.ts`; `app/frontend/src/components/hms/*.test.tsx` |
| 18.2 Integration Tests | `app/backend/tests/test_auth.py`; `app/backend/tests/test_chat_endpoint.py`; `app/backend/tests/test_chat_stream_endpoint.py`; `app/backend/tests/test_documents.py`; `app/backend/tests/test_search.py`; `app/backend/tests/test_access_requests.py`; `app/backend/tests/test_rag_trace.py`; `app/backend/tests/test_graph_rag_integration.py` |
| 18.3 End-to-End Tests | `app/frontend/e2e/*`; `app/frontend/playwright.config.ts`; `app/frontend/src/routes/_app.screens.tsx`; seed scripts under `app/backend/scripts/` |
| 18.4 Security Tests | `app/backend/tests/test_permissions.py`; `app/backend/tests/test_retrieval_sql.py`; `app/backend/tests/test_retrieval_postgres_integration.py`; `app/backend/tests/test_chat_endpoint.py`; `app/backend/tests/test_chat_stream_endpoint.py`; `app/backend/tests/test_search.py`; frontend access-denied E2E tests under `app/frontend/e2e/*` |
| 19.1 Demo Story | `README.md` if present or created; `docs/plan.md`; `app/frontend/src/routes/_app.screens.tsx`; `app/frontend/src/components/hms/SyntheticDataPill.tsx` |
| 19.2 Demo Data | `app/backend/scripts/seed_dev.py`; `app/backend/scripts/seed_data.py`; `app/backend/scripts/demo_setup.py`; `app/backend/tests/conftest.py`; `screen-demo/*` only after UI is working and screenshots are regenerated |
| 19.3 UI Labels | `app/frontend/src/routes/_app.screens.tsx`; affected route files under `app/frontend/src/routes/`; `app/frontend/src/components/hms/SafetyFooter.tsx`; `app/frontend/src/components/hms/SyntheticDataPill.tsx`; `app/frontend/src/components/shell/ActingAsBanner.tsx` |
| 19.4 README / Portfolio Explanation | `README.md` if present or created; docs under `docs/`; `app/backend/README.md` if present; `app/frontend/README.md` if present |
| 19.5 Known Limitations | `README.md` if present or created; `docs/plan.md`; portfolio docs under `docs/`; visible demo labels in affected frontend route files |

---

# Phase 0 — Baseline Audit and Stabilization

## Goal

Understand what is real, what is mock, what is partially wired, and what must be fixed first. This phase prevents random patching and creates a clear technical baseline.

## Tasks

* [x] Audit all frontend routes and identify whether each page uses backend API, local mock data, or hardcoded static content.
* [x] Audit backend endpoints related to auth, chat, documents, citations, access requests, audit logs, dashboard, and graph.
* [x] Create a mapping table:

```text
Frontend page → API used → Current status → Required fix
```

* [x] Identify all buttons that currently do nothing.
* [x] Identify all buttons that route incorrectly.
* [x] Identify all UI claims that are not supported by backend logic.
* [x] Identify all mock files such as `data/metrics`, `data/patients`, `data/documents`, `data/threads`, `data/graph.ts`.
* [x] Identify all backend flows that are already usable and should be connected to frontend.
* [x] Define environment flags:

```env
DEMO_MODE=true
DEV_AUTO_GRANT_ACCESS=false
USE_MOCK_DATA=false
ENABLE_BREAK_GLASS=false
```

* [x] Create a single issue list grouped by P0, P1, and P2 priority.

## Acceptance Criteria

* [x] Every frontend page is classified as one of:

```text
Real API-backed
Partially API-backed
Mock/static
Broken/unwired
```

* [x] Every important broken interaction is documented.
* [x] The team knows which backend APIs already exist and which ones are missing.
* [x] No UI claim remains undocumented.
* [x] A clear implementation order exists before coding begins.

## Exceptions / Edge Cases

* If a backend endpoint exists but returns incomplete data, mark it as “partially usable,” not “done.”
* If a frontend button opens a fake modal with static data, mark it as mock.
* If a feature is only for portfolio storytelling and not production-ready, label it clearly as demo/planned.

---

# Phase 1 — Authentication, Demo Mode, Role, and Workspace Control

## Goal

Fix the mismatch between frontend login and backend auth, separate Real Login from Demo Persona Login, and prevent users from switching roles/workspaces freely after entering the app.

## Current Problem

Frontend “Real Login” calls:

```text
/auth/token
```

but backend currently mainly supports:

```text
/auth/me
```

Also, the avatar menu allows switching role/workspace inside the app, which breaks the permission model.

## Tasks

### 1.1 Implement or Align Auth Token Flow

* [x] Add backend endpoint:

```http
POST /auth/token
```

* [x] Accept login payload:

```json
{
  "email": "riya.patel@hospital.org",
  "password": "demo"
}
```

* [x] Return:

```json
{
  "access_token": "jwt-or-dev-token",
  "token_type": "bearer",
  "user": {
    "id": "u-pharm-001",
    "name": "Pharm. Riya Patel",
    "role": "pharmacist",
    "workspace": "Pharmacy Dept"
  }
}
```

* [x] Keep `/auth/me` as the canonical endpoint for current user verification.
* [x] Frontend should call `/auth/token` first, then `/auth/me`.
* [x] Store token securely according to current app architecture.
* [x] Add logout flow that clears token and user state.

### 1.2 Separate Real Login and Demo Persona Login

* [x] Create login screen with two tabs:

```text
Real Login
Demo Persona
```

* [x] Real Login uses email/password.
* [x] Demo Persona allows reviewer to choose:

```text
Cardiologist
Pharmacist
Nurse
Hospitalist
Admin
Compliance
```

* [x] After entering the app, the selected role is fixed.
* [x] Add visible banner in demo mode:

```text
Demo mode: You are signed in as Pharmacist in Pharmacy Dept.
```

### 1.3 Remove In-App Role/Workspace Switching

* [x] Remove or disable avatar menu items:

```text
Switch role
Switch workspace
```

* [x] Replace avatar menu with:

```text
Profile
Security
My audit trail
Keyboard shortcuts
Sign out
```

* [x] Show current role and workspace as read-only.
* [x] If demo mode still needs switching, force sign out and return to Demo Persona Login.

### 1.4 Enforce Single Role Model

* [x] Keep `users.role` as a single string for this portfolio version.
* [x] Avoid introducing many-to-many role mapping unless required later.
* [x] Ensure backend derives permission from authenticated user, not frontend state.

## Acceptance Criteria

* [x] Real Login no longer calls a missing endpoint.
* [x] `/auth/token` and `/auth/me` work consistently.
* [x] Demo Persona Login works separately from Real Login.
* [x] Users cannot switch role/workspace from inside the app.
* [x] Current user role and workspace are shown correctly in header.
* [x] Backend never trusts role/workspace sent from frontend if it conflicts with token identity.

## Exceptions / Edge Cases

* If backend token validation fails, frontend must redirect to login.
* If user token is valid but user record is missing, show session expired.
* If Demo Persona mode is enabled, label it clearly.
* If Real Login is not fully production-grade, do not present it as production-ready.
* If workspace is missing, default to “Hospital-wide” only for non-PHI general access.

---

# Phase 2 — Core Layout, Header, Navigation, and Back Buttons

## Goal

Fix visible UX issues that make the system feel unfinished: header alignment, broken global search, route detail pages without back navigation, and inconsistent menu behavior.

## Tasks

### 2.1 Header Alignment

* [x] Move notification bell and profile/avatar area to the far right of the header.
* [x] Use a layout similar to:

```text
[Sidebar toggle] [Global search...................] [Workspace badge] [Bell] [Avatar]
```

* [x] Ensure header actions use `margin-left: auto` or equivalent flex behavior.
* [x] Make header responsive for smaller screens.

### 2.2 Sidebar Navigation Cleanup

* [x] Keep Chat as a primary item.
* [x] Consider renaming:

```text
Graph RAG → Knowledge Graph
```

or:

```text
Graph RAG → Clinical Reasoning Graph
```

* [x] Group navigation clearly:

```text
Workspace
- Dashboard
- Notifications
- Screens Index

Clinical
- Patients
- Chat
- Timeline
- Medication Safety

Knowledge
- Documents
- Citations
- Knowledge Graph

Compliance
- Audit
- Access Requests
- Access Policy

Ops
- Metrics
- Integrations

Admin
- Settings
```

### 2.3 Add Back Button to Detail Pages

Add a parent back link in main content for every detail route.

* [x] `/audit/traces/:trace_id`

```text
← Back to Audit logs
```

* [x] `/documents/:document_id`

```text
← Back to Documents
```

* [x] `/citations/:citation_id`

```text
← Back to Citations
```

* [x] `/access-requests/:request_id/review`

```text
← Back to Access requests
```

* [x] `/graph/patients/:patient_id`

```text
← Back to Knowledge Graph
```

* [x] `/patients/:patient_id`

```text
← Back to Patients
```

* [x] `/chat?patient=p-001`

```text
← Clear patient context
```

### 2.4 Empty, Loading, and Error States

* [x] Add loading state for pages using backend API.
* [x] Add empty state for no results.
* [x] Add error state for failed API call.
* [x] Add retry button where appropriate.
* [x] Avoid showing stale mock data when API fails.

## Acceptance Criteria

* [x] Header profile and notification are visually aligned to the far right.
* [x] Every detail page has a clear back action.
* [x] Navigation labels are understandable for both technical and clinical viewers.
* [x] No route feels like a dead end.
* [x] API loading/error/empty states are handled consistently.

## Exceptions / Edge Cases

* If user directly opens a detail URL, back button should still go to the logical parent route, not browser history only.
* If user does not have access to parent list, back button should go to Dashboard.
* If the sidebar is collapsed, navigation should remain usable.

---

# Phase 3 — Global Chat Redesign Without Major UI Redesign

## Goal

Keep the current chat UI, but fix its logic. The system should have one global ChatGPT-like chat interface for all hospital roles. Roles should affect permissions, not create separate chat systems.

## Current Problem

Clicking a suggestion can route to:

```text
/chat/patients/p-001
```

This is wrong. Suggestions should fill the input, not change route.

## Tasks

### 3.1 Establish One Global Chat Route

* [x] Make `/chat` the canonical chat route.
* [x] Treat patient context as optional state:

```text
/chat?patient=p-001
```

* [x] Avoid using separate route as a different chat engine:

```text
/chat/patients/p-001
```

* [x] If `/chat/patients/:patient_id` exists, redirect it to:

```text
/chat?patient=:patient_id
```

### 3.2 Fix Suggestion Behavior

* [x] Clicking a suggestion should only fill the input.
* [x] It should not send automatically.
* [x] It should not change route.
* [x] It should not attach patient context unless suggestion explicitly contains patient metadata.
* [x] User must manually press Send.

Correct behavior:

```text
Click suggestion
→ Fill input
→ Stay on /chat
→ User may edit
→ User clicks Send
```

### 3.3 Add Context Selector

* [x] Add optional context display near the input:

```text
Context: General hospital knowledge
Context: Patient — Eleanor Vance
Context: Document — DOAC-Renal-Dosing.pdf
Context: Unit — Pharmacy Dept
```

* [x] Allow clearing current patient/document context.
* [x] Show permission warning if selected context is restricted.

### 3.4 Chat Request Payload

* [x] Frontend sends:

```json
{
  "thread_id": "th-001",
  "message": "What about metoprolol?",
  "context": {
    "patient_id": "p-001",
    "document_ids": []
  },
  "mode": "cited"
}
```

* [x] Backend returns:

```json
{
  "answer": "...",
  "citations": [],
  "thread_id": "th-001",
  "safety_status": "answered"
}
```

### 3.5 Recent Threads

* [x] Replace mock recent threads with backend `chat_threads`.
* [x] Clicking a thread opens the same `/chat` page with selected `thread_id`.
* [x] Thread list should show title, patient context if any, last message time, and access state.

## Acceptance Criteria

* [x] `/chat` is the main chat experience.
* [x] Suggestions only fill the input.
* [x] Suggestions never route to patient chat automatically.
* [x] Patient context can exist without creating a separate chat system.
* [x] Recent threads are loaded from backend.
* [x] A thread can continue conversation using `thread_id`.

## Exceptions / Edge Cases

* If selected patient is inaccessible, chat should show access request option.
* If thread belongs to a patient the current user no longer has access to, show restricted thread state.
* If thread is missing, create a new thread.
* If user opens old URL `/chat/patients/p-001`, redirect safely.

---

# Phase 4 — Chat Session Memory

## Goal

Enable short-term memory within one chat thread so follow-up questions work correctly, while avoiding dangerous cross-session or cross-patient memory leakage.

## Tasks

### 4.1 Use Existing Thread History

* [x] Ensure frontend always sends `thread_id`.
* [x] Backend loads last N messages for the thread.
* [x] Backend uses thread history to resolve follow-up questions.
* [x] Store all user and assistant messages in `chat_messages`.

### 4.2 Add Session Memory Summary

Create or use a table:

```text
chat_session_memory
- thread_id
- active_patient_id
- summary
- active_entities
- source_ids
- updated_at
```

* [x] After each assistant response, update memory summary.
* [x] Store only concise clinical/contextual summary.
* [x] Store active entities such as:

```text
apixaban
metoprolol
AFib
CKD stage 3
Eleanor Vance
```

* [x] Store source IDs used in previous answers.
* [x] Do not store irrelevant full PHI in memory summary.

### 4.3 Memory Scope Rules

* [x] Memory only applies within the same thread.
* [x] Memory does not automatically transfer across threads.
* [x] Memory does not transfer across patients.
* [x] If patient context changes, summarize and reset active patient context.
* [x] If user asks a new unrelated question, memory should not over-constrain retrieval.

### 4.4 Follow-up Question Support

Example:

```text
User: Explain apixaban renal-dose adjustment for Eleanor Vance.
Assistant: ...
User: What about metoprolol?
```

Expected behavior:

```text
Assistant understands metoprolol question in the context of Eleanor Vance, if thread context is still active.
```

## Acceptance Criteria

* [x] Follow-up questions work within a thread.
* [x] Patient context is preserved within the same thread.
* [x] Memory does not leak between different patients.
* [x] Memory summary is short and auditable.
* [x] Thread history is not mock data.

## Exceptions / Edge Cases

* If memory summary conflicts with current patient record, current database data wins.
* If user switches patient context, require confirmation.
* If thread has stale access permission, re-check permission before using memory.
* If memory references a document that user can no longer access, do not use it.

---

# Phase 5 — Chat Permission and Data Control

## Goal

Ensure the LLM never receives unauthorized patient data, document chunks, or PHI. Permission filtering must happen before retrieval results are sent to the model.

## Core Rule

```text
Unauthorized chunks must never be sent to the LLM.
```

## Tasks

### 5.1 Define Role-Based Access Matrix

Create a permission matrix for the portfolio version.

#### Pharmacist

* [x] May access medication list/orders.
* [x] May access allergies.
* [x] May access renal labs relevant to medication dosing.
* [x] May access medication safety evidence.
* [x] May access medication-related document chunks.
* [x] Should not access unrelated full progress notes by default.

#### Cardiologist

* [x] May access assigned cardiology patients.
* [x] May access cardiology guidelines.
* [x] May access relevant labs, imaging summaries, medications, diagnoses.
* [x] May ask patient-specific clinical questions if access is verified.

#### Nurse

* [x] May access assigned unit patients.
* [x] May ask general hospital guideline questions.
* [x] May access patient care plan data if assigned.
* [x] Should be blocked from unrelated patient PHI.

#### Admin

* [x] May access audit/system/config data.
* [x] May access access request metadata.
* [x] Must not access PHI by default.
* [x] Must not bypass patient permissions by role alone.

#### Compliance

* [x] May access audit logs.
* [x] May review access policy and access request records.
* [x] PHI access should be limited, logged, and justified.

### 5.2 Enforce Permission Before Retrieval

* [x] Identify patient context.
* [x] Check user role/workspace.
* [x] Check patient access.
* [x] Check document access.
* [x] Check chunk-level access tags.
* [x] Retrieve only allowed chunks.
* [x] Send only allowed chunks to LLM.
* [x] Count blocked chunks for audit metadata.

### 5.3 Safe Refusal

If user asks patient-specific question without access:

```text
I cannot answer because you do not have access to this patient record. You may submit an access request.
```

* [x] Show `Request access` button.
* [x] Do not reveal patient details.
* [x] Log denied attempt.

### 5.4 Citation Requirement

* [x] Patient-specific RAG answers must cite source documents.
* [x] Guideline/protocol answers must cite approved sources.
* [x] If no sufficient evidence, return insufficient evidence response.
* [x] Do not hallucinate clinical guidance without source.

## Acceptance Criteria

* [x] Unauthorized patient data is blocked before LLM call.
* [x] Backend returns safe refusal when permission fails.
* [x] Admin cannot read PHI by default.
* [x] Pharmacist sees medication-related context only.
* [x] Every patient/RAG answer has citation or safe refusal.
* [x] Audit log records allowed chunks, blocked chunks, and permission result.

## Exceptions / Edge Cases

* If no patient context is detected, answer only from general approved knowledge.
* If patient name is ambiguous, ask for clarification.
* If user has document access but not patient access, do not reveal patient-specific content.
* If citation source is deleted, show citation unavailable and refuse clinical conclusion.
* If break-glass is disabled, do not offer emergency bypass.

---

# Phase 6 — Access Request Workflow

## Goal

Replace auto-grant behavior with a proper pending approval workflow, making access control credible for a healthcare AI portfolio.

## Current Problem

Backend may auto-grant access for 1 hour when HMS sync is off. This weakens the permission model.

## Tasks

### 6.1 Disable Auto-Grant by Default

* [x] Set:

```env
DEV_AUTO_GRANT_ACCESS=false
```

* [x] If auto-grant exists, restrict it to local development only.
* [x] Add UI warning if auto-grant mode is enabled.

### 6.2 Submit Access Request

* [x] When user lacks patient access, show button:

```text
Request access
```

* [x] Submit request with:

```json
{
  "patient_id": "p-001",
  "requester_id": "u-001",
  "requested_scope": "patient.medication_context",
  "justification": "Medication renal-dose review",
  "duration_requested": "24h"
}
```

* [x] Initial status must be:

```text
pending
```

### 6.3 Review Page

* [x] Add working review page:

```text
/access-requests/:request_id/review
```

* [x] Display:

```text
Request ID
Patient
Requester
Requester role
Workspace
Requested scope
Justification
Submitted time
Current status
Risk level
Policy recommendation
```

* [x] Add actions:

```text
Approve
Deny
Request more information
```

### 6.4 Approval Scope

When approving, reviewer must select:

```text
Access level:
- Read patient summary
- Medication context only
- Full chart
- Ask AI about patient
- Download source docs

Duration:
- 1 hour
- 24 hours
- 7 days
- Until discharge
- Custom
```

### 6.5 Audit Events

* [x] Log access request submitted.
* [x] Log access request approved.
* [x] Log access request denied.
* [x] Log access request expired.
* [x] Log every patient access after approval.

## Acceptance Criteria

* [x] No access request is auto-approved by default.
* [x] Request page shows real request data.
* [x] Approve updates user access.
* [x] Deny requires reason.
* [x] Request more information changes status.
* [x] Chat can proceed after approval.
* [x] All access decisions are audited.

## Exceptions / Edge Cases

* If request is already approved/denied, disable duplicate action.
* If patient no longer exists, mark request invalid.
* If reviewer lacks approval permission, hide action buttons.
* If requested scope exceeds reviewer authority, block approval.
* If access expires, chat must re-check permission.

---

# Phase 7 — Documents Upload, OCR, Indexing, and Search

## Goal

Wire the frontend Documents page to the real backend upload, extraction, OCR, chunking, embedding, and hybrid search pipeline.

## Tasks

### 7.1 Upload Documents

* [x] Connect Upload button to backend upload endpoint.
* [x] Support drag and drop.
* [x] Support file picker.
* [x] Support accepted types:

```text
PDF
DOCX
JPG/PNG scan
HL7 v2
DICOM SR
```

* [x] Enforce file size limit.
* [x] Show upload progress.
* [x] Create document record immediately after upload.

### 7.2 Processing Status

* [x] Show statuses:

```text
Queued
Processing
OCR
Indexed
Error
```

* [x] Poll backend status until final state.
* [x] Display error reason when status is Error.
* [x] Add retry processing button if supported.

### 7.3 OCR and Text Extraction

* [x] Use PyMuPDF for native PDF extraction.
* [x] Use PaddleOCR for image/scan if installed.
* [x] If OCR dependency is missing, show honest warning.
* [x] Store extracted page text.
* [x] Store page-level metadata.

### 7.4 Chunking and Embedding

* [x] Chunk extracted text.
* [x] Store chunk metadata:

```text
document_id
page
section
chunk_text
embedding
access_tags
patient_id
source_type
```

* [x] Index chunks into vector/hybrid search.
* [x] Ensure permission tags are attached before retrieval.

### 7.5 Document Search

* [x] Connect search input to backend hybrid search.
* [x] Search by:

```text
file name
document category
uploader
status
content
semantic meaning
```

* [x] Show result snippets.
* [x] Show page number.
* [x] Show score/confidence if useful.
* [x] Clicking result opens document detail.

## Acceptance Criteria

* [x] Upload button works.
* [x] Drag and drop works.
* [x] Uploaded file appears in Documents table.
* [x] Status changes from queued/processing to indexed/error.
* [x] Search finds documents by name.
* [x] Search finds documents by content.
* [x] Indexed document can be used by chat.
* [x] Document search respects permissions.

## Exceptions / Edge Cases

* If upload type unsupported, reject with clear message.
* If OCR fails, mark OCR error but preserve original file.
* If embedding fails, mark indexing error.
* If document has PHI and redaction is not implemented, do not claim redaction.
* If user lacks permission, document should not appear in search.

---

# Phase 8 — PHI Redaction Claim and Compliance Accuracy

## Goal

Avoid false compliance claims. Either implement redaction before embedding or remove the claim from the UI.

## Current Problem

UI says uploads pass through PHI redaction before vector embedding, but backend currently embeds extracted text directly.

## Option A — Implement PHI Redaction

### Tasks

* [ ] Add PHI detection step after extraction.
* [ ] Detect names, MRNs, dates, addresses, phone numbers, and identifiers.
* [ ] Store original document securely.
* [ ] Store redacted text for embedding.
* [ ] Keep mapping from redacted chunk to original page for authorized citation viewing.
* [ ] Add audit event for redaction processing.
* [ ] Add redaction status to document pipeline.

### Acceptance Criteria

* [ ] Text is redacted before embedding.
* [ ] Original source remains accessible only to authorized users.
* [ ] Citation can still open original page for authorized users.
* [ ] UI claim is accurate.

## Option B — Remove Claim for Portfolio Honesty

### Tasks

* [x] Replace UI claim with:

```text
Uploads are indexed for demo search. PHI redaction is planned for production hardening.
```

* [x] Add production hardening note in documentation.
* [x] Ensure no false compliance statement remains.

### Acceptance Criteria

* [x] UI no longer claims unsupported redaction.
* [x] Portfolio remains technically honest.
* [x] Future redaction work is listed as planned.

## Recommended Choice

* [x] For short-term portfolio: choose Option B.
* [ ] For stronger compliance demo: choose Option A later.

## Exceptions / Edge Cases

* If demo data is synthetic only, still avoid claiming redaction unless implemented.
* If using real clinical files, redaction should be mandatory before indexing.
* If redaction confidence is low, require manual review.

---

# Phase 9 — Citations, Source Verification, Open Original, and Download

## Goal

Make citations trustworthy. Users must be able to trace every RAG answer back to original source, page, and chunk.

## Tasks

### 9.1 Replace Mock Citation Data

* [x] Stop using mock citation data on citation screens.
* [x] Load citations from backend response and database.
* [x] Store citation metadata:

```text
citation_id
answer_id
thread_id
document_id
chunk_id
page
section
snippet
confidence
created_at
```

### 9.2 Citation Panel in Chat

* [x] Show citations under answer.
* [x] Each citation should include:

```text
Document title
Page number
Short snippet
Source type
Open original button
```

### 9.3 Open Original

* [x] Implement PDF/document viewer.
* [x] Open correct document.
* [x] Jump to correct page.
* [x] Highlight cited snippet if possible.
* [x] For image/scan, show page image.
* [x] For DOCX, show extracted section or converted preview.

### 9.4 Download Source

* [x] Add Download Source button.
* [x] Check permission before download.
* [x] Audit download action if PHI or restricted document.
* [x] If user lacks permission, block download.

### 9.5 Copy Citation

* [x] Add Copy Citation button.
* [x] Format citation consistently:

```text
Document title, page, section, retrieved date/thread.
```

## Acceptance Criteria

* [x] Every RAG answer has clickable citations.
* [x] Citation opens original document/page.
* [x] Download source works for authorized users.
* [x] Unauthorized users cannot open or download restricted sources.
* [x] Citation viewer uses backend document/page/chunk data.
* [x] Citation failure results in safe warning, not silent broken UI.

## Exceptions / Edge Cases

* If original document is missing, show source unavailable.
* If page number is unavailable, open document detail with snippet.
* If snippet cannot be highlighted, still show correct page.
* If user loses permission after answer was generated, citation access must be re-checked.
* If citation confidence is low, label it as weak evidence.

---

# Phase 10 — Header Global Search

## Goal

Make the header search functional across the system, with results filtered by role and permission.

## Tasks

### 10.1 Create Global Search API

* [x] Add or connect endpoint:

```http
GET /search?q=...
```

* [x] Search across:

```text
Patients
Documents
Chats
Citations
Audit traces
Access requests
Graph nodes
```

* [x] Return grouped results:

```json
{
  "patients": [],
  "documents": [],
  "threads": [],
  "citations": [],
  "audit_traces": [],
  "access_requests": [],
  "graph_nodes": []
}
```

### 10.2 Role-Aware Search Results

* [x] Pharmacist searching `apixaban` can see medication documents and accessible patient context.
* [x] Admin searching `tr-001` can see audit trace.
* [x] Nurse can see guideline documents and assigned patient data.
* [x] Restricted results should not leak names, MRNs, or snippets.

### 10.3 Frontend Search UI

* [x] Create dropdown/command palette.
* [x] Show grouped results.
* [x] Add keyboard navigation.
* [x] Add loading state.
* [x] Add empty state.
* [x] Press Enter opens best result or full results page.
* [x] Clicking result navigates to appropriate page.

## Acceptance Criteria

* [x] Header search returns real backend data.
* [x] Search results are grouped by type.
* [x] Restricted data is not leaked.
* [x] Search works for patients, docs, chats, and audit traces.
* [x] Search opens correct detail pages.
* [x] Search input is no longer decorative.

## Exceptions / Edge Cases

* If query is shorter than 2 characters, do not search or show recent results.
* If API fails, show search unavailable.
* If result becomes inaccessible after search, show access denied page.
* If multiple patients have same name, show disambiguating non-sensitive metadata only if allowed.

---

# Phase 11 — Dashboard, Metrics, Charts, and AI Insight

## Goal

Replace scattered mock dashboard data with consistent backend/seed data, then add lightweight AI insight under each chart.

## Current Problem

Frontend dashboard/charts use static data from files while backend has `/dashboard/summary`.

## Tasks

### 11.1 Create Consistent Seed Data

* [x] Seed users.
* [x] Seed workspaces.
* [x] Seed patients.
* [x] Seed documents.
* [x] Seed document chunks.
* [x] Seed chat threads.
* [x] Seed chat messages.
* [x] Seed citations.
* [x] Seed audit logs.
* [x] Seed access requests.
* [x] Seed graph nodes/edges.
* [x] Seed metrics snapshots.

### 11.2 Backend-Backed Dashboard

* [x] Connect dashboard to:

```text
/dashboard/summary
/dashboard/metrics
/dashboard/recent-patients
/dashboard/recent-threads
/documents/recent
```

* [x] Remove static dashboard data imports.
* [x] Ensure dashboard numbers match DB counts.
* [x] Update metrics when user performs key actions:

```text
chat query
document upload
document indexed
citation generated
access denied
access request submitted
```

### 11.3 Important Metrics

Show metrics such as:

* [x] Citation rate.
* [x] Safe refusal rate.
* [x] Denied/unauthorized access count.
* [x] Unauthorized chunks sent to LLM.
* [x] P95 latency.
* [x] Average summary time.
* [x] Indexed documents.
* [x] Failed documents.
* [x] Query volume.
* [x] Helpful feedback.
* [x] Estimated time saved.

Most important safety metric:

```text
Unauthorized chunks sent to LLM = 0
```

### 11.4 AI Analyze Button Under Charts

* [x] Add button under each chart:

```text
Analyze with AI
```

* [x] Phase 1 implementation should be rule-based.
* [x] Use aggregate non-PHI metrics only.
* [x] Display one short insight line under the chart.

Example:

```text
AI insight: Citation rate improved by 1.2% this week, indicating stronger source grounding.
```

* [x] If later using LLM, audit event:

```text
dashboard.insight.generate
```

## Acceptance Criteria

* [x] Dashboard no longer depends on unrelated mock data.
* [x] Chart values match backend data.
* [x] Recent patients match patient database.
* [x] Recent documents match document database.
* [x] Recent threads match chat database.
* [x] Analyze with AI produces a short useful insight.
* [x] Insight uses aggregate metrics only.

## Exceptions / Edge Cases

* If metric has no prior period, show “No comparison available.”
* If data volume is too low, insight should mention limited sample.
* If metric is PHI-related, do not send raw patient data to insight generator.
* If backend summary fails, show retry state instead of fake numbers.

---

# Phase 12 — Knowledge Graph / Clinical Reasoning Graph

## Goal

Turn Graph RAG from a hardcoded visual demo into a backend-backed explainability feature that shows relationships between patient, diagnosis, medication, lab, document evidence, and reasoning path.

## Recommended Rename

Use one of:

```text
Knowledge Graph
Clinical Reasoning Graph
```

Avoid exposing the technical term “Graph RAG” to clinical users.

## Tasks

### 12.1 Connect Graph to Backend

* [x] Stop using hardcoded `data/graph.ts`.
* [x] Add or connect endpoint:

```http
GET /graph/patients/:patient_id
```

* [x] Response should include:

```json
{
  "nodes": [],
  "edges": [],
  "reasoning_path": [],
  "metadata": {
    "patient_id": "p-001",
    "updated_at": "2026-06-11",
    "node_count": 12,
    "edge_count": 11
  }
}
```

### 12.2 Node Types

Support node types:

* [x] Patient.
* [x] Encounter.
* [x] Diagnosis.
* [x] Medication.
* [x] Allergy.
* [x] Lab.
* [x] Document.
* [x] Provider.

### 12.3 Edge Types

Support relationships:

* [x] diagnosed with.
* [x] treated with.
* [x] allergic to.
* [x] lab result.
* [x] documented in.
* [x] supports.
* [x] contraindicates.
* [x] adjusted by.
* [x] evidence for.

### 12.4 Node Detail Side Panel

* [x] Click node opens side panel.
* [x] Side panel shows:

```text
Node label
Node type
Clinical summary
Related evidence
Connected nodes
Source citations
Ask about this node
Highlight neighborhood
```

### 12.5 Edge Detail

* [x] Click edge shows relationship evidence.
* [x] Show why two nodes are connected.
* [x] Show source document/page if available.

### 12.6 Graph Controls

* [x] Zoom in.
* [x] Zoom out.
* [x] Reset view.
* [x] Fullscreen.
* [x] Fit to screen.
* [x] Filter by node type.
* [x] Highlight reasoning path.

### 12.7 Export and Share

Phase 1:

* [x] Export PNG.
* [x] Export JSON.

Phase 2:

* [x] Export PDF report.
* [x] Share permission-aware snapshot.

## Acceptance Criteria

* [x] Graph data comes from backend DB.
* [x] Graph supports any accessible patient, not only p-001.
* [x] Click node opens detail side panel.
* [x] Click edge shows relationship evidence.
* [x] Fullscreen works.
* [x] Export PNG works.
* [x] Export JSON works.
* [x] Restricted patient graph is blocked.

## Exceptions / Edge Cases

* If graph has no nodes, show empty state.
* If user lacks patient access, show access request option.
* If node evidence is missing, label as extracted relationship with low confidence.
* If graph is too large, load neighborhood view first.
* If export contains PHI, require permission and audit export.

---

# Phase 13 — Audit Logs, Trace Detail, Export, and Signed Digest

## Goal

Make audit/compliance features functional and convincing. Audit should show who accessed what, what AI did, what data was retrieved, and whether permissions were enforced.

## Tasks

### 13.1 Audit Log Search

* [x] Connect audit log page to backend.
* [x] Search by:

```text
user
action
target
category
result
IP
trace_id
time range
```

* [x] Filters:

```text
Last 24h
PHI only
AI only
Denied only
Pending only
Admin actions
```

### 13.2 Audit Export

* [x] Implement Export button.
* [x] Support CSV.
* [x] Support JSON.
* [x] Optionally support PDF later.
* [x] Export respects filters.
* [x] Audit the export action.

### 13.3 View Signed Digest

* [x] Implement signed digest page or modal.
* [x] Display:

```text
Digest ID
Generated at
Time range
Total events
Hash algorithm
Signature status
Verification status
Download digest
Verify integrity
```

* [x] If signature is demo-only, label clearly.

### 13.4 Trace Detail Page

For route:

```text
/audit/traces/:trace_id
```

* [x] Add back button:

```text
← Back to Audit logs
```

* [x] Show trace spans:

```text
POST /api/chat
Auth - verify session
Permission - ABAC eval
Audit - log query
Retrieval - hybrid search
LLM - generate
Citation - resolve sources
```

* [x] Allow click on each span.
* [x] Show span detail panel.

### 13.5 Trace Span Detail

For Permission span, show:

```text
Decision
Policy
User role
Workspace
Patient context
Allowed scopes
Denied scopes
```

For Retrieval span, show:

```text
Query
Retrieved chunks
Allowed chunks
Blocked chunks
Top source IDs
Hybrid score summary
```

For LLM span, show:

```text
Model
Latency
Token count
Safety mode
Prompt classification
```

Do not show raw PHI prompt unless user is authorized.

## Acceptance Criteria

* [x] Audit search works.
* [x] Filters work.
* [x] Export works.
* [x] Signed digest opens.
* [x] Trace page has back navigation.
* [x] Trace spans are clickable.
* [x] Permission/retrieval metadata is visible.
* [x] AI query and denied access are logged.

## Exceptions / Edge Cases

* If user is not Admin/Compliance, block audit access.
* If digest is unavailable, show not generated state.
* If trace is missing, show 404 with back to audit.
* If span contains PHI, mask details for unauthorized viewers.
* If export is too large, generate async export job.

---

# Phase 14 — Patients, Add Patient, Filters, and Patient Detail

## Goal

Make Patients page interactive enough for portfolio demo and ensure patient access status is accurate.

## Tasks

### 14.1 Patients API Integration

* [x] Replace mock patient list with backend patients API.
* [x] Filter by:

```text
name
MRN
condition
unit
status
access state
```

* [x] Show counts:

```text
total in workspace
accessible
restricted
```

### 14.2 Add Patient

* [x] Implement Add Patient button.
* [x] Option A: modal.
* [x] Option B: route `/patients/new`.

Fields:

```text
Full name
MRN
Age/DOB
Sex
Unit
Condition
Assigned team
Access policy
```

* [x] Validate required fields.
* [x] Prevent duplicate MRN.
* [x] Save to backend.
* [x] Add audit event.

### 14.3 Open Chat from Patient Row

* [x] Open global chat with patient context:

```text
/chat?patient=p-001
```

* [x] Do not open a separate patient chat engine.
* [x] If user lacks access, open access request prompt.

### 14.4 Patient Detail

* [x] Show demographics.
* [x] Show access status.
* [x] Show linked documents.
* [x] Show recent encounters.
* [x] Show medication summary if permitted.
* [x] Show button:

```text
Ask AI about this patient
```

## Acceptance Criteria

* [x] Patients table uses backend data.
* [x] Search/filter works.
* [x] Add patient works.
* [x] Duplicate MRN is blocked.
* [x] Open chat uses global chat with context.
* [x] Restricted patient data is not leaked.
* [x] Patient actions are audited.

## Exceptions / Edge Cases

* If user lacks permission, show restricted row with minimal metadata.
* If patient is archived/discharged, label status.
* If patient creation fails, show validation error.
* If backend is read-only in demo, hide Add Patient or label as disabled.

---

# Phase 15 — Chat File Attachment

## Goal

Make the paperclip attachment in chat functional. Users should be able to attach documents and ask questions about them.

## Tasks

### 15.1 Phase 1 Attachment Behavior

Since backend upload currently stores documents in patient knowledge base, implement:

```text
Attach file in chat
→ Upload to documents backend
→ If patient context exists, link document to patient
→ Process/index document
→ Allow chat to retrieve from the document after indexing
```

### 15.2 UI

* [x] Clicking paperclip opens file picker.
* [x] Show attached file card:

```text
renal-dose-note.pdf
Processing...
```

* [x] Show final status:

```text
Indexed
Error
```

* [x] Allow remove attachment before sending if not uploaded yet.
* [x] Show warning if file will be added to knowledge base.

### 15.3 Backend Integration

* [x] Upload file.
* [x] Receive document ID.
* [x] Poll processing status.
* [x] Add document ID to chat context.
* [x] Chat request includes attached document IDs.

### 15.4 Future Session-Only Attachments

* [x] Add planned feature for session-only attachments.
* [x] Session-only files should not become hospital-wide knowledge.
* [x] Session-only files expire after thread/session.

## Acceptance Criteria

* [x] Paperclip button works.
* [x] File uploads successfully.
* [x] Processing status is visible.
* [x] Indexed file can be used in chat answer.
* [x] Chat answer cites attached file.
* [x] Upload failure is handled.

## Exceptions / Edge Cases

* If file is too large, reject before upload.
* If file type unsupported, reject clearly.
* If OCR/indexing fails, allow user to retry or remove.
* If file contains PHI and redaction is not implemented, show warning.
* If user lacks permission to upload to patient KB, block action.

---

# Phase 16 — Medication Safety Page

## Goal

Make the Medication Safety page meaningful for the Pharmacist persona and connect it to chat, documents, patient data, and graph.

## Tasks

* [x] Define medication safety scope:

```text
renal dose review
drug-drug interaction
allergy conflict
duplicate therapy
contraindication
high-risk medication monitoring
```

* [x] Load medication-related patients from backend.
* [x] Show medication safety alerts.
* [x] Allow filtering by severity.
* [x] Click alert opens detail.
* [x] Detail shows:

```text
patient
medication
risk
supporting lab/allergy/diagnosis
citation/evidence
recommended next step
```

* [x] Add action:

```text
Ask AI about this medication risk
```

* [x] Route to global chat with medication context.
* [x] Audit alert review.

## Acceptance Criteria

* [x] Medication Safety page is not static.
* [x] Pharmacist can see medication-relevant alerts.
* [x] Alert detail has evidence.
* [x] Chat can answer based on alert context.
* [x] Restricted patient data remains protected.

## Exceptions / Edge Cases

* If no medication alerts exist, show empty state.
* If alert evidence is missing, label low confidence.
* If user lacks patient access, show access request instead of details.

---

# Phase 17 — API Contract and Frontend Data Layer

## Goal

Create a stable frontend-backend contract so pages stop depending on scattered mock imports.

## Tasks

### 17.1 Central API Client

* [x] Create central API client with auth token handling.
* [x] Add request interceptors.
* [x] Add response error handling.
* [x] Add automatic logout on 401.
* [x] Add typed API functions.

### 17.2 API Modules

Create modules:

```text
authApi
chatApi
patientApi
documentApi
citationApi
searchApi
graphApi
auditApi
accessRequestApi
dashboardApi
metricsApi
```

### 17.3 Replace Mock Imports

* [x] Replace `data/patients` usage.
* [x] Replace `data/documents` usage.
* [x] Replace `data/threads` usage.
* [x] Replace `data/metrics` usage.
* [x] Replace `data/graph.ts` usage.

### 17.4 Mock Fallback Policy

* [x] Avoid silent fallback to mock data.
* [x] If demo mode uses seed data, serve it from backend seed DB.
* [x] If API fails, show error state.

## Acceptance Criteria

* [x] Frontend uses API modules.
* [x] Mock data files are removed or clearly limited to Storybook/dev.
* [x] API errors are consistent.
* [x] Auth token is attached to protected API calls.
* [x] No sensitive page silently falls back to fake data.

## Exceptions / Edge Cases

* If running frontend without backend, show backend unavailable.
* If demo data is required for tests, isolate it in test fixtures.
* If API contract changes, TypeScript/types should fail early.

---

# Phase 18 — Testing Strategy

## Goal

Ensure core flows work reliably and permission/security behavior is not accidentally broken.

## Test Types

### 18.1 Unit Tests

* [x] Permission policy evaluation.
* [x] Role/workspace derivation.
* [x] Citation formatting.
* [x] Session memory summary update.
* [x] Chart insight rule generation.
* [x] Search result grouping.
* [x] Access request state transition.

### 18.2 Integration Tests

* [x] Login → `/auth/token` → `/auth/me`.
* [x] Chat message with citation.
* [x] Chat no-access safe refusal.
* [x] Document upload → processing → indexed.
* [x] Document search returns uploaded document.
* [x] Citation open original.
* [x] Access request submit → approve → chat allowed.
* [x] Audit log generated for AI query.
* [x] Trace generated for chat query.
* [x] Graph loaded from backend.

### 18.3 End-to-End Tests

Golden demo flow:

* [x] Login as Pharmacist.
* [x] Open `/chat`.
* [x] Click suggestion.
* [x] Confirm suggestion fills input only.
* [x] Send query.
* [x] Receive cited answer.
* [x] Attach file.
* [x] Wait for indexing.
* [x] Ask about attached file.
* [x] Open citation.
* [x] Search header for `apixaban`.
* [x] Open Knowledge Graph.
* [x] Click Apixaban node.
* [x] Open Audit.
* [x] Search query log.
* [x] Open trace.
* [x] Click retrieval span.

### 18.4 Security Tests

* [x] Pharmacist cannot access full unrelated patient notes.
* [x] Admin cannot access PHI by default.
* [x] Unauthorized chunks count remains zero sent to LLM.
* [x] Restricted document does not appear in search.
* [x] Expired access blocks future chat.
* [x] Direct URL to restricted page returns access denied.

## Acceptance Criteria

* [x] P0 flows have automated tests.
* [x] Permission tests pass.
* [x] Golden demo flow works end to end.
* [x] Broken API calls do not show fake data.
* [x] No unauthorized chunk reaches LLM in test scenarios.

## Exceptions / Edge Cases

* If OCR is unavailable in CI, mock OCR service but test pipeline state.
* If LLM is unavailable, use deterministic test model/stub.
* If vector DB is unavailable, use seeded hybrid search fixture for tests.

---

# Phase 19 — Portfolio Demo Polish

## Goal

Make the final product feel intentional, credible, and easy for reviewers to understand.

## Tasks

### 19.1 Demo Story

Prepare a guided scenario:

```text
Persona: Pharmacist
Task: Review apixaban renal dosing
Evidence: DOAC protocol + patient renal lab
Safety: Permission enforced
Explainability: Knowledge Graph
Compliance: Audit trace
```

### 19.2 Demo Data

* [x] Use synthetic data label clearly.
* [x] Ensure patient data, documents, graph, audit logs, and charts all match.
* [x] Seed one strong patient case:

```text
Eleanor Vance
AFib
Apixaban
CKD stage 3
Creatinine 1.6
eGFR 42
Sulfa allergy
ACC/AHA guideline
DOAC renal dosing document
```

### 19.3 UI Labels

* [x] Replace technical labels where needed.
* [x] Add short helper text.
* [x] Label demo-only features.
* [x] Remove false claims.
* [x] Add “AI can make mistakes. Verify important information.”

### 19.4 README / Portfolio Explanation

Create README sections:

```text
Overview
Architecture
Key Features
Demo Personas
Security and Permissions
RAG and Citation Flow
Knowledge Graph Explainability
Audit and Compliance
Known Limitations
Future Improvements
How to Run Locally
```

### 19.5 Known Limitations

Clearly list:

```text
PHI redaction planned if not implemented
Break-glass planned/demo only
Session-only attachments planned
PDF graph export planned
Multi-role users not implemented
```

## Acceptance Criteria

* [x] Reviewer can understand the product in less than 2 minutes.
* [x] Golden demo flow works without manual database fixes.
* [x] UI does not overclaim features.
* [x] README honestly explains what is real, demo, and planned.
* [x] Screenshots match the actual working product.

## Exceptions / Edge Cases

* If a feature is not finished, hide it or label it planned.
* If a button is visible, it should either work or explain why disabled.
* If demo seed fails, app should provide reset seed command.

---

# Final Completion Checklist

## P0 Completion

* [x] Auth flow works.
* [x] Demo Persona Login is separate.
* [x] No in-app role/workspace switching.
* [x] Header layout fixed.
* [x] Chat suggestion fills input only.
* [x] Global `/chat` is canonical.
* [x] Chat sends `thread_id`.
* [x] Session memory works within thread.
* [x] Permission filter happens before LLM.
* [x] Unauthorized chunks sent to LLM equals zero.
* [x] Patient/RAG answers cite sources or safely refuse.
* [x] Access requests are pending approval by default.
* [x] Document upload works.
* [x] Document search works.
* [x] Citation open original works.
* [x] Header global search works.
* [x] Back buttons exist on detail pages.

## P1 Completion

* [x] Dashboard uses backend/seed DB.
* [x] Charts match DB data.
* [x] Analyze with AI button works under charts.
* [x] Knowledge Graph uses backend nodes/edges.
* [x] Node detail side panel works.
* [x] Graph fullscreen works.
* [x] Graph PNG/JSON export works.
* [x] Audit search works.
* [x] Audit export works.
* [x] Trace span drill-down works.
* [x] Admin PHI bypass removed.
* [x] Patient Add button works.

## P2 Completion

* [x] PHI redaction implemented or claim removed.
* [x] Signed digest viewer works.
* [x] Session-only chat attachments planned or implemented.
* [x] Break-glass either implemented properly or labeled planned.
* [x] PDF graph export planned or implemented.
* [x] Multi-role user model documented as future work.

---

# Definition of Done

The project is considered complete for portfolio demo when:

* [x] The app can be run locally with seeded synthetic data.
* [x] Login works for at least three personas: Pharmacist, Cardiologist, Admin.
* [x] Role and workspace are fixed after login.
* [x] Chat works as one global assistant.
* [x] Chat uses thread memory.
* [x] Chat answers are permission-aware.
* [x] Chat answers include citations or safe refusal.
* [x] Upload/search/citation/document open flows work.
* [x] Dashboard and charts use backend-backed data.
* [x] AI chart insight works with aggregate metrics.
* [x] Knowledge Graph explains reasoning path with backend data.
* [x] Audit log records AI query, permission check, retrieval, citation, and access decisions.
* [x] Trace page shows backend execution spans.
* [x] No visible button is completely dead.
* [x] No UI claim contradicts backend behavior.
* [x] README clearly explains real features, demo features, and planned features.
