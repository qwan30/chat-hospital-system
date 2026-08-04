# Operations Guide

> Project: AI-Powered Hospital Knowledge Assistant
> Target: 4 GB RAM / 45 GB disk VPS staging/demo
> Version: 2.1
> Status: Dokploy/VPS operations runbook
> Owner: DevOps / SRE Lead
> Last Updated: 2026-08-04

## 1. PostgreSQL Backup and Restore

The repository provides operator commands, not a scheduler. Configure an approved external cron, systemd timer, or platform scheduler to run encrypted backups and enforce retention.

**Retention target:** 14 daily, 8 weekly, and 12 monthly encrypted copies.

```bash
set -euo pipefail
umask 077
TEMP_DUMP="<protected-temporary-path>/<BACKUP_ID>.dump"
trap 'rm -f "$TEMP_DUMP"' EXIT

docker compose -f "<absolute-path-to-infra/docker-compose.yml>" exec -T postgres \
  pg_dump --format=custom --no-owner --no-acl \
  --username="<POSTGRES_USER>" --dbname="<POSTGRES_DB>" > "$TEMP_DUMP"

age --encrypt --recipient "<BACKUP_ENCRYPTION_RECIPIENT>" \
  --output "<protected-off-host-destination>/<BACKUP_ID>.dump.age" "$TEMP_DUMP"
```

The trap removes the plaintext temporary dump whether encryption succeeds or fails. Verify checksum, decryption, schema integrity, and representative reads through a monthly restore into an isolated database.

## 2. R2 Backup and Recovery

R2 is the authoritative document store when `HOSPITAL_AI_STORAGE_BACKEND=r2`. The application does not maintain a complete local document copy and provides **no automatic local-document failover** during an R2 outage.

Use a scheduled, separately credentialed backup process to copy R2 objects to an independent approved bucket or backup destination. Backup keys must be timestamped or otherwise immutable so later writes do not overwrite prior recovery points. Test a monthly restore into a separate bucket or prefix and verify object checksums plus application readability.

Do not rely on undocumented provider-side version-history behavior as the only deletion recovery control. Rotate R2 credentials after suspected exposure or personnel changes, updating backend and worker together.

## 3. Dokploy Volume Boundaries

- `postgres-data` contains live PostgreSQL state; logical `pg_dump` backups are the primary database recovery artifact.
- `storage-data` contains temporary/cache state used by containers. It is not a substitute for R2 backup and cannot guarantee document availability during R2 outages.

A named-volume export may support forensic or secondary recovery work, but it does not replace database dumps or off-host object backups.

## 4. Worker Queue Monitoring

The worker consumes exactly `document-indexing` and `cdss-analysis`.

```bash
# Queue depth
for queue in document-indexing cdss-analysis; do
  docker compose -f "<absolute-path-to-infra/docker-compose.yml>" exec -T redis \
    redis-cli LLEN "rq:queue:${queue}"
done

# Failed jobs by queue registry
for queue in document-indexing cdss-analysis; do
  docker compose -f "<absolute-path-to-infra/docker-compose.yml>" exec -T worker \
    python -c "from redis import Redis; from rq.registry import FailedJobRegistry; r=Redis.from_url('redis://redis:6379/0'); print('${queue}', FailedJobRegistry('${queue}', connection=r).count)"
done
```

Treat jobs queued or running for more than 30 minutes as stale. Inspect worker logs and job metadata before retrying. Restarting the worker does not repair invalid payloads or provider failures.

## 5. VPS Resource Monitoring

```bash
free -h
df -h "<VPS_DATA_MOUNT>"
docker stats --no-stream
docker system df
```

Alert when disk free space is below 20%, available memory below 512 MB, or swap usage exceeds 50%. For disk pressure, inspect which images, containers, logs, or backups consume space. Prefer targeted removal such as unused image pruning after confirming no rollback candidate depends on those images; do not run blanket destructive pruning as a default incident action.

## 6. LLM Quota and Emergency Disable

Gemini is primary; DeepSeek is an explicit configured alternative. Monitor provider quotas and costs. To stop external LLM calls during a quota, credential, or cost incident, set `HOSPITAL_AI_CHAT_PROVIDER=stub` in Dokploy and restart backend plus worker. Restore an approved provider only after validation.

## 7. Rollback and Migrations

Rollback targets an immutable image identity. Database migrations follow a forward-compatible expand/contract policy. Roll back only the application image when schema compatibility is preserved. A destructive migration requires a separately approved database restore procedure.

## 8. R2 and HMS JWKS Outages

### R2 outage

- New uploads and reads that require R2 fail.
- Preserve queued work and avoid repeated destructive retries.
- Monitor provider status and application error rates.
- Resume or retry affected operations after R2 recovers.
- Restore from the independent backup only for verified loss or corruption, not ordinary transient unavailability.

### HMS JWKS outage

JWT validation fails closed when a required key cannot be obtained or validated. Check HMS IdP health, DNS, routing, TLS, and the configured JWKS endpoint. Preserve current service while cached keys remain valid, then restore the same RS256/JWKS trust path. Do not switch signing algorithms or introduce an HMAC secret as an emergency shortcut.

## Change Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-06-14 | Agent | Initial operations guide |
| 2.0 | 2026-08-04 | Agent | VPS/Dokploy rewrite |
| 2.1 | 2026-08-04 | Agent | Fail-closed backups, queue monitoring, R2, JWKS, and disk procedures |
