# PRD / SRS Requirements Specification

**Project:** AI-Powered Hospital Knowledge Assistant
**Project Code:** HOSP-AI-001
**Version:** 1.0
**Status:** Draft
**Last Updated:** 2026-04-27

**Owner:** Product Owner / Business Analyst

## 1. Product Overview
The product is a secure, local-first AI assistant for hospital knowledge retrieval. It uses OCR, semantic search, PostgreSQL, pgvector, and Graph RAG to answer questions over patient data and documents with citations.

## 2. Personas
| Persona | Need | Pain Point | Success Signal |
|---|---|---|---|
| Doctor | Fast patient summary | Manual review takes 10-15 min | Summary in <30 sec |
| Nurse | Latest notes/instructions | Data scattered | One query finds result |
| Pharmacist | Med/allergy check | Manual verification | Warning + source |
| Records staff | Searchable scanned docs | Scans not searchable | OCR indexed |
| Admin/IT | Safe access control | Overexposure risk | RBAC/ABAC verified |
| PM/PO | Impact proof | No measurement | Metrics dashboard |

## 3. Functional Requirements
| FR ID | Module | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|---|
| FR-001 | Auth | Authenticate users via local login or OIDC. | Must | User receives scoped session. |
| FR-002 | Authorization | Enforce RBAC/ABAC before retrieval. | Must | Unauthorized users receive 403. |
| FR-003 | Patient Search | Search patients within scope. | Must | Results exclude unauthorized patients. |
| FR-004 | AI Chat | Ask natural language questions. | Must | Answer or safe refusal returned. |
| FR-005 | Citations | Show source document/table/page/chunk. | Must | Cited answers for evidence-backed claims. |
| FR-006 | OCR | Upload PDF/image and OCR it. | Must | Document moves to indexed/failed state. |
| FR-007 | Document Search | Semantic search over chunks. | Must | Relevant chunks returned with metadata. |
| FR-008 | Patient Summary | Generate cited patient summary. | Must | Includes history, meds, allergies, labs. |
| FR-009 | Metrics | Track latency, docs retrieved, time saved. | Must | Metrics dashboard shows before/after. |
| FR-010 | Audit | Log sensitive access. | Must | Every patient query creates audit event. |
| FR-011 | Graph RAG | Use patient relationship graph. | Should | Relationship-based queries work. |
| FR-012 | Drug Check | Flag potential med/allergy conflicts. | Should | Warning includes evidence. |
| FR-013 | Timeline | Show patient timeline. | Should | Filter by date/entity type. |
| FR-014 | Admin | Manage roles and departments. | Should | Role changes affect access. |
| FR-015 | Feedback | User can rate/report answer. | Should | Feedback linked to query ID. |

## 4. Non-Functional Requirements
| NFR ID | Category | Requirement | Target | Verification |
|---|---|---|---|---|
| NFR-PERF-001 | Performance | Patient summary latency | <30 sec MVP | Perf test |
| NFR-PERF-002 | Performance | Document search latency | P95 <5 sec | Load test |
| NFR-SEC-001 | Security | All APIs authenticated | 100% endpoints | Security test |
| NFR-SEC-002 | Security | No unauthorized context to LLM | 0 leaks | Access test |
| NFR-PRI-001 | Privacy | No external LLM for PHI by default | Local mode | Architecture review |
| NFR-AUD-001 | Audit | Sensitive access logged | 100% | Audit sample |
| NFR-OBS-001 | Observability | Logs, metrics, traces | Trace ID across flow | Ops review |
| NFR-REL-001 | Reliability | OCR/index jobs retryable | Retry succeeds | Integration test |
| NFR-COST-001 | Cost | MVP runs on 16GB RAM | Local Lite works | Dev test |

## 5. Business Rules
| Rule ID | Rule |
|---|---|
| BR-SEC-001 | User must be authenticated before accessing patient data. |
| BR-SEC-002 | Retrieval must apply RBAC/ABAC before LLM context creation. |
| BR-RAG-001 | Evidence metadata must be preserved through retrieval and generation. |
| BR-AI-001 | If evidence is insufficient, AI must say so. |
| BR-MED-001 | AI output is assistive and must not replace clinician judgment. |
| BR-AUD-001 | All patient-related queries create audit events. |
| BR-MET-001 | AI workflows create metric events. |
| BR-OCR-001 | OCR text must link to original document/page. |

## 6. Data Requirements
| Object | Key Fields | Source | Privacy |
|---|---|---|---|
| Patient | id, MRN, name, DOB | PostgreSQL HIS/EMR | PHI |
| Encounter | id, patient_id, date, department | PostgreSQL | PHI |
| Diagnosis | code, name, date | PostgreSQL | PHI |
| Medication | drug, dose, route, dates | PostgreSQL | PHI |
| Allergy | allergen, reaction, severity | PostgreSQL | PHI |
| Lab Result | test, value, unit, range, timestamp | LIS/PostgreSQL | PHI |
| Document | id, type, file_uri, status | Upload/storage | PHI |
| Chunk | text, embedding, metadata | OCR/parser | PHI |
| Audit Event | actor, action, object, trace_id | System | Sensitive |
| Metric Event | task, latency, time_saved | System | De-identified when possible |

## 7. Open Questions
| ID | Question | Impact | Owner | Status |
|---|---|---|---|---|
| Q-001 | What is the real PostgreSQL schema? | High | Backend | Open |
| Q-002 | Which roles are required for MVP? | High | PO/Security | Open |
| Q-003 | Which languages are in documents? | Medium | SME | Open |
| Q-004 | Is GPU available for production? | Medium | DevOps | Open |
| Q-005 | What compliance rules apply? | High | Security | Open |

## 8. MVP Acceptance
MVP is accepted when login, document upload/OCR, semantic search, patient summary, citations, permission checks, audit logs, and metric tracking all work with synthetic data.
