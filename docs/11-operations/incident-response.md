# Incident Response

> Project: HOSP-AI-001 · Version: 1.0 · Owner: DevOps Lead · Last Updated: 2026-06-14  

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
1. Check Ollama: `curl localhost:11434/api/tags`
2. Check embedding service
3. Check RQ queue depth
4. Switch to stub temporarily if needed
5. Reduce retrieval_top_k

## 6. Contacts

| Role | When |
|------|------|
| Backend Lead | API, DB, worker issues |
| Frontend Lead | UI issues |
| DevOps Lead | Infrastructure, deployment |
| Security Lead | Security incidents |
| Product Owner | User communication |
| Hospital IT | Network, hardware |

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
