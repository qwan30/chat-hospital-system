# Database Schema

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 4.0  
> Status: In Sync  
> Owner: Database Lead / Lead Dev  
> Last Updated: 2026-06-14  

---

## 1. Data Ownership Boundary

*   **HMS Core Database (Source of Record)**: Owns master tables for clinical patient records, logins, appointments, and access requests. Accessed via the HMS Spring Boot API.
*   **AI Assistant Database (Cache & AI Engine)**: Owns vector tables (`document_chunks`), raw OCR extracts (`document_pages`), chat thread histories (`chat_threads`, `chat_messages`), AI query logs (`ai_queries`, `retrieved_evidence`), impact metrics, and security audit trails (`audit_logs`). Synchronized with HMS data via periodic sync jobs tracked in `hms_sync_logs`.

---

## 2. Core Tables (13 tables)

### users
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default uuid4 |
| email | VARCHAR(320) | UNIQUE, NOT NULL, INDEX |
| full_name | VARCHAR(255) | NOT NULL |
| department | VARCHAR(128) | NULLABLE |
| role | VARCHAR(32) | NOT NULL, CHECK: doctor/nurse/pharmacist/lab_staff/records_staff/security/admin |
| is_active | BOOLEAN | NOT NULL, DEFAULT true |
| created_at | TIMESTAMPTZ | NOT NULL, server_default now() |
| updated_at | TIMESTAMPTZ | NOT NULL, server_default now(), onupdate now() |
| deleted_at | TIMESTAMPTZ | NULLABLE (soft delete) |

### patients
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default uuid4 |
| mrn | VARCHAR(64) | UNIQUE, NOT NULL, INDEX |
| full_name | VARCHAR(255) | NOT NULL |
| dob | DATE | NULLABLE |
| department | VARCHAR(128) | NULLABLE |
| status | VARCHAR(32) | NOT NULL, DEFAULT 'active' |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
| deleted_at | TIMESTAMPTZ | NULLABLE |

### patient_permissions
Per-user, per-patient access scopes. Enforces RBAC + ABAC boundary before any RAG retrieval.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NOT NULL, INDEX |
| patient_id | UUID | FK → patients.id, NOT NULL, INDEX |
| scope | VARCHAR(32) | NOT NULL, CHECK: read/summary/medication/upload/admin |
| source | VARCHAR(64) | NOT NULL, DEFAULT 'manual' |
| expires_at | TIMESTAMPTZ | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
| deleted_at | TIMESTAMPTZ | NULLABLE |

UNIQUE constraint on (user_id, patient_id, scope).

### documents
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| patient_id | UUID | FK → patients.id, NOT NULL, INDEX |
| uploaded_by | UUID | FK → users.id, NOT NULL |
| title | VARCHAR(255) | NOT NULL |
| document_type | VARCHAR(64) | NOT NULL |
| storage_uri | TEXT | NOT NULL |
| mime_type | VARCHAR(128) | NOT NULL |
| status | VARCHAR(32) | NOT NULL, DEFAULT 'uploaded', CHECK: uploaded/ocr_processing/ocr_failed/ocr_completed/indexing/index_failed/indexed/archived |
| page_count | INTEGER | NULLABLE |
| ocr_error | TEXT | NULLABLE |
| index_generation | INTEGER | NOT NULL, DEFAULT 0 |
| indexed_source_sha256 | VARCHAR(64) | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
| deleted_at | TIMESTAMPTZ | NULLABLE |

### document_pages
OCR-extracted text per page, one row per page per document.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| document_id | UUID | FK → documents.id, NOT NULL, INDEX |
| page_number | INTEGER | NOT NULL |
| ocr_text | TEXT | NOT NULL |
| ocr_confidence | NUMERIC | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
| deleted_at | TIMESTAMPTZ | NULLABLE |

UNIQUE constraint on (document_id, page_number).

### document_chunks
Vector-indexed semantic chunks. Embeddings stored via pgvector `EmbeddingVector(1024)`.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| document_id | UUID | FK → documents.id, NOT NULL, INDEX |
| page_id | UUID | FK → document_pages.id, NOT NULL, INDEX |
| patient_id | UUID | FK → patients.id, NOT NULL, INDEX (denormalized) |
| chunk_index | INTEGER | NOT NULL |
| content | TEXT | NOT NULL |
| token_count | INTEGER | NULLABLE |
| embedding | VECTOR(1024) | NULLABLE |
| metadata | JSON | NOT NULL, DEFAULT {} |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
| deleted_at | TIMESTAMPTZ | NULLABLE |

UNIQUE constraint on (document_id, chunk_index).

### ai_queries
Every chat/AI question asked, with latency and status tracking. Immutable (no updated_at, no soft delete).

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NOT NULL, INDEX |
| patient_id | UUID | FK → patients.id, NOT NULL, INDEX |
| question | TEXT | NOT NULL |
| answer | TEXT | NULLABLE |
| status | VARCHAR(32) | NOT NULL (received/denied/no_evidence/completed/failed) |
| latency_ms | INTEGER | NULLABLE |
| model | VARCHAR(128) | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL, server_default now() |

### retrieved_evidence
Links AI queries to the document chunks used as evidence, with RAG trace observability fields.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| ai_query_id | UUID | FK → ai_queries.id, NOT NULL, INDEX |
| chunk_id | UUID | FK → document_chunks.id, NOT NULL, INDEX |
| rank | INTEGER | NOT NULL |
| score | NUMERIC | NOT NULL |
| citation_label | VARCHAR(16) | NOT NULL |
| rerank_score | NUMERIC | NULLABLE |
| retrieval_method | VARCHAR(32) | NULLABLE |
| rerank_method | VARCHAR(32) | NULLABLE |

### chat_threads
Conversation threads with patient-linked or general scope. Supports private/shared visibility.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| title | VARCHAR(255) | NOT NULL |
| scope | VARCHAR(32) | NOT NULL, CHECK: general/patient-linked |
| visibility | VARCHAR(32) | NOT NULL, DEFAULT 'private', CHECK: private/shared |
| status | VARCHAR(32) | NOT NULL, DEFAULT 'active', CHECK: active/archived |
| owner_user_id | UUID | FK → users.id, NOT NULL, INDEX |
| patient_id | UUID | FK → patients.id, NULLABLE, INDEX |
| created_trace_id | VARCHAR(64) | NOT NULL |
| last_message_at | TIMESTAMPTZ | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
| deleted_at | TIMESTAMPTZ | NULLABLE |

CHECK: (scope = 'general' AND patient_id IS NULL) OR (scope = 'patient-linked' AND patient_id IS NOT NULL)

### chat_thread_participants
Multi-user access control for chat threads with three-level access.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| thread_id | UUID | FK → chat_threads.id, NOT NULL, INDEX |
| user_id | UUID | FK → users.id, NOT NULL, INDEX |
| access_level | VARCHAR(32) | NOT NULL, CHECK: owner/write/read |
| can_share | BOOLEAN | NOT NULL, DEFAULT false |
| added_by_user_id | UUID | FK → users.id, NOT NULL |
| created_trace_id | VARCHAR(64) | NOT NULL |
| last_read_at | TIMESTAMPTZ | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
| deleted_at | TIMESTAMPTZ | NULLABLE |

UNIQUE constraint on (thread_id, user_id).

### chat_messages
Individual messages within a chat thread, linked to AI queries and patient context. Immutable.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| thread_id | UUID | FK → chat_threads.id, NOT NULL, INDEX |
| sender_user_id | UUID | FK → users.id, NULLABLE, INDEX |
| ai_query_id | UUID | FK → ai_queries.id, NULLABLE, INDEX |
| patient_id | UUID | FK → patients.id, NULLABLE, INDEX |
| role | VARCHAR(32) | NOT NULL, CHECK: user/assistant/system |
| scope | VARCHAR(32) | NOT NULL, CHECK: general/patient-linked |
| content | TEXT | NOT NULL |
| patient_permission_state | VARCHAR(32) | NOT NULL, CHECK: not-required/pending/allowed/denied |
| citations | JSON | NOT NULL, DEFAULT [] |
| metadata | JSON | NOT NULL, DEFAULT {} |
| trace_id | VARCHAR(64) | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL, server_default now() |

### audit_logs
Immutable security audit trail. No soft delete, no update timestamp.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| actor_user_id | UUID | FK → users.id, NULLABLE, INDEX |
| action | VARCHAR(128) | NOT NULL |
| object_type | VARCHAR(64) | NOT NULL |
| object_id | UUID | NULLABLE |
| patient_id | UUID | FK → patients.id, NULLABLE, INDEX |
| outcome | VARCHAR(32) | NOT NULL, CHECK: allowed/denied/failed |
| trace_id | VARCHAR(64) | NOT NULL |
| ip_address | VARCHAR(64) | NULLABLE (INET on PostgreSQL, VARCHAR on SQLite) |
| metadata | JSON | NOT NULL, DEFAULT {} |
| created_at | TIMESTAMPTZ | NOT NULL, server_default now() |

### hms_sync_logs
Tracks HMS data synchronization operations with progress counters.

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| patient_id | UUID | FK → patients.id, NOT NULL, INDEX |
| initiated_by | UUID | FK → users.id, NOT NULL, INDEX |
| sync_type | VARCHAR(32) | NOT NULL, CHECK: appointments/lab_results/medical_records/full |
| status | VARCHAR(32) | NOT NULL, DEFAULT 'pending', CHECK: pending/running/completed/failed/partial |
| records_synced | INTEGER | NOT NULL, DEFAULT 0 |
| records_skipped | INTEGER | NOT NULL, DEFAULT 0 |
| records_failed | INTEGER | NOT NULL, DEFAULT 0 |
| error_message | TEXT | NULLABLE |
| trace_id | VARCHAR(64) | NOT NULL |
| started_at | TIMESTAMPTZ | NULLABLE |
| completed_at | TIMESTAMPTZ | NULLABLE |
| metadata | JSON | NOT NULL, DEFAULT {} |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

### system_settings
Key-value configuration store for runtime application settings (added in migration 0005).
Stored via `db/settings_store.py` with 14 configurable keys.

---

## 3. Common Patterns

*   **Soft Delete**: `users`, `patients`, `patient_permissions`, `documents`, `document_pages`, `document_chunks`, `chat_threads`, `chat_thread_participants` use `deleted_at` (via `SoftDeleteMixin`).
*   **Timestamps**: Mutable entities inherit `TimestampMixin` (created_at + updated_at). Immutable entities (`audit_logs`, `ai_queries`, `chat_messages`, `retrieved_evidence`) only have created_at.
*   **Identity**: All primary keys are UUIDs generated server-side via `uuid.uuid4`.
*   **Migrations**: Managed by Alembic, 6 migration files under `app/backend/alembic/versions/`.

---

## 4. Entity Relationships

```
users ──< patient_permissions >── patients
users ──< documents (uploaded_by)
users ──< chat_threads (owner_user_id)
users ──< chat_thread_participants
patients ──< documents
patients ──< document_chunks (denormalized patient_id)
patients ──< chat_threads
patients ──< audit_logs
patients ──< hms_sync_logs
documents ──< document_pages
documents ──< document_chunks
document_pages ──< document_chunks
chat_threads ──< chat_thread_participants
chat_threads ──< chat_messages
ai_queries ──< retrieved_evidence
ai_queries ──< chat_messages
document_chunks ──< retrieved_evidence
```

---

## 5. Migration History

| Migration | Description |
|-----------|-------------|
| 0001 | Initial schema: users, patients, patient_permissions, documents, document_pages, document_chunks, audit_logs, ai_queries, retrieved_evidence |
| 0002 | Added document index_generation and indexed_source_sha256 tracking |
| 0003 | Added chat_threads, chat_thread_participants, chat_messages |
| 0004 | Added hms_sync_logs |
| 0005 | Added system_settings key-value store |
| 0006 | Added Phase 4 tables (extended observability and access control) |

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | Database Lead | Initial entity definitions |
| 2.0 | 2026-06-07 | Agent | Restructured into DDL schema guide |
| 3.0 | 2026-06-07 | Agent | Added read-model caching DDL and RAG join examples |
| 4.0 | 2026-06-14 | Agent | Full rewrite to match actual 13-table schema from `db/models.py` — replaced fictional cached_* tables, added chat_threads, patient_permissions, hms_sync_logs, retrieved_evidence, migration history |
