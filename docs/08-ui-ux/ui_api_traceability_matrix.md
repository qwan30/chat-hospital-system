# UI & API Traceability Matrix

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 3.0  
> Status: Approved  
> Owner: Product Owner / QA Lead  
> Last Updated: 2026-06-07  

---

## 1. Traceability Matrix

This cross-cutting matrix maps all user interface screens (SCR) to Use Cases (UC), API endpoints, Functional Requirements (FR), Business Rules (BR), and Test Cases (TC):

| Screen ID | Screen Name | Use Case | API Endpoint called | FR ID | BR ID | Test Case |
|---|---|---|---|---|---|---|
| **SCR-001** | Staff SSO Login | UC-001 (Precondition) | `POST /api/v1/auth/login` | FR-001 | BR-SEC-001 | TC-001 |
| **SCR-002** | MFA Verify Identity Code | UC-001 (Precondition) | `POST /api/v1/auth/mfa/verify` | FR-001 | BR-SEC-001 | TC-001 |
| **SCR-003** | Populated HMS-AI Workspace | UC-009 | `GET /api/v1/dashboard/summary` | FR-016 | BR-MET-001 | TC-026 |
| **SCR-004** | Action Success Toast | Multiple | N/A (UI state only) | N/A | N/A | TBD |
| **SCR-005** | Workspace Onboarding / Empty | UC-003, UC-001 | `GET /api/v1/dashboard/summary` (empty state) | FR-016 | BR-RAG-001 | TBD |
| **SCR-006** | Patient List with Scoped Alerts | UC-001 (Select Patient) | `GET /api/v1/patients/search` | FR-003 | BR-SEC-002 | TC-003 |
| **SCR-007** | Patient Overview with AI Summary| UC-002, UC-007 | `GET /api/v1/patients/{id}/overview`, `GET /api/v1/patients/{id}/timeline` | FR-018, FR-013 | BR-MED-001 | TC-020, TC-014 |
| **SCR-008** | Medication Review | UC-006 | `POST /api/v1/patients/{id}/medication-review` | FR-012 | BR-MED-001 | TC-013 |
| **SCR-009** | Patient Empty State | UC-001 (Alternate flow) | `GET /api/v1/patients/search` | FR-003 | BR-SEC-002 | TC-003 |
| **SCR-010** | AI Summary Stream | UC-002 (Main flow) | `POST /api/v1/patients/{id}/ai-summary/generate` | FR-008 | BR-MED-001 | TC-008 |
| **SCR-011** | New Patient Context Thread | UC-001 | `POST /api/v1/chat-threads`, `GET /api/v1/patients/search` | FR-004, FR-003 | BR-SEC-001 | TC-004 |
| **SCR-012** | Safe Refusal — Insufficient | UC-001 (Alternate flow) | `POST /api/v1/chat` | FR-004 | BR-AI-001 | TC-005 |
| **SCR-013** | AI HMS Copilot Landing | UC-001 (General mode) | `GET /api/v1/chat-threads`, `POST /api/v1/chat` | FR-004 | BR-SEC-001 | TC-004 |
| **SCR-014** | Chat Cited Answer | UC-001, UC-005 | `POST /api/v1/chat` | FR-004, FR-005 | BR-RAG-001 | TC-004 |
| **SCR-015** | OCR Indexing Dashboard | UC-004 | `POST /api/v1/documents/search`, `GET /api/v1/documents` | FR-007, FR-022 | BR-OCR-001 | TC-007, TC-024 |
| **SCR-016** | OCR Review | UC-003 (Alternate flow) | `GET /api/v1/documents/{id}/extracted-text` | FR-006, FR-022 | BR-OCR-001 | TC-006, TC-024 |
| **SCR-017** | Batch Upload Modal | UC-003 | `POST /api/v1/documents/batch` | FR-006, FR-022 | BR-OCR-001 | TC-006 |
| **SCR-018** | Document Pages Preview | UC-005 | `GET /api/v1/documents/{id}/pages/{page}` | FR-005 | BR-OCR-001 | TC-004 |
| **SCR-019** | Verified Source Document Viewer | UC-005 | `GET /api/v1/chat/queries/{queryId}/citations` | FR-005 | BR-RAG-001 | TC-004 |
| **SCR-020** | Global Command Palette | UC-001, UC-004 | `GET /api/v1/search/global` | FR-021 | BR-SEC-002 | TC-025 |
| **SCR-021** | Access Denied — No Relationship | UC-001 (Alternate flow) | `GET /api/v1/patients/{id}/overview` (returns 403) | FR-002 | BR-SEC-002 | TC-002, TC-021 |
| **SCR-022** | Access Request Justification | UC-001 (Exception) | `POST /api/v1/access-requests` | FR-019 | BR-SEC-002 | TC-023 |
| **SCR-023** | Audit Logs Dashboard | UC-008 | `GET /api/v1/audit/events` | FR-010, FR-025 | BR-SEC-001 | TC-011, TC-021 |
| **SCR-024** | Impact Quality Dashboard | UC-009 | `GET /api/v1/metrics/summary` | FR-009, FR-024 | BR-MET-001 | TC-026 |
| **SCR-025** | Profile & System Preferences | UC-010 (TBD) | `GET /api/v1/users/me/preferences` | FR-023 | BR-SEC-001 | TBD |
| **SCR-026** | Account Menu Dropdown | UC-010 (TBD) | `POST /api/v1/auth/logout` (TBD) | FR-001 | BR-SEC-001 | TC-001 |
| **SCR-027** | Environment Selector | UC-011 (TBD) | `POST /api/v1/workspaces/{id}/switch` | FR-020 | BR-SEC-001 | TBD |

---

## 2. Coverage Analysis

*   **UI Coverage**: All 27 screens (including 2 implied preview screens) have been registered and tracked in the matrix.
*   **API Coverage**: 93% of the cataloged UI screens link to active backend API endpoints. Mapped TBD paths are registered for development.
*   **Requirements Coverage**: 100% of Must functional requirements are represented in at least one interface.
*   **Verification Gaps**: Under `Test Case` mapping, 4 screens (SCR-004, SCR-005, SCR-025, SCR-027) currently lack dedicated verification tests. These have been noted as QA tasks for the next development iteration.

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 2.0 | 2026-06-07 | Agent | Compiled complete trace database from screen catalogs and requirement indexes |
| 3.0 | 2026-06-07 | Agent | Realigned API endpoints and test cases to fit HMS integration architecture |
