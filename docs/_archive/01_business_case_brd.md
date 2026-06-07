# Business Case & BRD

**Project:** AI-Powered Hospital Knowledge Assistant
**Project Code:** HOSP-AI-001
**Version:** 1.0
**Status:** Draft
**Last Updated:** 2026-04-27

**Owner:** Sponsor / Product Owner / Business Analyst

## 1. Executive Summary
Hospital staff spend significant time searching across structured records, PDFs, scanned documents, prescriptions, lab results, and historical notes. This project proposes a secure AI assistant that retrieves and summarizes information with citations.

## 2. Business Problem
- Patient information is fragmented across PostgreSQL tables and documents.
- Scanned documents are difficult to search.
- Manual lookup can take 10-15 minutes per patient.
- Answers are hard to verify without source links.
- There is no reliable metric system to prove time or cost savings.

## 3. Business Objectives and KPIs
| Goal ID | Goal | Baseline | Target | Owner |
|---|---|---:|---:|---|
| BG-001 | Reduce patient lookup time | 10-15 min | <30 sec | PO |
| BG-002 | Reduce manual document review | 5-10 docs/query | 1 cited AI query | Clinical SME |
| BG-003 | Improve traceability | Manual/no citations | >=95% cited answers | QA |
| BG-004 | Improve operational productivity | Unknown | >=80% effort reduction for target workflows | PM |
| BG-005 | Improve auditability | Partial | 100% sensitive queries logged | Security |

## 4. Scope
### In Scope
- AI chat over authorized hospital data
- Patient summary
- OCR ingestion for PDF/image documents
- Semantic search with citations
- PostgreSQL + pgvector retrieval
- RBAC + ABAC permission model
- Audit log and productivity metrics
- Optional drug/allergy pre-check in Phase 2

### Out of Scope
- Replacing clinical judgment
- Full PACS image diagnosis
- Medical device certification
- Public internet deployment in MVP
- Large multi-hospital production rollout in MVP

## 5. Stakeholders and RACI
| Stakeholder | Need | RACI |
|---|---|---|
| Sponsor | ROI, risk, timeline | A |
| Product Owner | Scope and priorities | A/R |
| Doctor | Fast cited patient summary | C |
| Nurse | Fast access to latest notes | C |
| Pharmacist | Medication/allergy warnings | C |
| Hospital IT | Secure integration | R/C |
| Security/Compliance | Access control and audit | A/C |
| QA Lead | Tests, RTM, UAT | R |

## 6. Business Requirements
| BR ID | Requirement | Priority | Acceptance / Measure |
|---|---|---|---|
| BR-001 | Authorized users can ask patient-related questions and receive cited answers. | Must | Answer includes source document/table/page/chunk. |
| BR-002 | System can generate patient summary. | Must | Summary includes history, meds, allergies, labs, citations. |
| BR-003 | System can OCR and index medical documents. | Must | Uploaded document becomes searchable. |
| BR-004 | System enforces permission-aware retrieval. | Must | Unauthorized context never reaches LLM. |
| BR-005 | System logs metrics for time saved and cost savings. | Must | Metrics dashboard shows before/after workflow data. |
| BR-006 | System supports Graph RAG relationships. | Should | Patient -> encounter -> diagnosis -> meds -> allergy traversal works. |
| BR-007 | System can flag potential drug/allergy conflicts. | Should | Warning includes source and rule explanation. |

## 7. Cost and Benefit
| Type | Item | Estimate / Note |
|---|---|---|
| Cost | MVP development | Backend, RAG, OCR, UI, QA, DevOps |
| Cost | Local development | 16GB RAM machine supported with quantized models |
| Cost | Production infra | Depends on LLM size and concurrency |
| Benefit | Lookup time saved | 10-15 min -> <30 sec |
| Benefit | Document review reduction | ~80% target |
| Benefit | Example cost saving | 100 lookups/day * 10 min saved * $20/hr = ~$333/day |

## 8. Risks and Decisions
| ID | Risk / Decision | Impact | Mitigation / Decision |
|---|---|---|---|
| R-001 | OCR may fail on poor scans | High | Use PaddleOCR first; VLM OCR fallback later |
| R-002 | 16GB RAM limits model size | Medium | Use 3B/7B quantized model for MVP |
| R-003 | PHI privacy risk | High | Local-first LLM, RBAC/ABAC, audit logs |
| R-004 | Hallucination risk | High | Require citations and safe refusal |
| D-001 | Use PostgreSQL + pgvector for MVP | High | Accepted |
| D-002 | Neo4j added in Phase 2 | Medium | Accepted |
| D-003 | UI uses Linear/Cal.com-inspired minimal style with medical semantic colors | Medium | Accepted |

## 9. CV Impact Target
```text
Built an AI-powered hospital knowledge assistant using FastAPI, PostgreSQL, pgvector, OCR, and Graph RAG to automate patient data retrieval.
Reduced patient information lookup time from ~10-15 minutes to under 30 seconds in simulated clinical workflows.
Decreased manual document review effort by ~80% through permission-aware semantic search with citations.
```
