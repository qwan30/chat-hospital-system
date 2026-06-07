# Product Requirements Document (PRD)

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 3.0  
> Status: Approved  
> Owner: Product Owner / Business Analyst  
> Last Updated: 2026-06-07  

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

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | Product Owner | Initial flat PRD/SRS |
| 2.0 | 2026-06-07 | Agent | Restructured into standalone PRD |
| 3.0 | 2026-06-07 | Agent | Realigned to HMS-integrated positioning and detailed EMR data mappings |
