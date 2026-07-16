# Software Requirements Specification (SRS)

> Project: HOSP-AI-001 — AI Hospital Knowledge Assistant  
> Version: 1.1 · Owner: Product Owner / Tech Lead · Last Updated: 2026-07-12  

## 1. Introduction
This SRS consolidates all functional and non-functional requirements. For details, see `functional-requirements.md`, `non-functional-requirements.md`, `use-cases.md`.

## 2. Functional Requirements (25)

| ID | Requirement | Priority | BR | UC | API |
|----|------------|----------|----|----|-----|
| FR-001 | HMS JWT auth bridge | Must | — | — | `GET /auth/me` |
| FR-002 | Patient-scoped ABAC + RBAC access | Must | BR-004 | UC-001-002 | All patient endpoints |
| FR-003 | Permission-filtered patient search | Must | BR-004 | UC-004 | `GET /patients` |
| FR-004 | AI chat with cited RAG answers | Must | BR-001 | UC-001 | `POST /chat` |
| FR-005 | SSE streaming chat | Should | BR-001 | UC-001 | `POST /chat/stream` |
| FR-006 | Document upload + OCR pipeline | Must | BR-003 | UC-003 | `POST /documents/upload` |
| FR-007 | Semantic search (vector+BM25+hybrid) | Must | BR-003 | UC-004 | `GET /search/global` |
| FR-008 | AI patient summary | Must | BR-002 | UC-002 | `GET /patients/{id}/summary` |
| FR-009 | Impact metrics tracking | Must | BR-005 | UC-009 | `GET /feedback/metrics/summary` |
| FR-010 | Immutable audit log | Must | BR-005 | UC-008 | `GET /audit/logs` |
| FR-011 | Graph RAG entity retrieval | Should | BR-006 | UC-001 | (internal) |
| FR-012 | Drug-allergy interaction check | Should | BR-007 | UC-006 | `GET /patients/{id}/meds` |
| FR-013 | Patient timeline view | Should | — | UC-007 | timeline endpoint |
| FR-014 | System settings (14 keys) | Should | — | — | `GET/PUT /settings` |
| FR-015 | User feedback (thumbs up/down) | Could | BR-005 | UC-009 | `POST /feedback` |
| FR-016 | Dashboard (populated + empty) | Must | — | — | `GET /dashboard/summary` |
| FR-017 | HMS data sync integration | Should | — | — | `POST /hms/sync/patients/{id}` |
| FR-018 | Patient overview (EMR + AI) | Must | — | — | `GET /patients/{id}/overview` |
| FR-019 | Break-glass access request | Must | BR-004 | — | `POST /access-requests` |
| FR-020 | Workspace switcher | Could | — | — | (frontend only) |
| FR-021 | Global search (Ctrl+K) | Should | — | — | `GET /search/global?q=` |
| FR-022 | OCR retry flow | Should | BR-003 | UC-003 | `POST /documents/{id}/retry-ocr` |
| FR-023 | RAG trace observability | Should | — | — | `GET /chat/queries/{id}/trace` |
| FR-024 | Chat thread CRUD + participants | Should | — | — | `/chat-threads` CRUD |
| FR-025 | Autonomous CDSS clinical alert generation | Must | BR-CDSS-001 | — | (internal worker) |

## 3. Non-Functional Requirements (22)

| ID | Category | Requirement | Target |
|----|----------|-------------|--------|
| NFR-001 | Performance | API P50 latency | <200 ms |
| NFR-002 | Performance | API P95 latency | <1000 ms |
| NFR-003 | Performance | Chat end-to-end | <30 sec |
| NFR-004 | Performance | Concurrent users | ~50 |
| NFR-005 | Performance | OCR per page | <60 sec |
| NFR-006 | Availability | Uptime | 99.5% |
| NFR-007 | Availability | RTO | <4 hours |
| NFR-008 | Availability | RPO | <1 hour |
| NFR-009 | Security | HTTPS all endpoints | Required |
| NFR-010 | Security | HMS JWT bridge | Required |
| NFR-011 | Security | Rate limiting | 10/min chat, 20/min search |
| NFR-012 | Security | Local-first PHI | Required |
| NFR-013 | Security | CI dependency scanning | Required |
| NFR-014 | Observability | Structured logging + trace_id | Required |
| NFR-015 | Observability | Health check | `GET /api/v1/health` |
| NFR-016 | Observability | Metrics endpoint | `GET /feedback/metrics/summary` |
| NFR-017 | Compliance | 100% audit on sensitive queries | Required |
| NFR-018 | Compliance | HIPAA data handling | Required |
| NFR-019 | Quality | Code coverage | ≥80% line |
| NFR-020 | Quality | Citation accuracy | ≥95% |
| NFR-021 | Scalability | Horizontal BFF scaling | Supported |
| NFR-022 | Scalability | Multiple RQ workers | Supported |

## 4. Traceability Matrix

| FR | BR | UC | API | Test |
|----|----|----|-----|------|
| FR-001 | — | — | `GET /auth/me` | TC-001 |
| FR-002 | BR-004 | UC-001,002 | All patient | TC-002 |
| FR-003 | BR-004 | UC-004 | `GET /patients` | TC-003 |
| FR-004 | BR-001 | UC-001 | `POST /chat` | TC-004 |
| FR-006 | BR-003 | UC-003 | `POST /documents/upload` | TC-006 |
| FR-007 | BR-003 | UC-004 | `GET /search/global` | TC-007 |
| FR-008 | BR-002 | UC-002 | `GET /patients/{id}/summary` | TC-008,009 |
| FR-009 | BR-005 | UC-009 | `GET /feedback/metrics/summary` | TC-010 |
| FR-010 | BR-005 | UC-008 | `GET /audit/logs` | TC-011 |
| FR-011 | BR-006 | UC-001 | (internal) | TC-012 |
| FR-017 | — | — | `POST /hms/sync` | TC-020,022 |
| FR-018 | — | — | `GET /patients/{id}/overview` | TC-020 |
| FR-019 | BR-004 | — | `POST /access-requests` | TC-023 |
| FR-021 | — | — | `GET /search/global` | TC-025 |
| FR-022 | BR-003 | UC-003 | `POST /documents/{id}/retry-ocr` | TC-024 |
| FR-025 | BR-CDSS-001 | — | (internal CDSS worker) | cdss-flow.spec.ts |

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Consolidated 24 FRs + 22 NFRs with traceability matrix |
| 1.1 | 2026-07-12 | Agent | Added FR-025 Autonomous CDSS Agent; updated FR count to 25; added traceability row |
