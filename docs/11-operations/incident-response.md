# Incident Response

> Project: HOSP-AI-001 · Version: 2.0 · Owner: DevOps Lead · Last Updated: 2026-08-04  

## 1. Severity Levels

| Level | Definition | Response | Example |
|-------|-----------|----------|---------|
| P1 — Critical | System unavailable or PHI breach | Immediate | API down, DB corrupted, unauthorized access |
| P2 — High | Core feature broken | <1 hour | Chat errors, upload failing |
| P3 — Medium | Feature degraded | <4 hours | Slow responses, non-critical endpoint down |
| P4 — Low | Minor / cosmetic | Next business day | UI glitch |

## 2. Process

```
DETECT → TRIAGE (P1-P4) → INVESTIGATE → MITIGATE → RESOLVE → POST-MORTEM
```

## 3. P1: System Down

### Immediate Actions
1. Check recent deployments
2. Check DB: `alembic current` + connectivity
3. Check Redis: `redis-cli PING`
4. Check disk: `df -h`
5. Check process list

### Mitigation
1. **Rollback** if deployment-caused
2. **Restart**: DB → Redis → API → Workers → Frontend
3. **Scale**: add workers, increase pool
4. **Failover** to standby if available

## 4. P1: PHI / Security Incident

### Immediate Actions
1. **Isolate**: Revoke tokens, block suspicious IPs
2. **Preserve**: Export audit_logs, don't delete
3. **Notify**: Security Lead → Product Owner → Hospital IT

### Containment
1. Rotate all secrets / API keys
2. Review CORS, rate limiting
3. Verify permission enforcement

## 5. P2: Chat / RAG Degraded

### Actions
1. Check Gemini API health / quota dashboard.
2. Check embedding service.
3. Check RQ queue depth.
4. Set `HOSPITAL_AI_CHAT_PROVIDER=stub` in Dokploy, restart backend and worker.
5. Reduce retrieval_top_k.

## 5.5 P2 — Gemini/DeepSeek Quota Exhaustion
- **Immediate**: Check quota dashboard, switch to DeepSeek if Gemini exhausted, or set `stub` provider.
- **Recovery**: Wait for quota reset, request limit increase, or use DeepSeek as temporary primary.

## 5.6 P2 — R2 Storage Outage
- **Immediate**: Document uploads fail, check R2 status page.
- **Mitigation**: Existing cached documents in `storage-data` volume may still serve for retrieval.
- **Recovery**: Monitor R2 status, re-upload failed documents after recovery.

## 5.7 P2 — HMS JWKS Outage
- **Immediate**: JWT validation fails if cached keys expire.
- **Mitigation**: PyJWKClient caches JWKS keys; auth works until cache expires.
- **If auth is failing**: Consider temporary HMAC fallback (`HOSPITAL_AI_JWT_ALGORITHM=HS256` + `HOSPITAL_AI_JWT_HMAC_SECRET`) with explicit incident approval.
- **Recovery**: Verify JWKS endpoint, restart backend to refresh cache.

## 5.8 P1 — VPS Disk/Memory Exhaustion
- **Immediate**: `df -h`, `free -h`, `docker system df`.
- **Mitigation**: `docker system prune -f`, check pg_dump retention, stop non-essential containers.
- **If <1GB disk**: Emergency prune, remove old backups from VPS (keep off-host copies).

## 5.9 Emergency LLM Disable
- Set `HOSPITAL_AI_CHAT_PROVIDER=stub` in Dokploy.
- Restart backend and worker.
- Returns canned/stub responses without calling external APIs.
- Reverse by setting `gemini` and restarting.

## 6. Contacts

| Role | When |
|------|------|
| Backend Lead | API, DB, worker issues |
| Frontend Lead | UI issues |
| DevOps Lead | Infrastructure, Dokploy, VPS deployment |
| Security Lead | Security incidents |
| Product Owner | User communication |
| R2 Account Owner | Object storage outages or credential rotation |
| Gemini/DeepSeek Admin | LLM provider quotas, keys, and limits |

## 7. Post-Mortem Template

```
# Incident: [Title]
- Date: YYYY-MM-DD · Duration: X hours · Severity: P1/P2/P3
- Timeline: [Time] → [Event]
- Root Cause: [What happened]
- Impact: Users/data/downtime affected
- Resolution: [How fixed]
- Prevention: [ ] Action 1 · [ ] Action 2
```

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Incident response: severity, P1/P2 runbooks, contacts, post-mortem |
| 2.0 | 2026-08-04 | Agent | Replaced Ollama references, added incident responses for Quotas, R2, JWKS, VPS exhaustion, and updated contacts |
