# Troubleshooting Guide

> Project: HOSP-AI-001 · Version: 2.0 · Owner: DevOps Lead · Last Updated: 2026-08-04  

## 1. Backend Issues

### API returns 500
1. Check logs for trace_id
2. Verify DB: `docker compose -f infra/docker-compose.yml exec backend alembic current`
3. Verify Redis: `redis-cli PING` (or via docker exec)
4. Verify LLM config: Check if `HOSPITAL_AI_CHAT_PROVIDER` is set and valid
5. Check disk: `df -h`

### Chat returns "no evidence" for everything
1. Check embedding provider is `gemini` (not `deterministic`)
2. Verify documents indexed: `SELECT status, count(*) FROM documents GROUP BY status`
3. Check evidence threshold not too high (>0.5)
4. Run RAG eval locally or via container.

### Migrations fail
1. `docker compose -f infra/docker-compose.yml exec backend alembic current` → check state
2. If stuck: `docker compose -f infra/docker-compose.yml exec backend alembic stamp <revision>`
3. Fresh start: drop DB → create → `alembic upgrade head` → `seed_dev.py` (via docker exec)

## 2. Frontend Issues

### CORS errors
1. Verify `HOSPITAL_AI_CORS_ORIGINS` includes frontend origin
2. Check frontend API base URL config

### No data in pages
1. Check browser console for API errors
2. Verify JWT present + valid
3. Check Network tab for 401/403
4. Verify user permissions: `SELECT * FROM patient_permissions WHERE user_id='<uuid>'`

## 3. Gemini / DeepSeek Troubleshooting

### Gemini not responding
- Check API key validity.
- Check quota dashboard.
- Check network connectivity to `generativelanguage.googleapis.com`.

### DeepSeek not responding
- Check API key.
- Check credit balance.
- Check network connectivity to `api.deepseek.com`.

### Too slow
1. Check provider status pages.
2. Reduce `retrieval_top_k` or `top_k` for smaller context.
3. Check for prompt-injection scanner warmup latency (if applicable).

## 3.5 Dokploy / Traefik Issues

### 502 Bad Gateway
- Backend container not healthy, check `docker compose ps`, restart backend.

### TLS certificate error
- Check Dokploy/Traefik cert renewal, Let's Encrypt rate limits.

### Route not found
- Verify Dokploy service routing `api.<domain> → backend:8000`.

## 3.6 R2 Storage Issues

### Upload fails
- Check R2 credentials, endpoint URL, bucket name, key rotation.

### Download fails
- Check object key, version, bucket policy.

### All R2 operations fail
- Check Cloudflare status, verify endpoint URL format.

## 3.7 Docker Resource Exhaustion

### Container OOMKilled
- Check `docker inspect <container>` for OOM events, increase `mem_limit` or optimize memory footprint.

### Disk full
- `docker system df`
- `docker system prune`
- Check pg_dump retention (old backups).

### Image pull fails
- Check GHCR auth, disk space, network connectivity.

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
curl https://<PLACEHOLDER_DOMAIN>/api/v1/health   # API
curl -I https://generativelanguage.googleapis.com # Gemini connectivity
docker compose -f infra/docker-compose.yml exec redis redis-cli PING # Redis
docker compose -f infra/docker-compose.yml exec backend alembic current # Database
docker compose -f infra/docker-compose.yml exec worker rq info --url redis://redis:6379/0 # Queue
df -h                                             # System Disk
docker system df                                  # Docker Disk
free -m                                           # Memory
docker stats --no-stream                          # Container Stats
```

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Troubleshooting: backend, frontend, LLM, DB, worker, diagnostics |
| 2.0 | 2026-08-04 | Agent | Replaced poetry with docker compose, replaced Ollama with Gemini/DeepSeek, added Dokploy, R2, and Docker exhaustion sections |
