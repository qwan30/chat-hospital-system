# Product Requirements Document (PRD)

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 4.0  
> Status: Approved  
> Owner: Product Owner / Business Analyst  
> Last Updated: 2026-07-12  

---

## 1. Product Overview
The product is an **AI Copilot integrated with the Hospital Management System (HMS)**. It serves as an intelligence extension over patient clinical files, unstructured document repositories, and scheduling calendars, providing clinician support while maintaining strict privacy boundaries and audit trails.

---

## 2. Personas & Operational Needs

The system targets specific hospital personas, transforming scattered HMS data into cited clinical actions:

| Persona | Operational Need | HMS System Pain Point | AI Copilot Success Signal |
|---|---|---|---|
| **Doctor** | Rapid, cited patient history and medication reviews. | Reviewing scattered EMR files and scanned charts takes 10–15 minutes. | Complete, cited patient summary rendered in <30 seconds. |
| **Nurse** | Quick access to ward instructions and latest vitals history. | Handover instructions are scattered across physical sheets and DB tables. | Natural language search queries return correct entries immediately. |
| **Pharmacist** | Automated medication and allergen safety reviews. | Manual drug interaction and allergy list cross-checking is error-prone. | Warning overlay displays with direct links to conflict EMR records. |
| **Records Staff** | Digital ingestion and semantic searching of scanned documents. | Scanned PDFs and paper forms are not searchable in standard HMS. | Uploaded documents are PaddleOCR indexed and searchable within 5 mins. |
| **Security Auditor** | Compliance monitoring of clinical patient data access. | Tracking access violations across disparate services is difficult. | Every sensitive read/query is tracked with a single trace ID in audit logs. |
| **IT Admin / DevOps**| Stable deployments and data cache synchronizations. | Ensuring system uptime on standard 16GB local machines is difficult. | Docker container stack deploys and operates within standard RAM limits. |
| **Product Manager**| Operational ROI and productivity metrics. | Proving time/cost savings to hospital stakeholders is subjective. | De-identified charts visualize time-saved metrics on the dashboard. |

---

## 3. Data Requirements & Source Mapping

The AI Copilot does not own transactional hospital data; it acts as a read-model cache.

| Object Category | Key Fields | Source System of Record | Privacy Level | Cache/RAG Usage |
|---|---|---|---|---|
| **Patient Demographics**| `id`, `mrn`, `name`, `dob`, `gender` | HMS PostgreSQL (HIS) | PHI | Cached for search / selector UI |
| **Encounters / Visits** | `id`, `patient_id`, `date`, `department` | HMS PostgreSQL (EMR) | PHI | Injected into clinical summaries |
| **Clinical Diagnoses** | `code` (ICD-10), `name`, `date` | HMS PostgreSQL (EMR) | PHI | Traversed for relationship RAG |
| **Medication Logs** | `drug_name`, `dose`, `route`, `dates` | HMS PostgreSQL (EMR) | PHI | Checked for drug/allergy warnings |
| **Allergy Records** | `allergen`, `reaction`, `severity` | HMS PostgreSQL (EMR) | PHI | Checked for drug/allergy warnings |
| **Lab Results** | `test_name`, `value`, `unit`, `timestamp`| HMS PostgreSQL (LIS) | PHI | Injected into clinical summaries |
| **Patient Documents** | `id`, `type`, `file_uri`, `status` | HMS File Store / S3 | PHI | Extracted for vector retrieval |
| **Document Chunks** | `text`, `embedding` (vector), `metadata` | Chatbot vector DB | PHI | Queried for semantic similarity |
| **Audit Events** | `actor`, `action`, `object`, `trace_id` | Chatbot PostgreSQL | Sensitive | Displayed in security log screens |
| **Metric Events** | `task`, `latency`, `time_saved`, `saved` | Chatbot PostgreSQL | De-identified | Displayed in metrics dashboards |

---

## 4. MVP Acceptance Gates
The integrated product is accepted when:
1.  **Auth & MFA Integration**: User SSO logins and MFA challenges are handled via the HMS authentication bridge.
2.  **Access Rules Verification**: Standard users trying to retrieve patient files outside their EMR clinical scope receive HTTP 403 blocks and trigger audit logs.
3.  **BFF Summaries**: The patient details screen renders a complete clinical overview with accurate citation links pointing back to HMS source documents or records.
4.  **OCR Processing Workers**: Batch PDF files uploaded are processed, chunked, embedded, and returned in global semantic queries.
5.  **Analytics Tracking**: Performance latency and estimated time/cost savings are recorded and rendered on the metrics dashboard.

---

## 5. CDSS Autonomous Alert Capability

### 5.1 Overview
The **Autonomous Clinical Decision Support System (CDSS) Agent** is an AI safety feature that proactively monitors patients by analyzing every newly uploaded clinical document for risk signals — without requiring a clinician to manually trigger a review. It extends the AI Copilot from a reactive Q&A tool into a proactive patient-safety layer.

### 5.2 How it works
1. After a document is uploaded and OCR-processed, the document ingestion pipeline automatically enqueues a CDSS analysis job.
2. The CDSS worker queries the patient's Knowledge Graph (`GraphEntity` + `GraphRelation`) to gather structured clinical context (diagnoses, medications, allergies, procedures).
3. The full document text combined with the graph context is submitted to the LLM with a structured prompt that requests JSON-formatted alert output: `{"alerts": [{"severity": "high"|"medium"|"low", "title": "...", "description": "..."}]}`.
4. Parsed alerts are persisted as `ClinicalAlert` records in the database, linked to the patient and source document.
5. Alerts surface in the HMS UI notification centre; high-severity alerts are highlighted immediately.

### 5.3 Personas served
| Persona | Benefit |
|---|---|
| **Doctor** | Receives proactive high-risk alerts without needing to re-read every uploaded document. |
| **Nurse** | Notified of patient risk escalations during shift handover before reviewing physical charts. |
| **Pharmacist** | CDSS catches drug-related risk signals in unstructured clinical notes automatically. |

### 5.4 Acceptance Criteria
- CDSS analysis is triggered automatically for every successfully processed document; no manual step is required.
- Generated `ClinicalAlert` records include `severity`, `title`, `description`, `patient_id`, and `source_document_id`.
- A high-severity CDSS alert (e.g., `n-007`) appears in the notification centre within 60 seconds of document processing completion.
- All CDSS alert generation events are captured in the audit log (actor: system, action: `cdss_alert_created`).
- The E2E test suite (`cdss-flow.spec.ts`) passes end-to-end across the full alert notification flow.

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | Product Owner | Initial flat PRD/SRS |
| 2.0 | 2026-06-07 | Agent | Restructured into standalone PRD |
| 3.0 | 2026-06-07 | Agent | Realigned to HMS-integrated positioning and detailed EMR data mappings |
| 4.0 | 2026-07-12 | Agent | Added Epic 5: CDSS Autonomous Alert Capability |
