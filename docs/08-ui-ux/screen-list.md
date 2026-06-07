# Screen List

> Project: AI-Powered Hospital Knowledge Assistant  
> Version: 2.0  
> Owner: UI/UX Lead  
> Last updated: 2026-06-07  
> Status: In Review

This document is the **Product UI Truth** — the definitive catalog of all screens in the application. Each screen maps to its API endpoints, use cases, test cases, and design reference image.

---

## Screen Summary by Domain

| Domain | Count | Screens |
|---|---|---|
| auth | 2 | SCR-001, SCR-002 |
| dashboard | 3 | SCR-003, SCR-004, SCR-005 |
| patients | 5 | SCR-006, SCR-007, SCR-008, SCR-009, SCR-010 |
| chat | 4 | SCR-011, SCR-012, SCR-013, SCR-014 |
| documents | 4 | SCR-015, SCR-016, SCR-017, SCR-018 |
| citations | 1 | SCR-019 |
| search | 1 | SCR-020 |
| access-control | 2 | SCR-021, SCR-022 |
| audit | 1 | SCR-023 |
| metrics | 1 | SCR-024 |
| users | 2 | SCR-025, SCR-026 |
| workspaces | 1 | SCR-027 |

---

## Screen Catalog

### Auth Domain

#### SCR-001: Staff SSO Email/Password Login
- **Route**: `/login`
- **Actor**: Guest / Unauthenticated user
- **Purpose**: Authenticate hospital staff via email/password or SSO
- **Screenshot**: [`auth.login.staff-sso-email-password.png`](../screen-design/auth.login.staff-sso-email-password.png)
- **Data required**: Email, password, SSO provider list
- **Actions**: Submit credentials, SSO redirect, forgot password
- **Related APIs**: `POST /api/v1/auth/login` (Chatbot), `POST /api/v1/auth/login` (HMS)
- **Related UC**: UC-001 (implied — auth is precondition for all UCs)
- **Related FR**: FR-001
- **Related TC**: TC-001
- **Related BR**: BR-004 (permission-aware retrieval requires auth)

#### SCR-002: MFA Verify Identity Code
- **Route**: `/login/mfa`
- **Actor**: Partially authenticated user
- **Purpose**: Second-factor verification via code entry
- **Screenshot**: [`auth.mfa.verify-identity-code.png`](../screen-design/auth.mfa.verify-identity-code.png)
- **Data required**: MFA code, session token
- **Actions**: Enter code, resend code, cancel
- **Related APIs**: `POST /api/v1/auth/mfa/verify` (Chatbot)
- **Related UC**: UC-001 (precondition)
- **Related FR**: FR-001
- **Related TC**: TC-001
- **Related BR**: BR-004

---

### Dashboard Domain

#### SCR-003: Populated HMS-AI Workspace
- **Route**: `/dashboard`
- **Actor**: Authenticated staff (Doctor, Nurse, Pharmacist)
- **Purpose**: Main workspace showing recent activity, quick actions, and system status
- **Screenshot**: [`dashboard.overview.populated-hms-ai-workspace.png`](../screen-design/dashboard.overview.populated-hms-ai-workspace.png)
- **Data required**: Recent patients, recent chats, document stats, metric summary
- **Actions**: Navigate to patient, start chat, upload document, view metrics
- **Related APIs**: `GET /api/v1/auth/me`, `GET /api/v1/metrics/productivity`, `GET /api/v1/patients/search`
- **Related UC**: UC-009 (metrics), UC-001 (quick patient access)
- **Related FR**: FR-009, FR-003
- **Related TC**: TC-010
- **Related BR**: BR-005

#### SCR-004: Action Success Toast
- **Route**: `/dashboard` (overlay)
- **Actor**: Authenticated staff
- **Purpose**: Confirm successful completion of an action (e.g., document upload, summary generated)
- **Screenshot**: [`dashboard.overview.action-success-toast.png`](../screen-design/dashboard.overview.action-success-toast.png)
- **Data required**: Action result message
- **Actions**: Dismiss toast, undo (if applicable)
- **Related APIs**: N/A (UI state only)
- **Related UC**: Multiple — toast appears after any successful action
- **Related FR**: N/A (UI feedback pattern)
- **Related TC**: TBD — needs UI test
- **Related BR**: N/A

#### SCR-005: Workspace Onboarding / Empty State
- **Route**: `/dashboard` (first use)
- **Actor**: New authenticated staff
- **Purpose**: Guide first-time users to upload first document or search first patient
- **Screenshot**: [`dashboard.empty.workspace-onboarding-first-data.png`](../screen-design/dashboard.empty.workspace-onboarding-first-data.png)
- **Data required**: Onboarding checklist state
- **Actions**: Upload document, search patient, start chat
- **Related APIs**: `GET /api/v1/auth/me`
- **Related UC**: UC-003 (first upload), UC-001 (first question)
- **Related FR**: FR-003, FR-006
- **Related TC**: TBD — needs onboarding test
- **Related BR**: BR-001

---

### Patients Domain

#### SCR-006: Patient List with Scoped Alerts
- **Route**: `/patients`
- **Actor**: Doctor, Nurse (scoped)
- **Purpose**: View authorized patients with alerts and recent activity
- **Screenshot**: [`patients.list.scoped-alerts-recent-activity.png`](../screen-design/patients.list.scoped-alerts-recent-activity.png)
- **Data required**: Patient list (name, MRN, DOB, department, alerts), pagination
- **Actions**: Search, filter, select patient, sort
- **Related APIs**: `GET /api/v1/patients/search` (Chatbot BFF) → `GET /api/v1/patients` (HMS)
- **Related UC**: UC-001 (precondition — select patient)
- **Related FR**: FR-003
- **Related TC**: TC-003
- **Related BR**: BR-001, BR-004

#### SCR-007: Patient Overview with AI Summary
- **Route**: `/patients/:id`
- **Actor**: Doctor, Nurse (scoped)
- **Purpose**: View patient overview including AI-generated summary with HMS data snapshot
- **Screenshot**: [`patients.overview.ai-summary-hms-snapshot.png`](../screen-design/patients.overview.ai-summary-hms-snapshot.png)
- **Data required**: Patient demographics, encounters, diagnoses, medications, allergies, labs, AI summary
- **Actions**: Generate/refresh summary, view citations, navigate to detail sections
- **Related APIs**: `GET /api/v1/patients/{id}` (Chatbot BFF) → `GET /api/v1/patient-records/{patientId}` (HMS), `POST /api/v1/patients/{id}/summary` (Chatbot)
- **Related UC**: UC-002 (generate patient summary)
- **Related FR**: FR-008, FR-005
- **Related TC**: TC-008, TC-009
- **Related BR**: BR-002

#### SCR-008: Medication Review with Cited Safety Answer
- **Route**: `/patients/:id/medications`
- **Actor**: Doctor, Pharmacist (scoped)
- **Purpose**: Review medications with AI-cited safety analysis (drug interactions, allergies)
- **Screenshot**: [`patients.medication-review.cited-safety-answer.png`](../screen-design/patients.medication-review.cited-safety-answer.png)
- **Data required**: Medication list, allergy list, AI safety analysis with citations
- **Actions**: Review warnings, view citation sources, dismiss/acknowledge warnings
- **Related APIs**: `POST /api/v1/medication/check` (Chatbot), `GET /api/v1/patients/{id}` → medications/allergies
- **Related UC**: UC-006 (drug/allergy pre-check)
- **Related FR**: FR-012
- **Related TC**: TC-013
- **Related BR**: BR-007

#### SCR-009: Patient Empty State
- **Route**: `/patients` (no results)
- **Actor**: Any scoped staff
- **Purpose**: Show when no patients match search or user has no access
- **Screenshot**: [`patients.empty.no-results-or-no-access.png`](../screen-design/patients.empty.no-results-or-no-access.png)
- **Data required**: Search query (if any), access scope info
- **Actions**: Modify search, request access
- **Related APIs**: `GET /api/v1/patients/search` (returns empty)
- **Related UC**: UC-001 (alternate flow — no results)
- **Related FR**: FR-003
- **Related TC**: TC-003 (empty result variant)
- **Related BR**: BR-004

#### SCR-010: AI Summary Stream with Citations Retrieving
- **Route**: `/patients/:id` (loading state)
- **Actor**: Doctor, Nurse (scoped)
- **Purpose**: Show streaming AI summary generation with citation retrieval progress
- **Screenshot**: [`patients.ai-summary.stream-citations-retrieving.png`](../screen-design/patients.ai-summary.stream-citations-retrieving.png)
- **Data required**: Streaming response chunks, retrieval status, citation count
- **Actions**: Cancel generation, wait for completion
- **Related APIs**: `POST /api/v1/patients/{id}/summary` (streaming response)
- **Related UC**: UC-002 (main flow — generating state)
- **Related FR**: FR-008
- **Related TC**: TC-008
- **Related BR**: BR-002

---

### Chat Domain

#### SCR-011: New Patient Context Thread
- **Route**: `/chat/new`
- **Actor**: Doctor, Nurse, Pharmacist (scoped)
- **Purpose**: Start a new chat conversation with patient context selection
- **Screenshot**: [`chat.workspace.new-patient-context-thread.png`](../screen-design/chat.workspace.new-patient-context-thread.png)
- **Data required**: Patient selector, thread list, scope indicator
- **Actions**: Select patient context, type question, select general mode
- **Related APIs**: `POST /api/v1/chat-threads` (Chatbot), `GET /api/v1/patients/search`
- **Related UC**: UC-001 (ask patient question)
- **Related FR**: FR-004, FR-003
- **Related TC**: TC-004
- **Related BR**: BR-001

#### SCR-012: Safe Refusal — Insufficient Evidence
- **Route**: `/chat/:threadId` (answer state)
- **Actor**: Any scoped staff
- **Purpose**: Display AI safe refusal when evidence is insufficient to answer
- **Screenshot**: [`chat.answer.safe-refusal-insufficient-evidence.png`](../screen-design/chat.answer.safe-refusal-insufficient-evidence.png)
- **Data required**: Refusal message, reason, available evidence count
- **Actions**: Rephrase question, upload more documents, accept refusal
- **Related APIs**: `POST /api/v1/chat` (returns `422 INSUFFICIENT_EVIDENCE`)
- **Related UC**: UC-001 (alternate flow — no evidence)
- **Related FR**: FR-004
- **Related TC**: TC-005
- **Related BR**: BR-001 (cited answers requirement includes safe refusal)

#### SCR-013: AI HMS Copilot Landing
- **Route**: `/chat`
- **Actor**: Any authenticated staff
- **Purpose**: Chat landing page for general clinical assistant (no patient context)
- **Screenshot**: [`chat.landing.ai-hms-copilot.png`](../screen-design/chat.landing.ai-hms-copilot.png)
- **Data required**: Suggested prompts, recent threads
- **Actions**: Start general conversation, select patient context, browse threads
- **Related APIs**: `GET /api/v1/chat-threads`, `POST /api/v1/chat`
- **Related UC**: UC-001 (general mode)
- **Related FR**: FR-004
- **Related TC**: TC-004 (general mode variant)
- **Related BR**: BR-001

#### SCR-014: Chat Cited Answer (implied from AI Answer Pattern)
- **Route**: `/chat/:threadId` (answer state)
- **Actor**: Any scoped staff
- **Purpose**: Display AI answer with citations, confidence, and disclaimer
- **Screenshot**: N/A — pattern documented in design system, visible in SCR-011 and SCR-012
- **Data required**: Answer text, citations array, confidence level, disclaimer
- **Actions**: Click citation to open evidence panel, rate answer, continue thread
- **Related APIs**: `POST /api/v1/chat`
- **Related UC**: UC-001, UC-005 (view citations)
- **Related FR**: FR-004, FR-005
- **Related TC**: TC-004
- **Related BR**: BR-001

> [!NOTE]
> SCR-014 does not have a dedicated screenshot — the pattern is visible across multiple screens. Consider merging with SCR-011 or creating a dedicated screenshot.

---

### Documents Domain

#### SCR-015: OCR Indexing & Semantic Search Dashboard
- **Route**: `/documents`
- **Actor**: Records staff, Admin
- **Purpose**: View document indexing status, OCR results, and run semantic searches
- **Screenshot**: [`documents.dashboard.ocr-indexing-semantic-search.png`](../screen-design/documents.dashboard.ocr-indexing-semantic-search.png)
- **Data required**: Document list with status (Uploaded/Processing/Indexed/Failed), search input
- **Actions**: Search documents, filter by status, view document detail
- **Related APIs**: `POST /api/v1/documents/search` (Chatbot), `GET /api/v1/documents` (list)
- **Related UC**: UC-004 (search documents)
- **Related FR**: FR-007
- **Related TC**: TC-007
- **Related BR**: BR-003

#### SCR-016: OCR Review — Needs Review / Low Confidence
- **Route**: `/documents/:id/review`
- **Actor**: Records staff
- **Purpose**: Review OCR output with low confidence scores, approve or flag for re-scan
- **Screenshot**: [`documents.ocr-review.needs-review-low-confidence.png`](../screen-design/documents.ocr-review.needs-review-low-confidence.png)
- **Data required**: Document pages, OCR text per page, confidence scores, original image
- **Actions**: Approve OCR, flag for re-scan, edit OCR text, reject
- **Related APIs**: `GET /api/v1/documents/{id}/pages/{page}`, `PATCH /api/v1/documents/{id}` (TBD — status update)
- **Related UC**: UC-003 (alternate flow — OCR failed/low confidence)
- **Related FR**: FR-006
- **Related TC**: TC-006, TC-007
- **Related BR**: BR-003

#### SCR-017: Batch Upload with OCR Progress Modal
- **Route**: `/documents/upload` (modal)
- **Actor**: Records staff
- **Purpose**: Upload multiple documents and track OCR processing progress
- **Screenshot**: [`documents.upload.batch-ocr-progress-modal.png`](../screen-design/documents.upload.batch-ocr-progress-modal.png)
- **Data required**: File list, upload progress, OCR job status per file
- **Actions**: Add files, start upload, cancel, retry failed
- **Related APIs**: `POST /api/v1/documents` (Chatbot — upload)
- **Related UC**: UC-003 (upload and OCR document)
- **Related FR**: FR-006
- **Related TC**: TC-006
- **Related BR**: BR-003

#### SCR-018: Document Pages / Source Preview (implied)
- **Route**: `/documents/:id/pages/:page`
- **Actor**: Any scoped staff
- **Purpose**: Preview original document source (PDF page) for citation verification
- **Screenshot**: N/A — combined with SCR-019 citation viewer
- **Data required**: Original document image/PDF, OCR text overlay, page metadata
- **Actions**: Navigate pages, zoom, compare OCR text to original
- **Related APIs**: `GET /api/v1/documents/{id}/pages/{page}`
- **Related UC**: UC-005 (view citations/source page)
- **Related FR**: FR-005
- **Related TC**: TC-004 (citation verification)
- **Related BR**: BR-001

> [!NOTE]
> SCR-018 may be merged with SCR-019 (citation viewer) since they share the source preview function.

---

### Citations Domain

#### SCR-019: Verified Source Document Viewer
- **Route**: `/citations/:citationId` or side panel
- **Actor**: Any scoped staff
- **Purpose**: View the verified source document/page/chunk that backs a citation
- **Screenshot**: [`citations.viewer.verified-source-document.png`](../screen-design/citations.viewer.verified-source-document.png)
- **Data required**: Citation metadata, source document, page number, highlighted chunk
- **Actions**: Navigate to source page, view full document, verify claim
- **Related APIs**: `GET /api/v1/documents/{id}/pages/{page}` (Chatbot)
- **Related UC**: UC-005 (view citations/source page)
- **Related FR**: FR-005
- **Related TC**: TC-004
- **Related BR**: BR-001

---

### Search Domain

#### SCR-020: Global Command Palette with Recent Entities
- **Route**: Global overlay (Cmd+K / Ctrl+K)
- **Actor**: Any authenticated staff
- **Purpose**: Quick search across patients, documents, and threads
- **Screenshot**: [`search.global.command-palette-recent-entities.png`](../screen-design/search.global.command-palette-recent-entities.png)
- **Data required**: Search query, recent entities, search results grouped by type
- **Actions**: Type search, select result, navigate to entity
- **Related APIs**: `GET /api/v1/patients/search`, `POST /api/v1/documents/search`, `GET /api/v1/chat-threads`
- **Related UC**: UC-001, UC-004
- **Related FR**: FR-003, FR-007
- **Related TC**: TC-003 (search variant)
- **Related BR**: BR-001

---

### Access Control Domain

#### SCR-021: Access Denied — No Treatment Relationship
- **Route**: `/patients/:id` (denied state)
- **Actor**: Any staff without patient access
- **Purpose**: Block PHI access and show clear denial reason when no treatment relationship exists
- **Screenshot**: [`access-control.denied.no-treatment-relationship.png`](../screen-design/access-control.denied.no-treatment-relationship.png)
- **Data required**: Denial reason, patient ID (masked), request access option
- **Actions**: Request access, go back, contact admin
- **Related APIs**: `GET /api/v1/patients/{id}` (returns `403 FORBIDDEN`)
- **Related UC**: UC-001 (alternate flow — permission denied)
- **Related FR**: FR-002
- **Related TC**: TC-002
- **Related BR**: BR-004

#### SCR-022: Access Request — Clinical Justification Modal
- **Route**: `/access-requests/new` (modal from SCR-021)
- **Actor**: Any staff requesting elevated access
- **Purpose**: Submit clinical justification for accessing a patient's data
- **Screenshot**: [`access-requests.create.clinical-justification-modal.png`](../screen-design/access-requests.create.clinical-justification-modal.png)
- **Data required**: Patient ID, justification text, requesting role, urgency level
- **Actions**: Submit request, cancel, attach supporting context
- **Related APIs**: `POST /api/v1/access-requests` (TBD — new endpoint needed)
- **Related UC**: UC-001 (exception — request access after denial)
- **Related FR**: FR-002 (extended)
- **Related TC**: TBD — needs access request test
- **Related BR**: BR-004

---

### Audit Domain

#### SCR-023: Audit Logs — Access Event Detail Panel
- **Route**: `/audit/logs`
- **Actor**: Security, Admin
- **Purpose**: View audit log with access event details, trace IDs, and filtering
- **Screenshot**: [`audit.logs.access-event-detail-panel.png`](../screen-design/audit.logs.access-event-detail-panel.png)
- **Data required**: Audit event list (actor, action, object, timestamp, trace_id), filters
- **Actions**: Filter by date/user/action, view event detail, export
- **Related APIs**: `GET /api/v1/audit/events` (Chatbot)
- **Related UC**: UC-008 (review audit logs)
- **Related FR**: FR-010
- **Related TC**: TC-011
- **Related BR**: BR-005

---

### Metrics Domain

#### SCR-024: Impact Quality Summary Dashboard
- **Route**: `/metrics`
- **Actor**: PM, Admin
- **Purpose**: View AI impact metrics — time saved, cost saved, citation rate, quality indicators
- **Screenshot**: [`metrics.dashboard.impact-quality-summary.png`](../screen-design/metrics.dashboard.impact-quality-summary.png)
- **Data required**: Metric aggregations (MET-001 through MET-013), time series, comparisons
- **Actions**: Filter by date range, export, drill into metric detail
- **Related APIs**: `GET /api/v1/metrics/productivity` (Chatbot)
- **Related UC**: UC-009 (view impact metrics)
- **Related FR**: FR-009
- **Related TC**: TC-010
- **Related BR**: BR-005

---

### Users Domain

#### SCR-025: Profile, Security & System Status Preferences
- **Route**: `/settings/profile`
- **Actor**: Any authenticated staff
- **Purpose**: Manage user profile, security settings (password, MFA), and view system status
- **Screenshot**: [`users.preferences.profile-security-system-status.png`](../screen-design/users.preferences.profile-security-system-status.png)
- **Data required**: User profile, MFA status, notification preferences, system health
- **Actions**: Update profile, enable/disable MFA, change password
- **Related APIs**: `GET /api/v1/auth/me`, `PATCH /api/v1/users/me` (TBD), `GET /api/v1/system/health` (TBD)
- **Related UC**: TBD — needs settings UC
- **Related FR**: FR-001 (auth), FR-014 (admin — limited)
- **Related TC**: TBD — needs settings test
- **Related BR**: BR-004

#### SCR-026: Account Menu — Session & Workspace Actions
- **Route**: Global dropdown
- **Actor**: Any authenticated staff
- **Purpose**: Quick access to account actions, workspace switching, and session management
- **Screenshot**: [`users.account-menu.session-workspace-actions.png`](../screen-design/users.account-menu.session-workspace-actions.png)
- **Data required**: User name, role, current workspace, session info
- **Actions**: Switch workspace, view profile, logout
- **Related APIs**: `GET /api/v1/auth/me`, `POST /api/v1/auth/logout` (TBD)
- **Related UC**: TBD — implied by auth
- **Related FR**: FR-001
- **Related TC**: TC-001 (logout variant)
- **Related BR**: BR-004

---

### Workspaces Domain

#### SCR-027: Environment Selector (Synthetic/Sandbox/Training/Production)
- **Route**: `/workspaces` or global selector
- **Actor**: Admin, DevOps
- **Purpose**: Select between synthetic, sandbox, training, and production environments
- **Screenshot**: [`workspaces.environment-selector.synthetic-sandbox-training-production.png`](../screen-design/workspaces.environment-selector.synthetic-sandbox-training-production.png)
- **Data required**: Environment list with status, data mode indicator
- **Actions**: Switch environment, view environment status
- **Related APIs**: `GET /api/v1/workspaces` (TBD — new endpoint), `POST /api/v1/workspaces/switch` (TBD)
- **Related UC**: TBD — needs workspace UC
- **Related FR**: TBD — not in current FR list
- **Related TC**: TBD — needs environment test
- **Related BR**: BR-004 (data safety across environments)

---

## Coverage Summary

| Metric | Value |
|---|---|
| Total screens | 27 (25 with screenshots + 2 implied) |
| Screens with ≥1 API mapping | 25/27 (93%) |
| Screens with ≥1 UC mapping | 22/27 (81%) |
| Screens with ≥1 TC mapping | 18/27 (67%) |
| Screens needing new API endpoints | 4 (SCR-022, SCR-025, SCR-026, SCR-027) |
| Screens needing new UCs | 3 (SCR-025, SCR-026, SCR-027) |
| Screens needing new TCs | 7 (SCR-004, SCR-005, SCR-014, SCR-018, SCR-022, SCR-025, SCR-026) |

## New API Endpoints Identified

| Endpoint | Method | Purpose | Source Screen |
|---|---|---|---|
| `/api/v1/access-requests` | POST | Submit clinical justification for patient access | SCR-022 |
| `/api/v1/users/me` | PATCH | Update user profile and preferences | SCR-025 |
| `/api/v1/auth/logout` | POST | End session | SCR-026 |
| `/api/v1/workspaces` | GET | List available environments | SCR-027 |
| `/api/v1/workspaces/switch` | POST | Switch active environment | SCR-027 |
| `/api/v1/system/health` | GET | System health status | SCR-025 |

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 2.0 | 2026-06-07 | Agent | Initial creation from 25 renamed screen-design images |
