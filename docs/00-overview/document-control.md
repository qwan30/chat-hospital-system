# Document Control

> Project: HOSP-AI-001 — AI Hospital Knowledge Assistant  
> Version: 1.0  
> Owner: Tech Lead  
> Last Updated: 2026-06-14  
> Status: Approved  

---

## Approval Matrix

| Document | Owner | Reviewer | Approver | Status |
|----------|-------|----------|----------|--------|
| Project Foundation | Tech Lead | System Architect | Product Owner | Approved |
| BRD | Product Owner | Business Analyst | Sponsor | Approved |
| PRD | Product Owner | Tech Lead | Sponsor | Approved |
| Architecture | System Architect | Tech Lead | Product Owner | Approved |
| API Contract | Backend Lead | Tech Lead | System Architect | Approved |
| DB Schema | Backend Lead | Tech Lead | System Architect | Approved |
| Test Plan | QA Lead | Backend Lead | Tech Lead | Approved |
| Deployment Guide | DevOps Lead | Tech Lead | System Architect | Approved |
| Security Architecture | Security Lead | System Architect | Product Owner | Approved |

---

## Versioning Rules

Use semantic versions for major documentation baselines:

- `0.x`: Draft
- `1.0`: First approved baseline
- `1.x`: Minor updates (content changes, corrections)
- `2.0`: Major changes (architecture shifts, new phases)

---

## Review Checklist

Before approving any documentation update:

- [ ] Requirements are clear and unambiguous
- [ ] Scope is explicit (in-scope and out-of-scope)
- [ ] Business rules are testable
- [ ] APIs and database models are consistent with each other
- [ ] Flows match documented requirements
- [ ] Test cases cover critical flows and acceptance criteria
- [ ] Cross-references between documents are valid
- [ ] No stale references to deleted or renamed files

---

## Last Sync Verification (June 14, 2026)

| Check | Status |
|-------|--------|
| All 13 DB tables documented in db-schema.md | ✅ Verified |
| All 14 API route modules in api-contract.md | ✅ Verified |
| Architecture worker system matches code (RQ, not Celery) | ✅ Verified |
| No references to deleted `00-overview/` files in other docs | ✅ Verified |
| ERD matches actual models.py schema | ✅ Verified |
| Metrics documented as MetricsService, not metric_events table | ✅ Verified |
| LLM documented as LLM Manager multi-provider, not Ollama-only | ✅ Verified |

---

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 0.1 | 2026-04-27 | Tech Lead | Initial draft |
| 1.0 | 2026-06-14 | Agent | Full sync verification against codebase — all docs validated |
