# API Contract Specification

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 4.0  
> Status: In Sync  
> Owner: API Lead / Data Lead  
> Last Updated: 2026-06-14  

---

## 1. Architecture

The backend is a **FastAPI BFF (Backend-for-Frontend)** serving the Next.js UI. The API base path is `/api/v1`. All endpoints use JSON request/response bodies, UUID primary keys, and require JWT-based authentication via `get_current_user` dependency. Rate limiting is enforced via `slowapi`.

---

## 2. Route Map (14 route modules)

All routes are mounted in `app/backend/src/hospital_ai/api/router.py`:

| Prefix | Module | Purpose |
|--------|--------|---------|
| `/health` | (inline) | Health check |
| `/auth` | `routes/auth.py` | Current user info (`GET /me`) |
| `/patients` | `routes/patients.py` | Patient CRUD, overviews, summaries |
| `/documents` | `routes/documents.py` | Document upload, listing, OCR management |
| `/chat` | `routes/chat.py` | Chat query (non-streaming, rate limited 10/min) |
| `/chat` | `routes/chat_stream.py` | Streaming chat with SSE (Server-Sent Events) |
| `/chat` | `routes/rag_trace.py` | RAG trace observability |
| `/chat-threads` | `routes/chat_threads.py` | Chat thread CRUD |
| `/hms` | `routes/hms.py` | HMS integration sync |
| `/audit` | `routes/audit.py` | Audit log access (security/admin only) |
| `/settings` | `routes/settings.py` | System settings management (14 configurable keys) |
| `/dashboard` | `routes/dashboard.py` | Dashboard summary metrics |
| `/search` | `routes/search.py` | Global entity search (rate limited 20/min) |
| `/access-requests` | `routes/access_requests.py` | Patient access requests |
| `/feedback` | `routes/feedback.py` | User feedback submission and metrics |

---

## 3. Key Endpoint Contracts

### `POST /api/v1/chat`
Submit a clinical question with RAG pipeline.

**Request:**
```json
{
  "patient_id": "uuid",
  "question": "What are this patient's recent lab results?",
  "top_k": 5,
  "thread_id": "uuid | null",
  "pipeline": "auto | simple | decompose | patient_summary"
}
```

**Response (200 OK):**
```json
{
  "query_id": "uuid",
  "answer": "Based on documented evidence...",
  "citations": [
    {
      "evidence_id": "E1",
      "chunk_id": "uuid",
      "document_title": "Lab Report.pdf",
      "page": 1,
      "excerpt": "..."
    }
  ],
  "confidence": "high | medium | low",
  "disclaimer": "This is an AI-generated response...",
  "thread_id": "uuid | null",
  "pipeline": "simple_qa | decompose_qa | patient_summary",
  "warnings": []
}
```

### `POST /api/v1/chat/stream`
Streaming variant of the chat endpoint using Server-Sent Events. Same request body, yields token-by-token chunks via SSE.

### `GET /api/v1/chat/queries/{query_id}/trace`
RAG observability trace. Returns all retrieved chunks with:
- Pre-rerank and post-rerank scores
- Retrieval method (vector/bm25/hybrid/graph)
- Rerank method
- Citation labels, document titles, page numbers
- Total query latency

Only accessible by the query owner or admin.

### `POST /api/v1/chat-threads`
Create a new chat thread.

**Request:**
```json
{
  "title": "Cardiology consult",
  "scope": "patient-linked | general",
  "patient_id": "uuid | null"
}
```

### `GET /api/v1/patients`
List patients accessible to the current user, filtered by active `patient_permissions` scopes (read/summary/medication/upload/admin).

### `GET /api/v1/patients/{id}/overview`
Merged EMR snapshot + AI summary with citations from HMS connector.

### `GET /api/v1/patients/{id}/summary`
AI-generated patient summary.

### `GET /api/v1/patients/{id}/meds`
Medication review with drug interaction checking via `DrugCheckService`.

### `POST /api/v1/documents/upload`
Upload a document for OCR processing. Returns document metadata with status.

### `GET /api/v1/documents`
List documents accessible to the current user. Supports filtering by `patient_id` and `status`.

### `POST /api/v1/documents/{id}/retry-ocr`
Re-enqueue a failed document for OCR reprocessing via RQ worker queue.

### `GET /api/v1/dashboard/summary`
Aggregated dashboard metrics.

**Response:**
```json
{
  "recent_patients": [{"id": "uuid", "name": "...", "mrn": "..."}],
  "document_stats": {"indexed": 142, "processing": 3, "failed": 1},
  "metrics": {"hours_saved": 42.5, "cost_saved_usd": 3187.50},
  "systems_health": {"hms_api": "healthy", "ollama_inference": "healthy"}
}
```

### `GET /api/v1/search/global?q=...`
Command-palette global search across patients, documents, and chat threads. Results filtered by active user permission scopes. Rate limited to 20/minute.

### `POST /api/v1/access-requests`
Submit clinical justification to request patient access (break-glass scenario).

### `GET /api/v1/audit/logs`
List audit events (security/admin role only). Supports filters: `patient_id`, `action`, `outcome`, `limit`.

### `POST /api/v1/hms/sync/patients/{id}`
Trigger HMS data synchronization for a specific patient.

### `GET /api/v1/hms/jobs/{job_id}`
Check HMS sync job status and progress (records synced/skipped/failed).

### `POST /api/v1/feedback/queries/{query_id}/feedback`
Submit thumbs up (+1), neutral (0), or thumbs down (-1) on an AI response. One feedback per query.

### `GET /api/v1/feedback/metrics/summary`
Aggregated impact metrics: total queries, avg latency, helpful rate, cost/time saved, audit denial count.

---

## 4. Standard Error Envelope

```json
{
  "error": "FORBIDDEN",
  "message": "You do not have active treatment relationship scope for this patient.",
  "metadata": {"trace_id": "fb8a9d2a-..."}
}
```

Error codes defined in [error-codes.md](error-codes.md). The `AppError` base class in `core/errors.py` provides consistent error formatting with `PermissionDeniedError`, `ExternalServiceError`, etc.

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | API Lead | Initial contracts |
| 2.0 | 2026-06-07 | Agent | Restructured with BFF/HMS separation |
| 3.0 | 2026-06-07 | Agent | Added HMS integration and BFF endpoints |
| 4.0 | 2026-06-14 | Agent | Rewritten to match actual 14 route modules from `api/router.py` — added chat-threads, feedback, rag_trace, chat_stream; corrected endpoint paths |
