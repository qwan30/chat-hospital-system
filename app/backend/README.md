# Hospital AI Backend

FastAPI backend for the AI-Powered Hospital Knowledge Assistant. This slice implements the permission-before-retrieval RAG path with local development auth, async SQLAlchemy models, Alembic migrations, document indexing adapters, pgvector retrieval, cited chat responses, HMS appointment evidence import, and audit logging.

## Commands

```bash
cd app/backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m uvicorn hospital_ai.main:create_app --factory --reload
```

Install PostgreSQL and pgvector dependencies for the Docker-backed stack:

```bash
python -m pip install -e ".[postgres]"
```

Install lint tooling separately on a standard CPython environment:

```bash
python -m pip install -e ".[dev]"
```

```bash
cd app/backend
alembic upgrade head
python scripts/seed_dev.py
pytest
```

Local service smoke:

```bash
cd app/backend
alembic upgrade head
python scripts/smoke_upload_index_chat.py
```

The dev seed also imports one synthetic HMS appointment summary for Alice. That gives the patient-linked chat flow a de-identified HMS-derived evidence source without connecting to a live HMS database.

## Local Services

```bash
cd app/backend
docker compose up -d postgres redis
```

The default `.env.example` uses deterministic embeddings and a stub chat client so unit tests and local smoke checks do not require Ollama. Set `HOSPITAL_AI_EMBEDDING_PROVIDER=ollama` and `HOSPITAL_AI_CHAT_PROVIDER=ollama` to use local Ollama APIs.

The frontend is a TanStack Start/Vite app served on `http://localhost:8082` during local development. Keep `HOSPITAL_AI_CORS_ORIGINS` limited to explicit development origins such as `http://localhost:8082`, `http://localhost:3000`, and the fallback `http://localhost:3001`; do not replace it with a wildcard for PHI-bearing environments.

## Development Auth

MVP auth uses bearer tokens mapped to seeded synthetic users:

| Token | User |
|---|---|
| `dev-doctor` | `doctor@example.test` |
| `dev-records` | `records@example.test` |
| `dev-security` | `security@example.test` |
| `dev-admin` | `admin@example.test` |

Production OIDC can replace the token resolver without changing route dependencies.

## HMS Appointment Evidence Contract

Phase 3 connects one HMS-derived data family: appointment summaries. Records staff with upload scope or admins can import synthetic/de-identified appointment summaries through:

```http
POST /api/v1/hms/appointments/import
```

The import payload must include matching `patient_id` and `source_patient_id`. The backend stores the summary as an indexed `hms_appointment_summary` document with metadata including `source_system`, `source_family`, `source_record_id`, `source_path`, `source_lifecycle_state`, and `patient_permission_required`.

Do not import HMS identifiers such as CCCD, phone, email, address, insurance number, or booking-contact fields. Appointment evidence is patient-linked PHI and is retrieved only through the existing patient permission filter.

## Security Notes

- Use synthetic or de-identified data only.
- Patient permission is checked before retrieval and repeated inside the retrieval query.
- HMS appointment evidence is imported as patient-owned indexed evidence and inherits the same permission-before-retrieval boundary as uploaded documents.
- Denied patient, document, and chat accesses write `audit_logs`.
- The LLM prompt receives only numbered evidence blocks returned by permission-filtered retrieval.
