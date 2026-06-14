# Entity Relationship Diagram (ERD)

> Project: AI-Powered Hospital Knowledge Assistant  
> Project Code: HOSP-AI-001  
> Version: 3.0  
> Status: In Sync  
> Owner: Backend Lead / Data Lead  
> Last Updated: 2026-06-14  

---

## ERD Mermaid Diagram

```mermaid
erDiagram
    users ||--o{ patient_permissions : has
    users ||--o{ documents : uploads
    users ||--o{ chat_threads : owns
    users ||--o{ chat_thread_participants : participates
    users ||--o{ chat_messages : sends
    users ||--o{ ai_queries : submits
    users ||--o{ audit_logs : triggers
    users ||--o{ hms_sync_logs : initiates

    patients ||--o{ patient_permissions : scoped_to
    patients ||--o{ documents : has
    patients ||--o{ document_chunks : denormalized_in
    patients ||--o{ chat_threads : linked_to
    patients ||--o{ chat_messages : referenced_by
    patients ||--o{ audit_logs : referenced_by
    patients ||--o{ hms_sync_logs : synced_for
    patients ||--o{ ai_queries : queried_for

    patient_permissions }o--|| users : granted_to
    patient_permissions }o--|| patients : grants_access_to

    documents ||--o{ document_pages : has
    documents ||--o{ document_chunks : contains

    document_pages ||--o{ document_chunks : contains

    chat_threads ||--o{ chat_thread_participants : has
    chat_threads ||--o{ chat_messages : contains

    ai_queries ||--o{ retrieved_evidence : has
    ai_queries ||--o{ chat_messages : linked_to

    document_chunks ||--o{ retrieved_evidence : cited_by
```

---

## Core Relationships

1. **User & Access Control**:
   - `users` receive `patient_permissions` with scoped access (read/summary/medication/upload/admin).
   - `users` own `chat_threads` and participate via `chat_thread_participants`.

2. **Patients & Clinical Data**:
   - `patients` hold the core clinical identity (MRN, demographics).
   - `patients` link to `documents` (scanned files), `chat_threads` (patient-linked or general), and `hms_sync_logs` (data sync tracking).

3. **Document Processing Pipeline**:
   - `documents` are processed page-by-page into `document_pages` (OCR text).
   - `document_pages` are chunked into `document_chunks` (semantic vector blocks with pgvector embeddings of dimension 1024).

4. **Chat & Retrieval**:
   - `ai_queries` record every AI question with status (`received → denied/no_evidence/completed/failed`), latency, and model info.
   - `retrieved_evidence` links queries to the specific `document_chunks` used as citations, with pre/post-rerank scores and retrieval method traces.
   - `chat_messages` store the full conversation history within `chat_threads`, each scoped to patient-linked or general.

5. **Audit & Sync**:
   - `audit_logs` provide immutable security trails for all actions (outcome: allowed/denied/failed).
   - `hms_sync_logs` track HMS data synchronization operations with progress counters (records synced/skipped/failed).

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | Backend Lead | Initial ERD |
| 2.0 | 2026-06-07 | Agent | Added EMR entity relationships |
| 3.0 | 2026-06-14 | Agent | Rewritten to match actual 13-table schema from db/models.py — replaced fictional allergies/medications/encounters/diagnoses/lab_results/metric_events with actual patient_permissions, chat_thread_participants, chat_messages, hms_sync_logs |
