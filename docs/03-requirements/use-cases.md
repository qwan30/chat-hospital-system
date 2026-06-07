# Use Case Index & Traceability Matrix

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 3.0  
> Owner: BA / Product Owner  
> Last updated: 2026-06-07  
> Status: Approved  

---

## 1. Use Case Inventory

| UC ID | Use Case descriptive Name | Primary Actor | Priority | Specification File Path |
|---|---|---|---|---|
| **UC-001** | Ask Patient Question | Doctor, Nurse | Must | [UC-001-Ask-Patient-Question.md](UC-001-Ask-Patient-Question.md) |
| **UC-002** | Generate Patient Summary | Doctor | Must | [UC-002-Generate-Patient-Summary.md](UC-002-Generate-Patient-Summary.md) |
| **UC-003** | Upload and OCR Document | Records Staff | Must | [UC-003-Upload-OCR-Document.md](UC-003-Upload-OCR-Document.md) |
| **UC-004** | Search Documents Semantically | Authorized Users | Must | [UC-004-Search-Documents-Semantically.md](UC-004-Search-Documents-Semantically.md) |
| **UC-005** | View Citations / Source Page | Authorized Users | Must | [UC-005-View-Citations-Source-Page.md](UC-005-View-Citations-Source-Page.md) |
| **UC-006** | Drug/Allergy Pre-Check | Doctor, Pharmacist | Should | [UC-006-Drug-Allergy-Pre-Check.md](UC-006-Drug-Allergy-Pre-Check.md) |
| **UC-007** | View Patient Timeline | Doctor, Nurse | Should | [UC-007-View-Patient-Timeline.md](UC-007-View-Patient-Timeline.md) |
| **UC-008** | Review Audit Logs | Security Auditor | Must | [UC-008-Review-Audit-Logs.md](UC-008-Review-Audit-Logs.md) |
| **UC-009** | View Impact Metrics | PM, PO | Must | [UC-009-View-Impact-Metrics.md](UC-009-View-Impact-Metrics.md) |

---

## 2. Requirements Traceability Matrix (RTM)

The matrix below traces use cases to EMR source business requirements, functional requirements, front-end views, and Backend-For-Frontend (BFF) endpoints:

| UC ID | Related BR | Related FR | Chatbot BFF Endpoints called | Screen ID | Test Cases |
|---|---|---|---|---|---|
| **UC-001** | BR-001, BR-004 | FR-004, FR-017, FR-018 | `POST /api/v1/chat`, `POST /api/v1/chat/stream`, `GET /api/v1/patients/search` | SCR-011, SCR-012, SCR-013 | TC-004, TC-005, TC-016 |
| **UC-002** | BR-002 | FR-008, FR-018 | `POST /api/v1/patients/{id}/ai-summary/generate`, `GET /api/v1/patients/{id}/overview` | SCR-007, SCR-010 | TC-008, TC-009 |
| **UC-003** | BR-003 | FR-006, FR-022 | `POST /api/v1/documents`, `POST /api/v1/documents/batch` | SCR-016, SCR-017 | TC-006, TC-007 |
| **UC-004** | BR-003 | FR-007, FR-021 | `POST /api/v1/documents/search`, `GET /api/v1/search/global` | SCR-015, SCR-020 | TC-007 |
| **UC-005** | BR-001 | FR-005 | `GET /api/v1/chat/queries/{queryId}/citations`, `GET /api/v1/documents/{id}/pages/{page}` | SCR-018, SCR-019 | TC-004 |
| **UC-006** | BR-007 | FR-012 | `POST /api/v1/patients/{id}/medication-review` | SCR-008 | TC-013 |
| **UC-007** | BR-002 | FR-013 | `GET /api/v1/patients/{id}/timeline` | SCR-007 | TC-014 |
| **UC-008** | BR-004, BR-005 | FR-010, FR-025 | `GET /api/v1/audit/events` | SCR-023 | TC-011 |
| **UC-009** | BR-005 | FR-009, FR-024 | `GET /api/v1/metrics/summary`, `GET /api/v1/dashboard/summary` | SCR-003, SCR-024 | TC-010 |

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 2.0 | 2026-06-07 | Agent | Restructured use case index and traceability mapping |
| 3.0 | 2026-06-07 | Agent | Updated use case mapping to target new BFF endpoints and screen IDs |
