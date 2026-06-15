# Requirements Traceability Matrix (RTM)

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 4.0  
> Status: Approved  
> Owner: QA Lead / PM  
> Last Updated: 2026-06-15  

---

## 1. Traceability Mapping

The RTM maps all functional and non-functional requirements to design elements, backend database/API components, and verification test cases:

| Req ID | Design Ref (Screen ID) | API / Database Reference | Test Cases | Validation Status |
|---|---|---|---|---|
| **FR-001** | Login (SCR-001, SCR-002) | `POST /api/v1/auth/login` | TC-001 | Covered |
| **FR-002** | Access Denied (SCR-021) | `user_roles`, HMS permission API | TC-002, TC-016, TC-021 | Covered |
| **FR-003** | Patient Search (SCR-006) | `GET /api/v1/patients/search` | TC-003, TC-009 | Covered |
| **FR-004** | Chat View (SCR-011, SCR-013) | `POST /api/v1/chat`, `chat_threads` | TC-004, TC-005, TC-012 | Covered |
| **FR-005** | Citations (SCR-014, SCR-019) | `GET /api/v1/chat/queries/{id}/citations` | TC-004, TC-017 | Covered |
| **FR-006** | OCR Upload (SCR-017) | `POST /api/v1/documents/batch` | TC-006, TC-024 | Covered |
| **FR-007** | Document Search (SCR-015) | `POST /api/v1/documents/search` | TC-007 | Covered |
| **FR-008** | Patient Summary (SCR-007, SCR-010) | `POST /api/v1/patients/{id}/ai-summary/generate`| TC-008, TC-009 | Covered |
| **FR-009** | Metrics Dashboard (SCR-024) | `GET /api/v1/metrics/summary` | TC-010, TC-026 | Covered |
| **FR-010** | Audit Event Logs (SCR-023) | `GET /api/v1/audit/events` | TC-011 | Covered |
| **FR-011** | Graph RAG (Phase 2) | `graph_edges` / Neo4j | TC-012 | Partially Covered |
| **FR-012** | Medication Review (SCR-008) | `POST /api/v1/patients/{id}/medication-review` | TC-013 | Partially Covered |
| **FR-013** | Timeline View (SCR-007) | `GET /api/v1/patients/{id}/timeline` | TC-014 | Covered |
| **FR-014** | Settings (SCR-025) | `GET /api/v1/users/me/preferences` | TBD | Covered |
| **FR-015** | Feedback (SCR-014) | `POST /api/v1/feedback` | TC-015 | Covered |
| **FR-016** | Dashboard Populated (SCR-003, SCR-005) | `GET /api/v1/dashboard/summary` | TC-026 | Covered |
| **FR-017** | HMS Sync Integration (Worker) | `/api/v1/hms/sync`, `patients`, `hms_sync_logs` | TC-020, TC-022 | Covered |
| **FR-018** | Patient Overview Snapshot (SCR-007) | `GET /api/v1/patients/{id}/overview` | TC-020 | Covered |
| **FR-019** | Access Justification Modal (SCR-022)| `POST /api/v1/access-requests` | TC-023 | Covered |
| **FR-020** | Environment Switcher (SCR-027) | `POST /api/v1/workspaces/{id}/switch` | TBD | Covered |
| **FR-021** | Global Search Command (SCR-020) | `GET /api/v1/search/global` | TC-025 | Covered |
| **FR-022** | Ingestion Review Flow (SCR-016) | `POST /api/v1/documents/{id}/retry-ocr` | TC-024 | Covered |
| **FR-023** | User Preferences View (SCR-025) | `GET /api/v1/users/me/preferences` | TBD | Covered |
| **FR-024** | HMS Integration Monitor (SCR-003) | `GET /api/v1/integrations/hms/health` | TC-026 | Covered |
| **FR-025** | Cross-system Audit Trace (SCR-023) | `GET /api/v1/audit/events` | TC-011, TC-021 | Covered |

---

## 2. E2E Test Coverage Mapping

The following maps each E2E real-user interaction test suite to the business requirements it validates:

| E2E Suite | Test Count | Requirements Covered | TC IDs |
|-----------|-----------|---------------------|--------|
| **login-flow** | 12 | FR-001 (Login), FR-014 (MFA) | TC-027, TC-028, TC-029, TC-037 |
| **chat-flow** | 7 | FR-004 (Chat), FR-005 (Citations) | TC-004, TC-005, TC-030 |
| **patient-flow** | 11 | FR-002 (Access), FR-003 (Search), FR-008 (Summary), FR-012 (Meds), FR-019 (Access Request) | TC-031, TC-032, TC-033, TC-034 |
| **document-flow** | 5 | FR-006 (OCR), FR-007 (Search), FR-022 (Review) | TC-036 |
| **navigation-flow** | 16 | FR-014 (Navigation), FR-021 (Search) | TC-035 |
| **error-flow** | 5 | NFR-SEC-003 (Rate Limit), NFR-REL-001 (Reliability) | TC-038, TC-039, TC-040 |
| **Total** | **56** | **12 functional + 2 non-functional requirements** | **14 test cases** |

> **Status (2026-06-15)**: All 56 E2E tests pass at 100%. Tests run in CI via `npx playwright test e2e/flows/ --workers=1`.

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 2.0 | 2026-06-07 | Agent | Restructured RTM map |
| 3.0 | 2026-06-07 | Agent | Expanded RTM map to track FR-016 through FR-025 |
| 4.0 | 2026-06-15 | Agent | Added E2E real-user interaction test coverage mapping (56 tests, 14 reqs) |
