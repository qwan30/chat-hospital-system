# Operations Guide

> Project: HOSP-AI-001 · Version: 1.0 · Owner: DevOps Lead · Last Updated: 2026-06-14  

## 1. Service Architecture

| Service | Process | Port | Health Check |
|---------|---------|------|-------------|
| FastAPI BFF | uvicorn | 8000 | `GET /api/v1/health` |
| TanStack Start Frontend | bun run dev | 8082 | `GET /` |
| PostgreSQL | Docker/system | 5432 | Connection check |
| Redis | Docker/system | 6379 | `PING` |
| RQ Worker | run_worker.py | — | Queue depth |
| Ollama | System service | 11434 | `GET /api/tags` |

## 2. Starting Services

### Local Dev
```bash
# DB + Redis (or use SQLite for local dev — see .env)
docker compose up -d postgres redis

# Backend
cd app/backend
alembic upgrade head
python -m uvicorn hospital_ai.main:create_app --factory --reload --port 8000

# Worker (optional — inline mode runs jobs in-process)
cd app/backend
python -m hospital_ai.workers.run_worker

# Frontend
cd app/frontend
npm run dev
```

### Production
```bash
gunicorn hospital_ai.main:create_app -w 4 -k uvicorn.workers.UvicornWorker
rq worker high default low --url redis://localhost:6379/0
cd app/frontend && npm run build && npm run start
```

## 3. Health Checks

| Check | Command | Expected |
|-------|---------|----------|
| API | `curl localhost:8000/api/v1/health` | `{"status":"ok"}` |
| DB | `poetry run alembic current` | Shows revision |
| Redis | `redis-cli PING` | `PONG` |
| Ollama | `curl localhost:11434/api/tags` | JSON list |
| RQ | `rq info --url redis://localhost:6379/0` | Queue stats |

## 4. Monitoring Alerts

| What | How | Threshold |
|------|-----|-----------|
| API errors | Health check + logs | 5xx >2% in 5 min |
| Chat latency | Metrics P95 | >5 seconds |
| LLM latency | Ollama logs | >20 sec avg |
| OCR backlog | RQ queue depth | Jobs >30 min stale |
| RAG quality | `/feedback/metrics/summary` | No-evidence >30% |
| Disk | `df -h` | <20% free |
| Memory | `free -m` | <2GB available |

## 5. Backup

```bash
pg_dump -h localhost -U hospital_ai hospital_ai > backup_$(date +%Y%m%d).sql
tar -czf storage_backup_$(date +%Y%m%d).tar.gz .local_storage/
```

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Operations guide: services, start/stop, health, monitoring, backup |
