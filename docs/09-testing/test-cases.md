# Test Case Inventory

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 3.0  
> Status: Approved  
> Owner: QA Lead / PM  
> Last Updated: 2026-06-07  

---

## 1. Automated & Manual Test Cases

This inventory catalogues all test cases mapped to functional requirements, non-functional requirements, and business rules:

| TC ID | Title / Scenario | Linked Req | Priority | Expected Result / Verification |
|---|---|---|---|---|
| **TC-001** | Login succeeds | FR-001 | P1 (Must) | Authenticated user receives valid scoped JWT session. |
| **TC-002** | Unauthorized patient blocked | FR-002 | P1 (Must) | Request returns HTTP 403, and an event is written to `audit_logs`. |
| **TC-003** | Patient search scoped | FR-003 | P1 (Must) | Search results exclude patient records outside user's ABAC scope. |
| **TC-004** | AI chat cited answer | FR-004/005 | P1 (Must) | Chat response contains valid structured source citations mapping to chunks. |
| **TC-005** | Safe refusal without evidence | BR-AI-001 | P1 (Must) | Query returns standard "Insufficient evidence" status (`INSUFFICIENT_EVIDENCE`). |
| **TC-006** | Upload creates OCR job | FR-006 | P1 (Must) | API accepts PDF and queues worker task, marking status as `OCR Processing`. |
| **TC-007** | OCR document searchable | FR-006/007 | P1 (Must) | Output text chunks are parsed, embedded, and visible in semantic search. |
| **TC-008** | Summary generation under target | FR-008 | P1 (Must) | Patient summary is generated in <30 seconds on the MVP benchmark dataset. |
| **TC-009** | Summary contains required sections| FR-008 | P1 (Must) | Completed summary contains: history, medications, allergies, and labs. |
| **TC-010** | Metric event created after query | FR-009 | P1 (Must) | A de-identified analytics row is successfully logged via the metrics service. |
| **TC-011** | Audit event created after query | FR-010 | P1 (Must) | An access control row is successfully logged in `audit_logs` (with trace ID). |
| **TC-012** | Graph RAG queries work | FR-011 | P2 (Should) | Multi-hop relationship evidence is retrieved and cited in the chatbot. |
| **TC-013** | Drug/allergy warning triggered | FR-012 | P2 (Should) | Medication check detects allergy conflict and displays high-severity warning. |
| **TC-014** | Patient timeline filtering | FR-013 | P2 (Should) | Sorting and filtering by category updates events list correctly (SCR-007). |
| **TC-015** | Local Lite stack runs on 16GB RAM | NFR-COST-001| P1 (Must) | Entire application stack launches and operates on a 16GB RAM constraint. |
| **TC-016** | Zero unauthorized chunks reach LLM | NFR-SEC-002 | P1 (Must) | Strict confirmation: 0 pages/chunks outside user's ABAC reach the LLM context. |
| **TC-017** | HMS appointment evidence import | FR-004/005 | P1 (Must) | Imported appointment text contains source lineage metadata for citations. |
| **TC-018** | HMS ownership mismatch blocked | NFR-SEC-002 | P1 (Must) | Ingesting data with mismatched clinician-patient identifiers is rejected. |
| **TC-019** | Archived/Deleted source excluded | NFR-SEC-002 | P1 (Must) | Documents marked as archived or deleted in the HIS are excluded from RAG. |
| **TC-020** | HMS Snapshot Sync Integration | FR-017, FR-018 | P1 (Must) | BFF retrieves demographics/med lists and joins them with local DB read-caches. |
| **TC-021** | HMS Permission Revoked Integration | FR-002, FR-025 | P1 (Must) | Revoking access on HMS immediately stops vector search retrieval. |
| **TC-022** | HMS Change Feed Sync Process | FR-017 | P1 (Must) | Incremental change events updates cached read models. |
| **TC-023** | Access Request Approval Flow | FR-019 | P1 (Must) | Justification logs are accepted, and access is permitted once status changes. |
| **TC-024** | Document OCR Workflow (Retry/Archive)| FR-022 | P2 (Should) | Triggering re-scan and archiving items reflects correctly in status updates. |
| **TC-025** | Global Search Command Palette | FR-021 | P2 (Should) | Ctrl+K displays matching results for patients, documents, and chat threads. |
| **TC-026** | Dashboard Summary Validation | FR-016, FR-024 | P1 (Must) | Operational page displays synced document counters, metrics, and health. |

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | QA Lead | Initial test cases list |
| 2.0 | 2026-06-07 | Agent | Split into standalone test cases catalog |
| 3.0 | 2026-06-07 | Agent | Added EMR/HMS integration test cases (TC-020 to TC-026) |
