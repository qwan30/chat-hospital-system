# Database Schema & Entity Caching

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 3.0  
> Status: Approved  
> Owner: Database Lead / Lead Dev  
> Last Updated: 2026-06-07  

---

## 1. Data Ownership Boundary

*   **HMS Core Database (Source of Record)**: Owns master tables for `users`, `roles`, `patients`, `encounters`, `diagnoses`, `medications`, `allergies`, `lab_results`, and patient access request states.
*   **AI Assistant Database (Cache & AI Engine)**: Owns vector tables (`document_chunks`), raw OCR extracts (`document_pages`), chat thread histories (`chat_threads`, `chat_messages`), time-saved telemetry (`metric_events`), and security audit trails (`audit_events`). It maintains read-only, cached read-models of HMS patient profiles to accelerate pgvector HNSW query joins.

---

## 2. EMR Read Model Cache Schema (AI Assistant DB)

The following tables are updated via the change feed synchronization process and joined with vector search queries:

```sql
-- Read-model Cache for Patient profiles
CREATE TABLE cached_patients (
    patient_id UUID PRIMARY KEY,
    mrn VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    gender VARCHAR(10),
    department VARCHAR(100), -- admittance department
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Read-model Cache for active Allergy lists
CREATE TABLE cached_allergies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES cached_patients(patient_id) ON DELETE CASCADE,
    allergen VARCHAR(255) NOT NULL,
    reaction VARCHAR(255),
    severity VARCHAR(50), -- Low/Med/High
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Read-model Cache for active Medication lists
CREATE TABLE cached_medications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES cached_patients(patient_id) ON DELETE CASCADE,
    drug_name VARCHAR(255) NOT NULL,
    dose VARCHAR(100),
    route VARCHAR(100),
    start_date DATE,
    end_date DATE,
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. Vector Retrieval & Joining Example

When performing a patient-grounded chat query, the RAG engine joins pgvector text chunks with cached EMR patient profiles to ensure scope boundaries are enforced:

```sql
SELECT 
    c.id, 
    c.content, 
    c.page_number,
    p.mrn,
    (c.embedding <=> :query_embedding) AS distance
FROM document_chunks c
JOIN cached_patients p ON c.metadata->>'patient_id' = p.patient_id::text
WHERE p.patient_id = :target_patient_id
  AND p.department = :user_authorized_department -- Enforces ABAC filter
ORDER BY distance LIMIT 5;
```

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | Database Lead | Initial entity definitions |
| 2.0 | 2026-06-07 | Agent | Restructured into DDL schema guide |
| 3.0 | 2026-06-07 | Agent | Added read-model caching DDL and scoped RAG join SQL examples |
