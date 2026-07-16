# Business Rules

> Project: AI-Powered Hospital Knowledge Assistant  
> Project Code: HOSP-AI-001  
> Version: 2.1  
> Status: Draft  
> Owner: Product Owner / Business Analyst  
> Last Updated: 2026-07-12  

---

## Business Rules Catalog

| Rule ID | Rule | Description / Context |
|---|---|---|
| BR-SEC-001 | User must be authenticated before accessing patient data. | Mandatory check at API gateway level. |
| BR-SEC-002 | Retrieval must apply RBAC/ABAC before LLM context creation. | Permission filter applied in PostgreSQL/pgvector queries, ensuring zero unauthorized chunks reach the LLM. |
| BR-RAG-001 | Evidence metadata must be preserved through retrieval and generation. | Retain source file, page number, and chunk ID in vectors to display in citations. |
| BR-AI-001 | If evidence is insufficient, AI must say so. | Do not hallucinate or make assumptions when information is not present in retrieved context. |
| BR-MED-001 | AI output is assistive and must not replace clinician judgment. | Present a warning message in the UI stating that clinician verification is required. |
| BR-AUD-001 | All patient-related queries create audit events. | Audit event must capture actor ID, timestamp, patient ID, query type, and request IP. |
| BR-MET-001 | AI workflows create metric events. | Performance and time-saved tracking events must be recorded (de-identified). |
| BR-OCR-001 | OCR text must link to original document/page. | Store document references per text block during ingestion. |
| BR-CDSS-001 | The system shall automatically analyze newly uploaded clinical documents for patient risk and generate clinical alerts when risk factors are detected. | After successful document ingestion and graph indexing, an autonomous CDSS worker must run LLM-based risk analysis using the patient's Knowledge Graph context and persist any resulting `ClinicalAlert` records (severity: low / medium / high) to the database without requiring manual clinician initiation. |

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | Product Owner | Initial business rules draft |
| 2.0 | 2026-06-07 | Agent | Restructured and separated from requirements pack |
| 2.1 | 2026-07-12 | Agent | Added BR-CDSS-001 for Autonomous CDSS Agent monitoring rule |
