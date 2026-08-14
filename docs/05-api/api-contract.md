# API Contract Specification

> Project: AI Copilot for Hospital Management System (HMS)  
> Project Code: HOSP-AI-001  
> Version: 4.1  
> Status: In Sync  
> Owner: API Lead / Data Lead  
> Last Updated: 2026-07-12  

---

## 1. Architecture

The backend is a **FastAPI BFF (Backend-for-Frontend)** serving the TanStack Start UI. The API base path is `/api/v1`. In development, the Vite frontend proxies `/api` → `http://localhost:8000/api/v1` (see `vite.config.ts`). All endpoints use JSON request/response bodies, UUID primary keys, and require JWT-based authentication via `get_current_user` dependency. Rate limiting is enforced via `slowapi`.

> **Important:** The frontend API client (`src/lib/api-client.ts`) defaults to `DEFAULT_API_URL = "/api"` — a relative path that goes through the Vite proxy. In SSR mode, the absolute URL `http://localhost:8000/api/v1` is used.

---

## 2. Route Map (16 route modules + CDSS worker pipeline)

All routes are mounted in `app/backend/src/hospital_ai/api/router.py`:

| Prefix | Module | Purpose |
|--------|--------|---------|
| `/health` | (inline) | Health check |
| `/auth` | `routes/auth.py` | Real credential login (`POST /token`), backend-issued demo login/status (`POST /demo`, `GET /demo/status`), and current user info (`GET /me`) |
| `/patients` | `routes/patients.py` | Patient CRUD, overviews, summaries |
| `/documents` | `routes/documents.py` | Document upload, listing, OCR management |
| `/chat` | `routes/chat.py` | Chat query (non-streaming, rate limited 10/min) |
| `/chat` | `routes/chat_stream.py` | Streaming chat with SSE (Server-Sent Events) |
| `/chat` | `routes/rag_trace.py` | RAG trace observability |
| `/chat-threads` | `routes/chat_threads.py` | Chat thread CRUD |
| `/hms` | `routes/hms.py` | HMS integration sync |
| `/audit` | `routes/audit.py` | Audit log access (security/admin only) |
| `/settings` | `routes/settings.py` | System settings management (14 configurable keys). **Admin-only**: GET requires `admin` or `security` role; PUT/DELETE requires `admin`. Frontend RBAC enforces this via `ADMIN_ONLY` in `rbac.ts`. |
| `/dashboard` | `routes/dashboard.py` | Dashboard summary metrics |
| `/search` | `routes/search.py` | Global entity search (rate limited 20/min) |
| `/access-requests` | `routes/access_requests.py` | Patient access requests |
| `/feedback` | `routes/feedback.py` | User feedback submission and metrics |
| `/graph` | `routes/graph.py` | Knowledge graph queries |
| `/medication-safety` | `routes/medication_safety.py` | Medication safety checks |

---

## 3. Key Endpoint Contracts

### Authentication contracts

`POST /api/v1/auth/token` remains the production credential flow. It accepts
the real username/password form and returns a bearer token for the active
local account. The frontend must keep this path separate from demo access.

`GET /api/v1/auth/demo/status` is public and returns whether the deployment is
configured to issue demo tokens:

```json
{ "enabled": true }
```

`POST /api/v1/auth/demo` accepts only an allowlisted synthetic persona:

```json
{ "role": "cardiologist" }
```

Supported roles are `cardiologist`, `hospitalist`, `rn`, `pharmacist`,
`front_desk`, `admin`, and `security`. The backend resolves the persona to an
active synthetic seeded account and signs a short-lived HS256 JWT with
`demo: true`, issuer, subject, email, role, issued-at, and expiry claims. The
frontend stores that bearer only in memory. It must not send a password or
construct a `dev-*` bearer token.

Demo issuance is available only when `HOSPITAL_AI_DEMO_MODE=true` and the
backend-only `HOSPITAL_AI_DEMO_JWT_SECRET` contains at least 32 characters.
Missing configuration returns `503`; an explicitly disabled deployment returns `403`. Demo tokens
are accepted by protected APIs only while demo mode remains enabled and are
resolved against an active local synthetic user. Demo data must remain
synthetic/de-identified.

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

### `GET /api/v1/chat-threads/{thread_id}/messages`
Get messages for a chat thread.

### `POST /api/v1/chat-threads/{thread_id}/messages`
Add a message to a chat thread.

### `GET /api/v1/chat-threads/{thread_id}/participants`
Get thread participants.

### `GET /api/v1/patients/search`
Search patients accessible to the current user.

### `GET /api/v1/patients/{id}/overview`
Merged EMR snapshot + AI summary with citations from HMS connector.

### `GET /api/v1/patients/{id}/timeline`
Get patient clinical timeline.

### `POST /api/v1/documents/`
Upload a document for OCR processing. Returns document metadata with status.

### `GET /api/v1/documents`
List documents accessible to the current user. Supports filtering by `patient_id` and `status`.

### `GET /api/v1/documents/{document_id}/pages/{page_number}/image`
Get document page image.

### `POST /api/v1/documents/search`
Search inside documents.

### `POST /api/v1/documents/{document_id}/retry-index`
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

### `GET /api/v1/access-requests/`
List access requests.

### `GET /api/v1/access-requests/{request_id}`
Get access request details.

### `PUT /api/v1/access-requests/{request_id}/review`
Review an access request.

### `GET /api/v1/audit/logs`
List audit events (security/admin role only). Supports filters: `patient_id`, `action`, `outcome`, `limit`.

### `POST /api/v1/hms/sync/patients/{id}`
Trigger HMS data synchronization for a specific patient.

### `POST /api/v1/hms/sync/appointments`
Trigger HMS appointments sync.

### `POST /api/v1/hms/sync/lab-results`
Trigger HMS lab results sync.

### `POST /api/v1/hms/sync/medical-records`
Trigger HMS medical records sync.

### `POST /api/v1/hms/sync/full`
Trigger HMS full sync.

### `GET /api/v1/hms/health`
HMS integration health check.

### `POST /api/v1/feedback/queries/{query_id}/feedback`
Submit thumbs up (+1), neutral (0), or thumbs down (-1) on an AI response. One feedback per query.

### `GET /api/v1/feedback/metrics/summary`
Aggregated impact metrics: total queries, avg latency, helpful rate, cost/time saved, audit denial count.

---

## 5. CDSS Clinical Alerts (Autonomous Worker-Driven)

> [!NOTE]
> `ClinicalAlert` records are **not created via a REST endpoint**. They are generated autonomously by the backend CDSS worker (`hospital_ai/workers/cdss.py`) as part of the document processing pipeline.

### How alerts are created

1. A document is uploaded via `POST /api/v1/documents/` and the `process_document` RQ job is enqueued.
2. Once OCR and indexing complete, the worker enqueues a `run_cdss_analysis(session, document_id)` job using `asyncio.to_thread` for non-blocking Redis dispatch.
3. The CDSS worker loads the patient's Knowledge Graph context (`GraphEntity`, `GraphRelation`) from PostgreSQL.
4. A medical risk analysis prompt is constructed and submitted to the local LLM.
5. The LLM JSON response is parsed and one or more `ClinicalAlert` rows are written to the `clinical_alerts` table with severity (`low` / `medium` / `high`), a title, and a description.

### Alert fields

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Auto-generated PK |
| `patient_id` | UUID | FK → patients |
| `source_document_id` | UUID\|null | FK → documents; nullable |
| `severity` | `low`\|`medium`\|`high` | LLM-assigned risk level |
| `title` | string | Short alert headline |
| `description` | string | Full clinical rationale |
| `is_acknowledged` | boolean | Default `false`; set by clinician |
| `created_at` / `updated_at` | timestamptz | Auto-managed |

### Future work — planned endpoint

```
GET /api/v1/patients/{patient_id}/alerts
```

This endpoint is **not yet implemented**. When added it should:
- Require an active `read` or higher permission scope for the target patient.
- Support filtering by `severity` and `is_acknowledged`.
- Return alerts ordered by `created_at DESC`.
- Include the `source_document_id` field so the UI can link back to the triggering document.

---

## 6. Standard Error Envelope

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
| 4.1 | 2026-07-12 | Agent | Added Section 5: CDSS Clinical Alerts — documents autonomous worker pipeline, alert fields, and future GET /patients/{id}/alerts endpoint |
