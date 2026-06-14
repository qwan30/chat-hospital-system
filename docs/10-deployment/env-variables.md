# Environment Variables

> Project: HOSP-AI-001 · Version: 1.0 · Last Updated: 2026-06-14  
> All prefixed `HOSPITAL_AI_` · Source: `app/backend/src/hospital_ai/core/config.py`

## 1. Core

| Variable | Default | Required |
|----------|---------|----------|
| `HOSPITAL_AI_ENVIRONMENT` | `local` | Yes |
| `HOSPITAL_AI_API_V1_PREFIX` | `/api/v1` | No |
| `HOSPITAL_AI_DATABASE_URL` | `postgresql+asyncpg://...` | Yes |
| `HOSPITAL_AI_REDIS_URL` | `redis://localhost:6379/0` | No |
| `HOSPITAL_AI_STORAGE_ROOT` | `.local_storage` | No |
| `HOSPITAL_AI_WORKER_INLINE` | `false` | No |
| `HOSPITAL_AI_CORS_ORIGINS` | `http://localhost:3000,...` | Yes |

## 2. LLM & Embedding

| Variable | Default | Notes |
|----------|---------|-------|
| `HOSPITAL_AI_CHAT_PROVIDER` | `stub` | stub/ollama/openai |
| `HOSPITAL_AI_EMBEDDING_PROVIDER` | `deterministic` | deterministic/ollama/openai |
| `HOSPITAL_AI_OLLAMA_BASE_URL` | `http://localhost:11434` | |
| `HOSPITAL_AI_EMBEDDING_MODEL` | `bge-m3` | |
| `HOSPITAL_AI_CHAT_MODEL` | `qwen2.5:7b` | |
| `HOSPITAL_AI_EMBEDDING_DIMENSIONS` | `1024` | |
| `HOSPITAL_AI_OPENAI_API_KEY` | (empty) | Required if provider=openai |
| `HOSPITAL_AI_OPENAI_BASE_URL` | `https://api.openai.com/v1` | |
| `HOSPITAL_AI_OPENAI_CHAT_MODEL` | `gpt-4o-mini` | |
| `HOSPITAL_AI_OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | |

## 3. RAG Tuning

| Variable | Default | Range |
|----------|---------|-------|
| `HOSPITAL_AI_RETRIEVAL_TOP_K` | `5` | |
| `HOSPITAL_AI_EVIDENCE_THRESHOLD` | `0.2` | |
| `HOSPITAL_AI_CHUNK_SIZE` | `512` | 64–4096 |
| `HOSPITAL_AI_CHUNK_OVERLAP` | `64` | 0–512 |
| `HOSPITAL_AI_STREAMING_ENABLED` | `true` | |
| `HOSPITAL_AI_SYSTEM_PROMPT` | (see config.py) | |

## 4. Reranker

| Variable | Default |
|----------|---------|
| `HOSPITAL_AI_RERANKER_PROVIDER` | `keyword` |
| `HOSPITAL_AI_RERANKER_MODEL` | `BAAI/bge-reranker-v2-m3` |
| `HOSPITAL_AI_RERANKER_TOP_K` | `5` |
| `HOSPITAL_AI_RERANKER_TEI_URL` | (empty) |
| `HOSPITAL_AI_COHERE_API_KEY` | (empty) |

## 5. Hybrid Search

| Variable | Default |
|----------|---------|
| `HOSPITAL_AI_RETRIEVAL_MODE` | `vector` |
| `HOSPITAL_AI_BM25_WEIGHT` | `0.4` |
| `HOSPITAL_AI_VECTOR_WEIGHT` | `0.6` |

## 6. HMS Integration

| Variable | Default |
|----------|---------|
| `HOSPITAL_AI_HMS_BASE_URL` | `http://localhost:8080/api/v1` |
| `HOSPITAL_AI_HMS_API_KEY` | (empty) |
| `HOSPITAL_AI_HMS_SYNC_ENABLED` | `false` |
| `HOSPITAL_AI_HMS_SYNC_TIMEOUT_SECONDS` | `30` |

## 7. JWT Auth

| Variable | Default | Notes |
|----------|---------|-------|
| `HOSPITAL_AI_JWT_ISSUER` | (empty) | Empty = use static tokens |
| `HOSPITAL_AI_JWT_AUDIENCE` | (empty) | |
| `HOSPITAL_AI_JWKS_URL` | (empty) | For RS256 |
| `HOSPITAL_AI_JWT_HMAC_SECRET` | (empty) | For HS256 |
| `HOSPITAL_AI_JWT_ALGORITHM` | `RS256` | |

## 8. Limits

| Variable | Default |
|----------|---------|
| `HOSPITAL_AI_MAX_UPLOAD_BYTES` | `10485760` (10MB) |
| `HOSPITAL_AI_DEV_BEARER_TOKENS` | (see config.py) |

## 9. .env Template

```bash
HOSPITAL_AI_ENVIRONMENT=local
HOSPITAL_AI_DATABASE_URL=postgresql+asyncpg://hospital_ai:hospital_ai@localhost:5432/hospital_ai
HOSPITAL_AI_CHAT_PROVIDER=ollama
HOSPITAL_AI_EMBEDDING_PROVIDER=ollama
HOSPITAL_AI_OLLAMA_BASE_URL=http://localhost:11434
HOSPITAL_AI_CHAT_MODEL=qwen2.5:7b
HOSPITAL_AI_RETRIEVAL_MODE=vector
HOSPITAL_AI_STREAMING_ENABLED=true
HOSPITAL_AI_CORS_ORIGINS=http://localhost:3000
```

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Complete reference: 30+ settings from core/config.py |
