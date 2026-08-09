# Troubleshooting Guide

> Project: HOSP-AI-001 · Version: 2.1 · Owner: DevOps Lead · Last Updated: 2026-08-04

## 1. Backend Issues

### API returns 500

1. Inspect backend logs and trace ID.
2. Check database revision with `docker compose -f infra/docker-compose.yml exec backend alembic current`.
3. Check Redis with `docker compose -f infra/docker-compose.yml exec redis redis-cli PING`.
4. Validate `HOSPITAL_AI_CHAT_PROVIDER` and provider credentials.
5. Check disk and memory pressure.

### Chat returns no evidence

1. Verify the embedding provider and API key.
2. Confirm documents reached the indexed state.
3. Inspect `document-indexing` queue depth and failures.
4. Check retrieval threshold and run the deterministic RAG evaluation.

## 2. Dokploy and Traefik

### 502 Bad Gateway

Check container health, backend logs, route target, and port `8000`. Confirm the deployed image matches the release record digest.

### TLS or route failure

Inspect Traefik certificate renewal, DNS, route mapping, and Let's Encrypt limits.

## 3. Gemini and DeepSeek

Check provider status, API key validity, quota/balance, and outbound network connectivity. Reduce concurrency or context size only after identifying provider throttling or latency as the cause.

## 4. R2 Storage

### Upload or download failure

Check endpoint, bucket, credentials, object key, network connectivity, and provider status. When the R2 backend is selected, there is **no automatic local-document failover**. Do not assume `storage-data` contains a complete recoverable copy.

For confirmed loss or corruption, restore from the independently maintained off-host backup into a separate bucket or prefix, validate checksums, and then perform the approved recovery cutover.

## 5. HMS JWKS Authentication

When authentication fails, check HMS IdP status, DNS, TLS, issuer, audience, algorithm configuration, and the JWKS endpoint. The service fails closed when validation cannot be completed. Restore the configured RS256/JWKS path; do not change signing algorithms during an outage.

## 6. RQ Worker

The worker consumes `document-indexing`, `cdss-analysis`, and `document-generation-build`.

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

If jobs are stuck, inspect worker logs, job payloads, provider errors, and Redis connectivity before retrying or restarting.

## 7. Resource Exhaustion

```bash
df -h
free -h
docker stats --no-stream
docker system df
```

Identify the actual consumer. Preserve current and rollback image digests. Remove only expired backups, disposable logs, stopped containers, or confirmed unused images after review.

## 8. Quick Diagnostics

```bash
curl --fail --show-error --connect-timeout 10 --max-time 20 https://<PLACEHOLDER_DOMAIN>/api/v1/health
docker compose -f infra/docker-compose.yml exec redis redis-cli PING
docker compose -f infra/docker-compose.yml exec backend alembic current
docker compose -f infra/docker-compose.yml logs --tail=100 backend worker
df -h
free -h
docker stats --no-stream
docker system df
```

## Change Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-06-14 | Agent | Initial troubleshooting guide |
| 2.0 | 2026-08-04 | Agent | Dokploy/R2/provider update |
| 2.1 | 2026-08-04 | Agent | Correct queue, R2, JWKS, and disk procedures |
