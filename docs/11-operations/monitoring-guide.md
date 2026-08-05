# Monitoring & Operations Guide

> Project: AI-Powered Hospital Knowledge Assistant  
> Project Code: HOSP-AI-001  
> Version: 3.1  
> Status: Draft  
> Owner: DevOps / SRE Lead  
> Last Updated: 2026-08-04

## 1. Application Metrics

Monitor query, retrieval, generation, citation, no-evidence, feedback, and authorization-denial metrics through the backend metrics endpoint and database-backed analytics. Provider dashboards remain the source for Gemini and DeepSeek quota and billing limits.

## 2. VPS Monitoring Profile

For the initial 4 GB VPS deployment, use native Linux and Docker telemetry until resource testing justifies a larger observability stack.

```bash
free -h
df -h
docker stats --no-stream
docker system df
docker compose -f infra/docker-compose.yml logs --tail=100 backend worker
docker compose -f infra/docker-compose.yml exec redis redis-cli INFO memory
```

## 3. Alerts and Thresholds

| What | How | Threshold | Action |
|---|---|---|---|
| API health | `curl <BASE_URL>/api/v1/health` | Non-200 for >60s | Inspect deployment and backend logs |
| Disk usage | `df -h` | <20% free | Identify the consumer; remove only confirmed disposable data |
| Memory | `free -h` | <512 MB available | Inspect container usage and worker workload |
| Docker disk | `docker system df` | Unexpected growth | Preserve rollback images; prune only confirmed unused images |
| `document-indexing` depth | `LLEN rq:queue:document-indexing` | >50 pending | Inspect worker and provider health |
| `cdss-analysis` depth | `LLEN rq:queue:cdss-analysis` | >50 pending | Inspect worker and provider health |
| Failed jobs | `FailedJobRegistry` for each active queue | >0 | Inspect failure reason before retry |
| Chat latency | Backend metrics/logs | P95 >10s | Check provider quota, network, and context size |
| Gemini quota | Provider dashboard | >80% of limit | Reduce concurrency or use an approved alternative |

## 4. Queue Commands

```bash
for queue in document-indexing cdss-analysis document-generation-build; do
  docker compose -f infra/docker-compose.yml exec -T redis \
    redis-cli LLEN "rq:queue:${queue}"
done

for queue in document-indexing cdss-analysis document-generation-build; do
  docker compose -f infra/docker-compose.yml exec -T worker \
    python -c "from redis import Redis; from rq.registry import FailedJobRegistry; r=Redis.from_url('redis://redis:6379/0'); print('${queue}', FailedJobRegistry('${queue}', connection=r).count)"
done
```

## Change Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-28 | PM / Tech Lead | Initial metrics framework |
| 2.0 | 2026-06-07 | Agent | Analytics schema and baseline update |
| 3.0 | 2026-08-04 | Agent | VPS monitoring and provider update |
| 3.1 | 2026-08-04 | Agent | Align queue and disk monitoring with runtime behavior |
