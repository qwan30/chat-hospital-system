# Functional Requirements

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 3.0  
> Status: Approved  
> Owner: Product Owner / Business Analyst  
> Last Updated: 2026-06-07  

---

## Functional Requirements Catalog

| FR ID | Module | Requirement Description | Priority | Acceptance Criteria |
|---|---|---|---|---|
| **FR-001** | Auth | Authenticate users via local login or OIDC. | Must | User receives scoped session token. |
| **FR-002** | Authorization | Enforce RBAC/ABAC before retrieval. | Must | Unauthorized users receive HTTP 403. |
| **FR-003** | Patient Search | Search patient profiles within scope. | Must | Results exclude unauthorized patients. |
| **FR-004** | AI Chat | Ask natural language questions in chat workspace. | Must | Answer or safe refusal response returned. |
| **FR-005** | Citations | Show source document/page/table citation chips. | Must | Cited answers link back to source chunks. |
| **FR-006** | OCR | Upload PDF/image and OCR files asynchronously. | Must | Document moves to indexed/failed status. |
| **FR-007** | Document Search | Semantic search over indexed text chunks. | Must | Chunks returned with metadata. |
| **FR-008** | Patient Summary | Generate cited patient clinical summary. | Must | Summary lists history, meds, allergies, labs. |
| **FR-009** | Metrics | Track system latency, documents, and time saved. | Must | Metrics dashboard shows before/after stats. |
| **FR-010** | Audit | Log sensitive EMR and document read actions. | Must | Patient query creates structured audit event. |
| **FR-011** | Graph RAG | Traverses patient entity relationships. | Should | Relationship-based queries are cited. |
| **FR-012** | Drug Check | Flag potential medication/allergy conflicts. | Should | Conflict warning includes evidence source. |
| **FR-013** | Timeline | Display patient events chronologically. | Should | Filter timeline events by date or type. |
| **FR-014** | Admin | Manage roles and department configurations. | Should | Role updates affect user access bounds. |
| **FR-015** | Feedback | User can rate/report chatbot answers. | Should | Feedback is linked to query Trace ID. |
| **FR-016** | Dashboard | User can view AI/HMS operational dashboard. | Must | Dashboard displays recent activity, threads, and stats. |
| **FR-017** | HMS Integration| Sync patient data, lab values, and vitals from HMS. | Must | Chatbot read-models cache HMS snapshots. |
| **FR-018** | Patient Overview| View AI-enhanced patient overview built from HMS data. | Must | Merges HMS EMR charts with chatbot vectors. |
| **FR-019** | Access Request | Submit temporary clinical access requests. | Must | Request flows to HMS for justification checks. |
| **FR-020** | Workspace | Switch environment modes (Synthetic, Sandbox, Prod). | Must | Environment determines database routing. |
| **FR-021** | Global Search | Search patients, documents, threads, and commands. | Should | Cmd+K triggers global search dialog overlay. |
| **FR-022** | Document Flow | Upload, OCR, review, approve, and archive files. | Should | Ingestion screens support retry/archive states. |
| **FR-023** | AI Preferences | Configure streaming, citations, and theme choices. | Should | Settings menu stores user session preferences. |
| **FR-024** | Sync Monitoring | Admin can view HMS sync states and failures. | Should | Dashboard tracks API sync logs and health indicators. |
| **FR-025** | Cross-sys Audit | Log sensitive actions across both HMS and Chatbot. | Should | Trace IDs map requests across boundary layers. |

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | Product Owner | Initial requirements catalog |
| 2.0 | 2026-06-07 | Agent | Split into standalone functional requirements document |
| 3.0 | 2026-06-07 | Agent | Expanded requirements catalog with HMS-integrated features (FR-016 to FR-025) |
