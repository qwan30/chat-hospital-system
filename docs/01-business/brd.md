# Business Requirements Document (BRD)

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 3.0  
> Owner: Sponsor / Product Owner / Business Analyst  
> Last updated: 2026-06-07  
> Status: Approved  

---

## 1. Business Objectives and KPIs

The AI Copilot acts as an intelligence extension for the Hospital Management System, improving lookup speeds and ensuring secure context-gated clinical support.

| Goal ID | Business Goal | Baseline | Target | Owner |
|---|---|---:|---:|---|
| **BG-001** | Reduce patient information lookup time | 10–15 min | <30 sec | Product Owner |
| **BG-002** | Reduce manual EMR and document review | 5–10 docs/query | 1 cited AI query response | Clinical SME |
| **BG-003** | Enforce source-lineage citation correctness | Manual lookup | ≥95% cited answers | QA Lead |
| **BG-004** | Improve overall staff operational productivity | Manual workflows | ≥80% effort reduction | Project Manager |
| **BG-005** | Ensure HIPAA/compliance trace audits | Partial logging | 100% of sensitive queries logged | Security Lead |
| **BG-006** | Maintain fresh HMS read-model caches | Batch transfers | Cache sync latency < 15 mins | DevOps / IT |

---

## 2. Product Scope

### In Scope (HMS Copilot MVP)
*   **Operational Dashboard**: populated and empty dashboard states (`SCR-003`, `SCR-005`) aggregating chatbot productivity metrics and patient statistics.
*   **Context-Gated AI Chat**: Streaming chat (`SCR-010`, `SCR-014`) using local quantized models (Qwen2.5 3B/7B via Ollama).
*   **Patient Overview Summarization**: AI summaries citing structured HMS snapshots (`SCR-007`) and unstructured docs.
*   **Document OCR & Indexing**: Ingestion queues (`SCR-017`) and low-confidence OCR review workflows (`SCR-016`).
*   **Access Control Gate**: ABAC-based patient scope checks (`SCR-021`) and clinical justification access requests (`SCR-022`).
*   **Global Command Palette**: Search across patients, files, and threads via a unified dialog bar (`SCR-020`).
*   **Audit & Telemetry Logs**: Chronicling sensitive read actions and auth events in database tables (`SCR-023`).

### Out of Scope
*   Replacing direct human clinician diagnosis or medical decisions.
*   Modifying EMR/HMS core databases or database record states directly from the Chatbot backend (read-only integrations).
*   Managing hospital inventory, billing, or patient portals directly.

---

## 3. Stakeholders and RACI Matrix

*   **Sponsor (Accountable)**: Approves ROI, operational budgets, and project phases.
*   **Product Owner (Accountable / Responsible)**: Manages product roadmap, feature requirements, and story priorities.
*   **Doctor / Nurse (Consulted)**: Reviews AI summary sections, checks clinical references, and validates search usability.
*   **Pharmacist (Consulted)**: Reviews medication and allergy safety check overlays.
*   **Hospital IT / Admin (Responsible / Consulted)**: Manages SSO authentication endpoints, local database environments, and EMR API sync channels.
*   **Security & Compliance (Accountable / Consulted)**: Performs privacy risk audits, approves access justifications, and checks logs.
*   **QA Lead (Responsible)**: Executes end-to-end contract validation, RAG metrics evaluation, and UAT sign-offs.

---

## 4. Business Requirements Index

| BR ID | Name | Priority | Target Scope |
|---|---|---|---|
| **BR-001** | Patient Question with Cited Answer | Must | [BR-001](BR-001-Patient-Question-Cited-Answer.md) |
| **BR-002** | AI Patient Summary | Must | [BR-002](BR-002-AI-Patient-Summary.md) |
| **BR-003** | OCR Document Indexing | Must | [BR-003](BR-003-OCR-Document-Indexing.md) |
| **BR-004** | Permission-Aware Retrieval | Must | [BR-004](BR-004-Permission-Aware-Retrieval.md) |
| **BR-005** | Impact Metrics Tracking | Must | [BR-005](BR-005-Impact-Metrics-Tracking.md) |
| **BR-006** | Graph RAG Relationships | Should | [BR-006](BR-006-Graph-RAG-Relationships.md) |
| **BR-007** | Drug/Allergy Conflict Warning | Should | [BR-007](BR-007-Drug-Allergy-Conflict-Warning.md) |

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | BA | Initial flat BRD |
| 2.0 | 2026-06-07 | Agent | Restructured into requirements index |
| 3.0 | 2026-06-07 | Agent | Updated to HMS AI Copilot positioning, added KPIs, and expanded scope mapping |
