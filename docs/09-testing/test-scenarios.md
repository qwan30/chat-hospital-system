# Test Scenarios

> Project: HOSP-AI-001 · Version: 1.0 · Owner: QA Lead · Last Updated: 2026-06-14  

## TS-001: Authentication & Authorization

| ID | Scenario | Priority | Type |
|----|----------|----------|------|
| TS-001-01 | Valid HMS JWT returns user identity | P1 | Integration |
| TS-001-02 | Expired JWT returns HTTP 401 | P1 | Integration |
| TS-001-03 | Missing Authorization header returns HTTP 401 | P1 | Integration |
| TS-001-04 | User with no patient permissions sees empty list | P1 | Integration |
| TS-001-05 | Expired permission scope gets HTTP 403 | P1 | Integration |
| TS-001-06 | Admin accesses audit logs | P1 | Integration |
| TS-001-07 | Non-security user blocked from audit logs | P1 | Integration |

## TS-002: Chat RAG Pipeline

| ID | Scenario | Priority | Type |
|----|----------|----------|------|
| TS-002-01 | Valid patient context returns cited answer | P1 | Integration |
| TS-002-02 | No patient permission returns HTTP 403 | P1 | Integration |
| TS-002-03 | No evidence returns safe refusal | P1 | Integration |
| TS-002-04 | Answer contains valid citation labels (E1, E2...) | P1 | Unit |
| TS-002-05 | Citation IDs match retrieved evidence IDs | P1 | Unit |
| TS-002-06 | Streaming chat delivers SSE tokens | P2 | Integration |
| TS-002-07 | Rate limiting enforces 10/min | P2 | Integration |
| TS-002-08 | Thread includes conversation history | P2 | Integration |
| TS-002-09 | Auto-pipeline selects patient_summary for summary Qs | P2 | Unit |
| TS-002-10 | Auto-pipeline selects decompose_qa for complex Qs | P2 | Unit |
| TS-002-11 | Drug-allergy warning on conflicting drugs | P2 | Integration |
| TS-002-12 | Graph RAG enriches evidence with entities | P3 | Integration |

## TS-003: Document Processing

| ID | Scenario | Priority | Type |
|----|----------|----------|------|
| TS-003-01 | Upload PDF → status=uploaded | P1 | Integration |
| TS-003-02 | Upload enqueues OCR via RQ | P1 | Integration |
| TS-003-03 | OCR creates document_pages rows | P1 | Integration |
| TS-003-04 | Chunking creates document_chunks with embeddings | P1 | Integration |
| TS-003-05 | Full lifecycle: uploaded→ocr→indexed | P1 | E2E |
| TS-003-06 | Failed OCR → status=ocr_failed + ocr_error | P1 | Integration |
| TS-003-07 | OCR retry re-enqueues job | P2 | Integration |
| TS-003-08 | No upload permission → HTTP 403 | P1 | Integration |
| TS-003-09 | Exceeds max size → HTTP 400 | P2 | Integration |
| TS-003-10 | Semantic search finds indexed content | P2 | Integration |

## TS-004: Patient Management

| ID | Scenario | Priority | Type |
|----|----------|----------|------|
| TS-004-01 | Patient list filtered by user permissions | P1 | Integration |
| TS-004-02 | Overview returns EMR snapshot + AI summary | P1 | Integration |
| TS-004-03 | Patient summary <30 seconds | P1 | Integration |
| TS-004-04 | Medication review lists all active meds | P2 | Integration |
| TS-004-05 | Drug check returns interaction warnings | P2 | Integration |

## TS-005: Audit & Compliance

| ID | Scenario | Priority | Type |
|----|----------|----------|------|
| TS-005-01 | Every chat query creates audit_logs entry | P1 | Integration |
| TS-005-02 | Denied access logs outcome=denied | P1 | Integration |
| TS-005-03 | Audit log contains trace_id | P1 | Integration |
| TS-005-04 | Filterable by patient_id, action, outcome | P2 | Integration |
| TS-005-05 | Non-security user blocked from audit endpoint | P1 | Integration |

## TS-006: Chat Threads

| ID | Scenario | Priority | Type |
|----|----------|----------|------|
| TS-006-01 | Patient-linked thread requires patient_id | P2 | Integration |
| TS-006-02 | General thread must not have patient_id | P2 | Integration |
| TS-006-03 | Participant added with correct access_level | P2 | Integration |

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | 42 test scenarios across 6 functional areas |
