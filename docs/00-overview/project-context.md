# Project Context

> Project: AI-Powered Hospital Knowledge Assistant  
> Project Code: HOSP-AI-001  
> Version: 2.0  
> Owner: Sponsor / Product Owner  
> Last updated: 2026-06-07  
> Status: In Review

## 1. Executive Summary

Hospital staff spend significant time searching across structured records, PDFs, scanned documents, prescriptions, lab results, and historical notes. This project builds a secure AI assistant that retrieves and summarizes information with citations, integrated with the existing Hospital Management System (HMS).

## 2. Business Problem

- Patient information is fragmented across PostgreSQL tables and documents.
- Scanned documents are difficult to search.
- Manual lookup can take 10–15 minutes per patient.
- Answers are hard to verify without source links.
- There is no reliable metric system to prove time or cost savings.

## 3. Product Vision

An AI-powered copilot for hospital staff that:
- **Retrieves** patient data from HMS with permission-aware filtering
- **Summarizes** patient history with citations to source documents
- **Indexes** scanned medical documents via OCR for semantic search
- **Refuses safely** when evidence is insufficient
- **Measures** time and cost savings for operational ROI proof

## 4. System Boundaries

| System | Role | Ownership |
|---|---|---|
| **HMS (Hospital Management System)** | Source of truth for clinical data (patients, encounters, diagnoses, medications, allergies, labs, appointments) | Separate Java/Spring Boot project |
| **Chatbot (this project)** | AI/RAG/BFF layer — OCR, embedding, retrieval, summary, citations, metrics, audit | Python/FastAPI + Next.js |
| **Frontend** | UI for staff interaction — chat, patient overview, documents, metrics | Next.js (inside this project) |

## 5. Integration Model

```
HMS owns clinical data → Chatbot reads via HMS REST API
Chatbot owns AI/RAG data → Frontend reads via Chatbot BFF API
Frontend never calls HMS directly
```

## 6. Key Stakeholders

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

## 7. Timeline

| Milestone | Status |
|---|---|
| Sprint 0 — Docs, repo, local stack | ✅ Complete |
| MVP Build — Auth, upload, OCR, search, chat, summary | 🔄 In Progress |
| System Test — E2E, access, OCR, RAG tests | ⬜ Planned |
| UAT — SME validation | ⬜ Planned |
| Demo Release — Metrics report and portfolio demo | ⬜ Planned |

## 8. Related Documents

- [Project Foundation](project-foundation.md) — Technical source of truth
- [Documentation Index](documentation-index.md) — Reading paths
- [BRD](../01-business/brd.md) — Business requirements
- [PRD](../02-product/prd.md) — Product requirements
- [Architecture](../04-architecture/architecture.md) — System design

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 2.0 | 2026-06-07 | Agent | Created from BRD sections 1–2 and project context |
