# Incident Response

> Project: HOSP-AI-001 · Version: 2.1 · Owner: DevOps Lead · Last Updated: 2026-08-04

## 1. Severity Levels

| Level | Definition | Response | Example |
|---|---|---|---|
| P1 — Critical | System unavailable, data loss, or PHI breach | Immediate | API down, DB corrupted, unauthorized access |
| P2 — High | Core feature unavailable or seriously degraded | <1 hour | Chat, upload, provider, or queue failure |
| P3 — Medium | Partial degradation | <4 hours | Slow responses, non-critical endpoint down |
| P4 — Low | Minor/cosmetic issue | Next business day | UI defect |

## 2. Process

`DETECT → TRIAGE → PRESERVE EVIDENCE → MITIGATE → RECOVER → VERIFY → POST-MORTEM`

## 3. P1 System Down

1. Check recent deployment and release record.
2. Check `df -h`, `free -h`, `docker stats --no-stream`, and `docker system df`.
3. Check PostgreSQL, Redis, backend, and worker health.
4. Roll back only to a verified immutable image when migration compatibility permits.
5. Preserve required rollback images and evidence before removing any data.

For disk exhaustion, identify the consumer first. Remove expired local backups or confirmed unused images selectively. Do not use blanket destructive pruning as the default response.

## 4. P1 Security or PHI Incident

1. Isolate affected credentials, tokens, and network paths.
2. Preserve audit logs and timelines.
3. Notify Security Lead, Product Owner, and Hospital IT.
4. Rotate affected secrets and verify authorization controls before restoring service.

## 5. P2 Chat, RAG, or Provider Degradation

1. Check Gemini/DeepSeek health and quota.
2. Check both active queues: `document-indexing`, `cdss-analysis`, and `document-generation-build`.
3. Inspect `FailedJobRegistry` for each queue.
4. Set `HOSPITAL_AI_CHAT_PROVIDER=stub` only when external LLM calls must be disabled.
5. Restore an approved provider after validation.

## 6. P2 R2 Outage

- New uploads and R2-backed reads fail; there is no automatic local-document failover.
- Preserve queued work and avoid repeated destructive retries.
- Monitor Cloudflare status and application errors.
- Resume or retry operations after service recovery.
- Use the independent backup only for confirmed loss or corruption.

## 7. P2 HMS JWKS Outage

- JWT validation fails closed when required keys cannot be obtained or validated.
- Check HMS IdP health, DNS, routing, TLS, and the configured JWKS URL.
- Cached keys may allow limited continued operation until expiry; do not restart healthy instances without a reason.
- Restore the same RS256/JWKS trust path.
- Do not switch to HS256 or introduce an HMAC secret as an emergency workaround.

## 8. Contacts

| Role | When |
|---|---|
| Backend Lead | API, database, worker, and queue incidents |
| Frontend Lead | Client-side incidents |
| DevOps Lead | Dokploy, VPS, deployment, backup, and rollback |
| Security Lead | Security, authentication, or PHI incidents |
| Product Owner | User communication and business impact |
| R2 Account Owner | Object storage incidents and credential rotation |
| LLM Provider Admin | Provider quota, keys, and billing |

## 9. Post-Mortem Minimums

Record incident severity, affected users/data, exact release SHA and digest, timeline, root cause, mitigation, recovery verification, and owned prevention actions.

## Change Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-06-14 | Agent | Initial incident response |
| 2.0 | 2026-08-04 | Agent | Dokploy/R2/provider incident additions |
| 2.1 | 2026-08-04 | Agent | Fail-closed JWKS, R2, queue, and disk response corrections |
