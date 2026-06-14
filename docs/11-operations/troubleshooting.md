# Troubleshooting Guide

> Project: HOSP-AI-001 · Version: 1.0 · Owner: DevOps Lead · Last Updated: 2026-06-14  

## 1. Backend Issues

### API returns 500
1. Check logs for trace_id
2. Verify DB: `poetry run alembic current`
3. Verify Redis: `redis-cli PING`
4. Verify Ollama: `curl localhost:11434/api/tags`
5. Check disk: `df -h`

### Chat returns "no evidence" for everything
1. Check embedding provider is `ollama` (not `deterministic`)
2. Verify documents indexed: `SELECT status, count(*) FROM documents GROUP BY status`
3. Check evidence threshold not too high (>0.5)
4. Run RAG eval: `poetry run python scripts/run_rag_eval.py`

### Migrations fail
1. `poetry run alembic current` → check state
2. If stuck: `poetry run alembic stamp <revision>`
3. Fresh start: drop DB → create → `alembic upgrade head` → `seed_dev.py`

## 2. Frontend Issues

### CORS errors
1. Verify `HOSPITAL_AI_CORS_ORIGINS` includes frontend origin
2. Check frontend API base URL config

### No data in pages
1. Check browser console for API errors
2. Verify JWT present + valid
3. Check Network tab for 401/403
4. Verify user permissions: `SELECT * FROM patient_permissions WHERE user_id='<uuid>'`

## 3. LLM / Ollama

### Ollama not responding
```bash
curl http://localhost:11434/api/tags  # Check
systemctl restart ollama              # Restart
ollama list                           # Models
```

### Too slow / OOM
1. Use smaller model: `HOSPITAL_AI_CHAT_MODEL=qwen2.5:3b`
2. Limit concurrency
3. `ollama ps` → check resource usage

## 4. Database

### Connection pool exhausted
1. `SELECT count(*) FROM pg_stat_activity`
2. Increase pool size in DB URL
3. Check for connection leaks

### pgvector not working
1. `SELECT * FROM pg_extension WHERE extname='vector'`
2. `SELECT * FROM pg_indexes WHERE tablename='document_chunks'`
3. `REINDEX INDEX <index_name>`

## 5. RQ Worker

### Jobs stuck
```bash
rq info --url redis://localhost:6379/0          # Status
rq info --url redis://localhost:6379/0 --failed # Failed jobs
```

### Worker not processing
1. `ps aux | grep run_worker`
2. Check Redis: `redis-cli PING`
3. Check worker logs
4. Kill + restart worker process

## 6. Quick Diagnostics

```bash
curl localhost:8000/api/v1/health         # API
curl localhost:11434/api/tags              # Ollama
redis-cli PING                             # Redis
poetry run alembic current                 # Database
rq info --url redis://localhost:6379/0    # Queue
df -h                                      # Disk
free -m                                    # Memory
```

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Troubleshooting: backend, frontend, LLM, DB, worker, diagnostics |
