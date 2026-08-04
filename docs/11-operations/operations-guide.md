# Operations Guide

> Project: AI-Powered Hospital Knowledge Assistant
> Target: 4 GB RAM / 45 GB disk VPS staging/demo
> Version: 2.0
> Status: Dokploy/VPS operations runbook
> Owner: DevOps / SRE Lead
> Last Updated: 2026-08-04

## 1. PostgreSQL Backup Schedule and Restore Test

PostgreSQL backups are taken daily using automated `pg_dump` via `docker compose exec` to the postgres container, encrypted with `age`, and copied off-host to an approved backup destination.

**Retention Policy:**
- 14 daily copies
- 8 weekly copies
- 12 monthly copies

**Backup Command:**
```bash
# OPERATOR-RUN: substitute approved values; do not put secrets in this file.
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" exec -T postgres \
  pg_dump --format=custom --no-owner --no-acl \
  --username="<POSTGRES_USER>" --dbname="<POSTGRES_DB>" > "<protected-temporary-path>/<BACKUP_ID>.dump"

# OPERATOR-RUN: obtain the recipient from the approved secret/key store.
age --encrypt --recipient "<BACKUP_ENCRYPTION_RECIPIENT>" \
  --output "<protected-backup-destination>/<BACKUP_ID>.dump.age" "<protected-temporary-path>/<BACKUP_ID>.dump"
```

**Restore Test:**
Perform a monthly restore test into an isolated database. Verify the checksum, decryption, schema integrity, and readability of the data using the verification checklist.

## 2. Cloudflare R2 Versioning and Lifecycle Policy

R2 is the authoritative, durable document store for this profile.
- **Object Versioning:** Enable bucket versioning to recover from accidental deletions.
- **Lifecycle Rules:** Retain non-current object versions for 90 days (for the demo profile), and configure automated cleanup of delete markers.
- **Restore Testing:** Conduct a monthly synthetic data restore check.
- **Key Rotation:** R2 access keys must be rotated immediately upon personnel change or suspected exposure. Update backend and worker secrets simultaneously.

## 3. Dokploy Volume Backup Behavior

VPS storage volumes are local caches and temporary state only. 
- `postgres-data` named volume holds the PostgreSQL database state.
- `storage-data` named volume holds the local document cache and temporary uploads. R2 is the authoritative source for documents.

Volume backups are secondary to the primary `pg_dump` process for the database. To back up a named volume:
```bash
# OPERATOR-RUN: backup Dokploy volume using alpine tar
docker run --rm --volumes-from "<CONTAINER_NAME>" \
  -v "<BACKUP_DESTINATION>:/backup" alpine \
  tar czf "/backup/volume_<VOLUME_NAME>.tar.gz" "<MOUNT_PATH>"
```

## 4. Worker Queue Monitoring

The background worker manages OCR and embedding jobs. Monitor queue depths and failed jobs via Redis.

```bash
# OPERATOR-RUN: check default queue depth
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" exec redis redis-cli LLEN rq:queue:default

# OPERATOR-RUN: check failed queue depth
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" exec redis redis-cli LLEN rq:queue:failed
```

**Thresholds and Actions:**
- A job is considered stale if it has been running or queued for > 30 minutes.
- Inspect logs via Dokploy UI or container logs.
- Restart worker if necessary:
```bash
# OPERATOR-RUN: restart worker container
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" restart worker
```

## 5. VPS Resource Monitoring (4 GB RAM Baseline)

Grafana, Loki, and Tempo are deferred for the first deployment due to the strict 4 GB RAM resource constraints of the VPS. Monitoring is performed manually via standard Linux and Docker utilities.

**Alert Thresholds:**
- Disk: < 20% free
- Memory: < 512MB available
- Docker System: > 30GB reclaimable space
- Swap: > 50% usage

**Monitoring Commands:**
```bash
# OPERATOR-RUN: check memory availability
free -h

# OPERATOR-RUN: check disk space
df -h "<VPS_DATA_MOUNT>"

# OPERATOR-RUN: check live container resource usage
docker stats --no-stream

# OPERATOR-RUN: check Docker disk usage
docker system df
```

## 6. LLM Quota and Cost Limits

Gemini is the default LLM provider. DeepSeek is an explicit fallback.
- **Gemini:** Subject to per-minute (RPM) and per-day (RPD) quotas. Monitor via the Google AI Studio dashboard.
- **DeepSeek:** Uses a prepaid credit balance. 

**Monitoring & Configuration:**
- Set budget and consumption alerts in provider dashboards.
- Track usage and cost estimations locally by querying the `audit_events` table for token usage logs.
- Controlled via environment variable: `HOSPITAL_AI_CHAT_PROVIDER` (values: `gemini`, `deepseek`, or `stub`).

## 7. API Rate Limiting

The backend uses `slowapi` to enforce rate limits per endpoint. Monitor backend logs for HTTP `429 Too Many Requests` responses.

| Endpoint | Limit |
|----------|-------|
| Login | 10/min |
| Chat | 10/min |
| Streaming | 5/min |
| Search | 20/min |
| Access Requests | 3/min |
| Global (Fallback) | 60/min |

## 8. Rollback to Previous Image Digest

Rollbacks must target an immutable image digest. Refer to `rollback-plan.md` for full context.

**5-Step Operator Sequence:**
1. Freeze promotion and note the incident timeline.
2. Confirm the target is staging/demo and obtain the exact immutable image digest (`sha256:<digest>`).
3. Verify the database pre-deployment backup is encrypted and available.
4. Confirm database schema compatibility (see Section 9).
5. Invoke the Dokploy rollback webhook with `<IMMUTABLE_BACKEND_IMAGE>` and `<ENVIRONMENT>`, or apply the change manually via the Dokploy UI.

## 9. Rollback Behavior After Migration

Database migrations enforce a **forward-only** policy. 
- **Expand/Contract Compatibility:** Ensure schema changes are additive before deploying dependent code.
- **When to Rollback Image:** If an application fails but the migration was additive and compatible, roll back the image only (forward fix).
- **When to Restore DB:** If a destructive migration was applied and the application failed, a database restore is required. This is a separate incident recovery procedure, not a standard rollback.

## 10. Emergency Disable Switch for External LLM Calls

If provider quotas are exhausted, credentials leak, or API costs spike, switch the application to the internal stub mode to return canned responses without hitting external APIs.

**Procedure:**
```bash
# OPERATOR-RUN: update environment in Dokploy or via env file
# Set HOSPITAL_AI_CHAT_PROVIDER=stub

# OPERATOR-RUN: restart backend and worker to apply
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" restart backend worker
```
To reverse, restore the value to `gemini` (or `deepseek`) and restart the services again.

## 11. R2 and HMS JWKS Outage Procedures

**R2 Outage:**
- Document uploads and fetching of new documents will fail.
- Existing cached documents may still serve successfully from the `storage-data` volume.
- There is no automatic failover for R2. Monitor the Cloudflare status page.

**HMS JWKS Outage:**
- JWT validation relies on cached JWKS keys (governed by the PyJWKClient default TTL).
- If the HMS IdP goes down and the cache expires, authentication will **fail closed**, blocking user access.
- **Operator Action:** Decide whether to manually extend the cache or switch the application to an HMAC fallback secret if authorized.

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Operations guide: services, start/stop, health, monitoring, backup |
| 2.0 | 2026-08-04 | Agent | Rewrite operations guide for VPS staging-demo profile (Dokploy/Vercel/R2/Gemini) |
