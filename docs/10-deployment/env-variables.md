# Environment Variables

> Project: HOSP-AI-001 · Version: 1.1 · Last Updated: 2026-08-03
> All prefixed `HOSPITAL_AI_` · Source: `app/backend/src/hospital_ai/core/config.py`

The deployment profile in this document is split between a local developer
profile and the Dokploy/VPS staging profile. The frontend is deployed on
Vercel and calls the backend through `VITE_API_URL`. Supabase is not part of
this project's deployment contract. The VPS does not run Ollama.

## 1. Core

| Variable                           | Default                     | Required                              |
| ---------------------------------- | --------------------------- | ------------------------------------- |
| `HOSPITAL_AI_ENVIRONMENT`          | `local`                     | Yes                                   |
| `HOSPITAL_AI_API_V1_PREFIX`        | `/api/v1`                   | No                                    |
| `HOSPITAL_AI_DATABASE_URL`         | `postgresql+asyncpg://...`  | Yes                                   |
| `HOSPITAL_AI_REDIS_URL`            | `redis://localhost:6379/0`  | No                                    |
| `HOSPITAL_AI_STORAGE_ROOT`         | `.local_storage`            | No                                    |
| `HOSPITAL_AI_STORAGE_BACKEND`      | `local`                     | `r2` for Dokploy/VPS                  |
| `HOSPITAL_AI_R2_ENDPOINT`          | (empty)                     | Required when storage backend is `r2` |
| `HOSPITAL_AI_R2_BUCKET`            | (empty)                     | Required when storage backend is `r2` |
| `HOSPITAL_AI_R2_REGION`            | `auto`                      | Cloudflare R2 uses `auto`             |
| `HOSPITAL_AI_R2_ACCESS_KEY_ID`     | (empty)                     | Backend/worker secret only            |
| `HOSPITAL_AI_R2_SECRET_ACCESS_KEY` | (empty)                     | Backend/worker secret only            |
| `HOSPITAL_AI_WORKER_INLINE`        | `false`                     | No                                    |
| `HOSPITAL_AI_CORS_ORIGINS`         | `http://localhost:8082,...` | Yes                                   |

## 2. LLM & Embedding

| Variable                             | Default                     | Notes                                                 |
| ------------------------------------ | --------------------------- | ----------------------------------------------------- |
| `HOSPITAL_AI_CHAT_PROVIDER`          | `stub`                      | stub/ollama/openai/gemini; VPS default is `gemini`    |
| `HOSPITAL_AI_EMBEDDING_PROVIDER`     | `deterministic`             | deterministic/ollama/gemini; VPS default is `gemini`  |
| `HOSPITAL_AI_OLLAMA_BASE_URL`        | `http://localhost:11434`    |                                                       |
| `HOSPITAL_AI_EMBEDDING_MODEL`        | `bge-m3`                    |                                                       |
| `HOSPITAL_AI_CHAT_MODEL`             | `qwen2.5:7b`                |                                                       |
| `HOSPITAL_AI_EMBEDDING_DIMENSIONS`   | `1024`                      |                                                       |
| `HOSPITAL_AI_OPENAI_API_KEY`         | (empty)                     | Required if provider=openai                           |
| `HOSPITAL_AI_OPENAI_BASE_URL`        | `https://api.openai.com/v1` | Dokploy DeepSeek value: `https://api.deepseek.com/v1` |
| `HOSPITAL_AI_OPENAI_CHAT_MODEL`      | `gpt-4o-mini`               | Dokploy DeepSeek value: `deepseek-chat`               |
| `HOSPITAL_AI_OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small`    |                                                       |
| `HOSPITAL_AI_GEMINI_API_KEY`         | (empty)                     | Required for VPS chat/embedding                       |
| `HOSPITAL_AI_GEMINI_CHAT_MODEL`      | `gemini-2.0-flash`          | VPS chat model                                        |

The VPS Compose file sets Gemini as the default provider and carries the
OpenAI-compatible DeepSeek settings to the backend/worker. This is a frozen
configuration contract, not automatic failover: switching to DeepSeek must be
an explicit provider configuration change and must be tested before rollout.

## 3. RAG Tuning

| Variable                         | Default         | Range   |
| -------------------------------- | --------------- | ------- |
| `HOSPITAL_AI_RETRIEVAL_TOP_K`    | `5`             |         |
| `HOSPITAL_AI_EVIDENCE_THRESHOLD` | `0.2`           |         |
| `HOSPITAL_AI_CHUNK_SIZE`         | `512`           | 64–4096 |
| `HOSPITAL_AI_CHUNK_OVERLAP`      | `64`            | 0–512   |
| `HOSPITAL_AI_STREAMING_ENABLED`  | `true`          |         |
| `HOSPITAL_AI_SYSTEM_PROMPT`      | (see config.py) |         |

## 4. Reranker

| Variable                        | Default                   |
| ------------------------------- | ------------------------- |
| `HOSPITAL_AI_RERANKER_PROVIDER` | `keyword`                 |
| `HOSPITAL_AI_RERANKER_MODEL`    | `BAAI/bge-reranker-v2-m3` |
| `HOSPITAL_AI_RERANKER_TOP_K`    | `5`                       |
| `HOSPITAL_AI_RERANKER_TEI_URL`  | (empty)                   |
| `HOSPITAL_AI_COHERE_API_KEY`    | (empty)                   |

## 5. Hybrid Search

| Variable                     | Default  |
| ---------------------------- | -------- |
| `HOSPITAL_AI_RETRIEVAL_MODE` | `vector` |
| `HOSPITAL_AI_BM25_WEIGHT`    | `0.4`    |
| `HOSPITAL_AI_VECTOR_WEIGHT`  | `0.6`    |

## 6. HMS Integration

| Variable                               | Default                        |
| -------------------------------------- | ------------------------------ |
| `HOSPITAL_AI_HMS_BASE_URL`             | `http://localhost:8080/api/v1` |
| `HOSPITAL_AI_HMS_API_KEY`              | (empty)                        |
| `HOSPITAL_AI_HMS_SYNC_ENABLED`         | `false`                        |
| `HOSPITAL_AI_HMS_SYNC_TIMEOUT_SECONDS` | `30`                           |

## 7. JWT Auth

| Variable                      | Default | Notes                     |
| ----------------------------- | ------- | ------------------------- |
| `HOSPITAL_AI_JWT_ISSUER`      | (empty) | Empty = use static tokens |
| `HOSPITAL_AI_JWT_AUDIENCE`    | (empty) |                           |
| `HOSPITAL_AI_JWKS_URL`        | (empty) | For RS256                 |
| `HOSPITAL_AI_JWT_HMAC_SECRET` | (empty) | For HS256                 |
| `HOSPITAL_AI_JWT_ALGORITHM`   | `RS256` |                           |

## 8. Limits

| Variable                        | Default           |
| ------------------------------- | ----------------- |
| `HOSPITAL_AI_MAX_UPLOAD_BYTES`  | `10485760` (10MB) |
| `HOSPITAL_AI_DEV_BEARER_TOKENS` | (see config.py)   |

For non-local deployments, set `HOSPITAL_AI_JWT_ISSUER`,
`HOSPITAL_AI_JWKS_URL`, `HOSPITAL_AI_JWT_AUDIENCE`, and
`HOSPITAL_AI_JWT_ALGORITHM=RS256`. Do not rely on the local static-token
fallback for a staging or production deployment.

## 9. Vercel and Dokploy profiles

Local development:

```bash
VITE_API_URL=
```

Browser API path:

```bash
/api
```

Vite rewrites that local path to `/api/v1` in development.

Backend CORS origin for local frontend:

```bash
HOSPITAL_AI_CORS_ORIGINS=http://localhost:8082
```

Vercel preview:

```bash
VITE_API_URL=https://api-preview.example.com/api/v1
```

Browser API path:

```bash
https://api-preview.example.com/api/v1
```

Backend CORS origin for this preview frontend:

```bash
HOSPITAL_AI_CORS_ORIGINS=https://preview-app.example.com
```

Vercel production:

```bash
VITE_API_URL=https://api.example.com/api/v1
```

Browser API path:

```bash
https://api.example.com/api/v1
```

Backend CORS origin for production frontend:

```bash
HOSPITAL_AI_CORS_ORIGINS=https://app.example.com
```

Dokploy backend/worker minimum profile (inject values through Dokploy
secrets/environment settings):

```bash
HOSPITAL_AI_ENVIRONMENT=staging
HOSPITAL_AI_CHAT_PROVIDER=gemini
HOSPITAL_AI_EMBEDDING_PROVIDER=gemini
HOSPITAL_AI_STORAGE_BACKEND=r2
HOSPITAL_AI_WORKER_INLINE=false
HOSPITAL_AI_CORS_ORIGINS=http://localhost:8082,https://preview-app.example.com,https://app.example.com
HOSPITAL_AI_HMS_SYNC_ENABLED=false
HOSPITAL_AI_JWT_ALGORITHM=RS256
```

`HOSPITAL_AI_GEMINI_API_KEY`, DeepSeek/OpenAI-compatible credentials, R2 credentials, and
HMS JWT values are backend-only. They must never be placed in Vercel client
variables or committed to the repository.

Preview domains must be explicitly approved and added to the backend CORS
allowlist before the frontend points at them.

## 10. .env Template

```bash
HOSPITAL_AI_ENVIRONMENT=local
HOSPITAL_AI_DATABASE_URL=postgresql+asyncpg://hospital_ai:hospital_ai@localhost:5432/hospital_ai
HOSPITAL_AI_CHAT_PROVIDER=ollama
HOSPITAL_AI_EMBEDDING_PROVIDER=ollama
HOSPITAL_AI_OLLAMA_BASE_URL=http://localhost:11434
HOSPITAL_AI_CHAT_MODEL=qwen2.5:7b
HOSPITAL_AI_RETRIEVAL_MODE=vector
HOSPITAL_AI_STREAMING_ENABLED=true
HOSPITAL_AI_CORS_ORIGINS=http://localhost:8082
```

## Change Log

| Version | Date       | Author | Change                                               |
| ------- | ---------- | ------ | ---------------------------------------------------- |
| 1.0     | 2026-06-14 | Agent  | Complete reference: 30+ settings from core/config.py |
