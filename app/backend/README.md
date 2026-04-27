# Hospital AI Backend

FastAPI backend for the AI-Powered Hospital Knowledge Assistant. This first slice implements the permission-before-retrieval RAG path with local development auth, async SQLAlchemy models, Alembic migrations, document indexing adapters, pgvector retrieval, cited chat responses, and audit logging.

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
python -m pip install -e ".[lint]"
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

## Local Services

```bash
cd app/backend
docker compose up -d postgres redis
```

The default `.env.example` uses deterministic embeddings and a stub chat client so unit tests and local smoke checks do not require Ollama. Set `HOSPITAL_AI_EMBEDDING_PROVIDER=ollama` and `HOSPITAL_AI_CHAT_PROVIDER=ollama` to use local Ollama APIs.

## Development Auth

MVP auth uses bearer tokens mapped to seeded synthetic users:

| Token | User |
|---|---|
| `dev-doctor` | `doctor@example.test` |
| `dev-records` | `records@example.test` |
| `dev-security` | `security@example.test` |
| `dev-admin` | `admin@example.test` |

Production OIDC can replace the token resolver without changing route dependencies.

## Security Notes

- Use synthetic or de-identified data only.
- Patient permission is checked before retrieval and repeated inside the retrieval query.
- Denied patient, document, and chat accesses write `audit_logs`.
- The LLM prompt receives only numbered evidence blocks returned by permission-filtered retrieval.
