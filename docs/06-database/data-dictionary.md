# Data Dictionary

> Project: HOSP-AI-001 · Version: 1.0 · Last Updated: 2026-06-14  

Column-level reference for all 13 tables. See `db-schema.md` for relationships and constraints. See `erd.md` for entity diagram. `*` = NOT NULL.

## users
| Column | Type | Null | Default |
|--------|------|------|---------|
| id* | UUID | | uuid4() |
| email* | VARCHAR(320) | | UNIQUE |
| full_name* | VARCHAR(255) | | |
| department | VARCHAR(128) | YES | NULL |
| role* | VARCHAR(32) | | CHECK: 7 roles |
| is_active* | BOOLEAN | | true |
| created_at* | TIMESTAMPTZ | | now() |
| updated_at* | TIMESTAMPTZ | | now() |
| deleted_at | TIMESTAMPTZ | YES | Soft delete |

## patients
| Column | Type | Null | Default |
|--------|------|------|---------|
| id* | UUID | | |
| mrn* | VARCHAR(64) | | UNIQUE |
| full_name* | VARCHAR(255) | | |
| dob | DATE | YES | |
| department | VARCHAR(128) | YES | |
| status* | VARCHAR(32) | | 'active' |
| + TimestampMixin, SoftDeleteMixin | | | |

## patient_permissions
| Column | Type | Null | Notes |
|--------|------|------|-------|
| id* | UUID | | |
| user_id* | UUID FK→users | | |
| patient_id* | UUID FK→patients | | |
| scope* | VARCHAR(32) | | read/summary/medication/upload/admin |
| source* | VARCHAR(64) | 'manual' | manual/hms_sync/access_request |
| expires_at | TIMESTAMPTZ | YES | |
| UNIQUE(user_id, patient_id, scope) | | | |

## documents
| Column | Type | Null | Notes |
|--------|------|------|-------|
| id* | UUID | | |
| patient_id* | UUID FK | | |
| uploaded_by* | UUID FK→users | | |
| title* | VARCHAR(255) | | |
| document_type* | VARCHAR(64) | | |
| storage_uri* | TEXT | | |
| mime_type* | VARCHAR(128) | | |
| status* | VARCHAR(32) | 'uploaded' | 8-state lifecycle |
| page_count | INTEGER | YES | |
| ocr_error | TEXT | YES | |
| index_generation* | INTEGER | 0 | |
| indexed_source_sha256 | VARCHAR(64) | YES | |

## document_pages
| Column | Type | Null | Notes |
|--------|------|------|-------|
| id* | UUID | | |
| document_id* | UUID FK | | |
| page_number* | INTEGER | | |
| ocr_text* | TEXT | | |
| ocr_confidence | NUMERIC | YES | 0.0–1.0 |
| UNIQUE(document_id, page_number) | | | |

## document_chunks
| Column | Type | Null | Notes |
|--------|------|------|-------|
| id* | UUID | | |
| document_id* | UUID FK | | |
| page_id* | UUID FK | | |
| patient_id* | UUID FK | | denormalized |
| chunk_index* | INTEGER | | |
| content* | TEXT | | |
| token_count | INTEGER | YES | |
| embedding | VECTOR(1024) | YES | pgvector |
| metadata* | JSON | {} | |
| UNIQUE(document_id, chunk_index) | | | |

## ai_queries
| Column | Type | Null | Notes |
|--------|------|------|-------|
| id* | UUID | | |
| user_id* | UUID FK | | |
| patient_id* | UUID FK | | |
| question* | TEXT | | |
| answer | TEXT | YES | |
| status* | VARCHAR(32) | | received/denied/no_evidence/completed/failed |
| latency_ms | INTEGER | YES | |
| model | VARCHAR(128) | YES | |
| created_at* | TIMESTAMPTZ | now() | Immutable |

## retrieved_evidence
| Column | Type | Null | Notes |
|--------|------|------|-------|
| id* | UUID | | |
| ai_query_id* | UUID FK | | |
| chunk_id* | UUID FK | | |
| rank* | INTEGER | | 1-based |
| score* | NUMERIC | | |
| citation_label* | VARCHAR(16) | | E1, E2... |
| rerank_score | NUMERIC | YES | |
| retrieval_method | VARCHAR(32) | YES | vector/bm25/hybrid/graph |
| rerank_method | VARCHAR(32) | YES | |

## chat_threads
| Column | Type | Null | Notes |
|--------|------|------|-------|
| id* | UUID | | |
| title* | VARCHAR(255) | | |
| scope* | VARCHAR(32) | | general/patient-linked |
| visibility* | VARCHAR(32) | 'private' | private/shared |
| status* | VARCHAR(32) | 'active' | active/archived |
| owner_user_id* | UUID FK | | |
| patient_id | UUID FK | YES | NULL if general |
| created_trace_id* | VARCHAR(64) | | |
| last_message_at | TIMESTAMPTZ | YES | |
| CHECK: scope matches patient_id nullability | | | |

## chat_thread_participants
| Column | Type | Null | Notes |
|--------|------|------|-------|
| id* | UUID | | |
| thread_id* | UUID FK | | |
| user_id* | UUID FK | | |
| access_level* | VARCHAR(32) | | owner/write/read |
| can_share* | BOOLEAN | false | |
| added_by_user_id* | UUID FK | | |
| created_trace_id* | VARCHAR(64) | | |
| last_read_at | TIMESTAMPTZ | YES | |
| UNIQUE(thread_id, user_id) | | | |

## chat_messages
| Column | Type | Null | Notes |
|--------|------|------|-------|
| id* | UUID | | |
| thread_id* | UUID FK | | |
| sender_user_id | UUID FK | YES | |
| ai_query_id | UUID FK | YES | |
| patient_id | UUID FK | YES | |
| role* | VARCHAR(32) | | user/assistant/system |
| scope* | VARCHAR(32) | | general/patient-linked |
| content* | TEXT | | |
| patient_permission_state* | VARCHAR(32) | | not-required/pending/allowed/denied |
| citations* | JSON | [] | |
| metadata* | JSON | {} | |
| trace_id* | VARCHAR(64) | | |
| created_at* | TIMESTAMPTZ | now() | Immutable |

## audit_logs
| Column | Type | Null | Notes |
|--------|------|------|-------|
| id* | UUID | | |
| actor_user_id | UUID FK | YES | |
| action* | VARCHAR(128) | | chat.ask, search.global... |
| object_type* | VARCHAR(64) | | |
| object_id | UUID | YES | |
| patient_id | UUID FK | YES | |
| outcome* | VARCHAR(32) | | allowed/denied/failed |
| trace_id* | VARCHAR(64) | | |
| ip_address | VARCHAR(64) | YES | INET(PG)/VARCHAR(SQLite) |
| metadata* | JSON | {} | |
| created_at* | TIMESTAMPTZ | now() | Immutable |

## hms_sync_logs
| Column | Type | Null | Notes |
|--------|------|------|-------|
| id* | UUID | | |
| patient_id* | UUID FK | | |
| initiated_by* | UUID FK | | |
| sync_type* | VARCHAR(32) | | appointments/lab_results/medical_records/full |
| status* | VARCHAR(32) | 'pending' | pending/running/completed/failed/partial |
| records_synced* | INTEGER | 0 | |
| records_skipped* | INTEGER | 0 | |
| records_failed* | INTEGER | 0 | |
| error_message | TEXT | YES | |
| trace_id* | VARCHAR(64) | | |
| started_at | TIMESTAMPTZ | YES | |
| completed_at | TIMESTAMPTZ | YES | |
| metadata* | JSON | {} | |
| + TimestampMixin | | | |

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Column-level dictionary for all 13 tables from db/models.py |
