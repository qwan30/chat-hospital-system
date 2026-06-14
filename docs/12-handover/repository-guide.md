# Repository Guide

> Project: HOSP-AI-001 · Version: 1.0 · Owner: Tech Lead · Last Updated: 2026-06-14

## 1. Repository Stats

| Metric | Value |
|--------|-------|
| Source files | 332 |
| Code symbols | 3,274 |
| Code edges | 6,683 |
| Execution flows | 216 |
| Languages | Python (137), TypeScript/TSX (150), JS, CSS |
| Backend | FastAPI 0.95+ |
| Frontend | Next.js 16.2 |
| Database | PostgreSQL + pgvector |

## 2. Backend (`app/backend/`)

### Route Modules (14)

| File | Prefix | Key Endpoints |
|------|--------|---------------|
| `auth.py` | `/auth` | GET /me |
| `patients.py` | `/patients` | GET list, overview, summary, meds |
| `documents.py` | `/documents` | GET list, POST upload, retry-ocr |
| `chat.py` | `/chat` | POST chat (10/min) |
| `chat_stream.py` | `/chat` | POST streaming (SSE) |
| `rag_trace.py` | `/chat` | GET trace |
| `chat_threads.py` | `/chat-threads` | CRUD |
| `hms.py` | `/hms` | POST sync, GET jobs |
| `audit.py` | `/audit` | GET logs (security/admin) |
| `settings.py` | `/settings` | GET/PUT (14 keys) |
| `dashboard.py` | `/dashboard` | GET summary |
| `search.py` | `/search` | GET global (20/min) |
| `access_requests.py` | `/access-requests` | POST create, GET status |
| `feedback.py` | `/feedback` | POST submit, GET metrics |

### Service Layer (18 modules)

| Module | Role |
|--------|------|
| `chat.py` | RAG pipeline orchestration |
| `chat_threads.py` | Thread lifecycle |
| `chat_utils.py` | Prompt building, stub answers |
| `embeddings.py` | Embedding generation + cache |
| `embedding/` | 3 providers (deterministic, ollama, openai) |
| `llm/` | 3 providers (stub, ollama, openai) |
| `reasoning.py` | 3 pipelines (SimpleQA, DecomposeQA, PatientSummary) |
| `retrieval.py` | Vector + BM25 + hybrid |
| `bm25.py` | BM25 keyword retrieval |
| `graph_rag.py` | Entity-relationship retrieval |
| `permissions.py` | ABAC + RBAC |
| `audit.py` | Audit trail |
| `drug_check.py` | Drug-allergy detection |
| `hms_connector.py` | HMS API client |
| `hms_sync.py` | Sync orchestration |
| `hms_appointments.py` | Appointments integration |
| `metrics.py` | Impact tracking |
| `general_knowledge.py` | Non-patient queries |

### Database (13 tables)

`users`, `patients`, `patient_permissions`, `documents`, `document_pages`, `document_chunks`, `ai_queries`, `retrieved_evidence`, `chat_threads`, `chat_thread_participants`, `chat_messages`, `audit_logs`, `hms_sync_logs`, `system_settings`

### Key Scripts

| Script | Purpose |
|--------|---------|
| `seed_dev.py` | Dev data seeding |
| `demo_setup.py` | Demo environment |
| `smoke_upload_index_chat.py` | Smoke test pipeline |
| `uat_product_api_check.py` | UAT validation (37 checks) |
| `run_rag_eval.py` | RAG evaluation (29 checks) |

## 3. Frontend (`app/frontend/`)

### Pages (14+ App Router)

| Route | Page |
|-------|------|
| `/login` | SSO login + MFA |
| `/dashboard` | Main dashboard |
| `/chat`, `/chat/new`, `/chat/[id]` | Chat (list, landing, thread) |
| `/patients`, `/patients/[id]`, `/patients/[id]/summary`, `/patients/[id]/meds`, `/patients/[id]/denied` | Patients |
| `/documents`, `/documents/upload`, `/documents/[id]`, `/documents/[id]/review` | Documents |
| `/audit` | Audit logs |
| `/metrics` | Impact metrics |
| `/timeline` | Patient timeline |
| `/settings` | User settings |

### Component Map

| Domain | Components |
|--------|-----------|
| `ui/` | 30+ shadcn primitives (Button, Card, Dialog, etc.) |
| `app-shell/` | Sidebar, Topbar, CommandPalette, Footer |
| `auth/` | LoginCard, MFACard, AuthMarketingPane |
| `chat/` | Composer, StreamingAnswer, AssistantCard, UserBubble |
| `patient/` | DetailHeader, AISummaryCard, MedicationList, EncounterTimeline |
| `document/` | DocumentsTable, UploadDropzone, BatchUploadModal |
| `evidence/` | CitationCard, EvidenceRail, DocumentViewerModal |
| `access/` | RequestModal, DeniedPanel, JustificationTextarea |
| `audit/` | EventsTable, FilterBar, MetricCard, EventDrawer |
| `viz/` | TrendLineChart, BarVolumeChart, StorageDonutChart |
| `empty/` | DashboardHero, EmptyStateCard, Skeleton components |

## 4. Data Flow

```
Clinician → Next.js UI → FastAPI BFF (14 routes)
    → Permission Check (RBAC + ABAC)
    → RAG Pipeline (embed → retrieve → rerank → generate → validate)
    → Drug Check (allergy + interaction)
    → Audit Log (immutable) + Metrics
    → PostgreSQL + pgvector (transactions + vectors)
    → Redis + RQ (async: OCR, indexing, HMS sync)
    → HMS Spring Boot (external source of truth)
```

## 5. LLM & AI Stack

| Component | Options |
|-----------|---------|
| LLM | Stub (test) / Ollama Qwen2.5 3B-7B / OpenAI-compatible |
| Embedding | Deterministic (SHA-256) / Ollama / OpenAI |
| Retrieval | Vector (pgvector HNSW) / BM25 / Hybrid / Graph RAG |
| Pipelines | Simple QA / Decompose QA / Patient Summary |
| Reranker | Cross-encoder (sentence-transformers, optional) |

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Complete repository tour from codebase analysis |
