# CI/CD Pipeline Specification

> Project: AI-Powered Hospital Knowledge Assistant  
> Project Code: HOSP-AI-001  
> Version: 3.0  
> Status: Production  
> Owner: DevOps / SRE / Tech Lead  
> Last Updated: 2026-06-14  

---

## 1. Workflow Overview

The project uses **5 GitHub Actions workflows** providing defense-in-depth:

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| **CI** | `.github/workflows/ci.yml` | Push, PR, Manual | Code quality, testing, security, Docker build+scan+push |
| **CD** | `.github/workflows/cd.yml` | CI success, Manual | Staging auto-deploy, production promotion, Slack notify |
| **Security Scan** | `.github/workflows/security-scan.yml` | Weekly cron, Manual | Dep audit, secret detection, container scanning |
| **Rollback** | `.github/workflows/rollback.yml` | Manual only | Emergency rollback with confirmation gate |
| **Dependabot** | `.github/dependabot.yml` | Automatic | Weekly dependency update PRs (npm, pip, GHA) |

---

## 2. CI Pipeline (8 Jobs)

| # | Job | Gates | Artifacts |
|---|-----|-------|-----------|
| 1 | `changes` | Path-based skip (dorny/paths-filter v3) | Output: backend, frontend, infra booleans |
| 2 | `codeql` | Security-extended queries (Python + JS/TS matrix) | SARIF → Security tab |
| 3 | `backend-test` | Ruff lint + format, Pytest 250+, API contract verify | Test results (7-day) |
| 4 | `backend-migration` | Alembic upgrade head + model alignment check | — |
| 5 | `frontend-test` | ESLint, TypeScript strict, Vitest, TanStack Start build, Playwright E2E | Playwright report (7-day) |
| 6 | `validate-observability` | Docker Compose config validation (2 files) | — |
| 7 | `docker-push` | Multi-stage build, Trivy scan, GHCR push | Trivy SARIF → Security tab |
| 8 | `ci-summary` | Aggregate all results, fail on any failure | Step summary table |

**Key features**: Concurrency cancellation, Playwright browser cache, TanStack Start build cache, Docker Buildx GHA cache, path-aware job skipping.

---

## 3. CD Pipeline (Staging → Production)

1. **Staging** (auto on CI pass): SCP `infra/` configs → SSH pull GHCR image → Alembic migration → `docker compose up -d` → 12-attempt smoke check
2. **Production** (auto-promote from staging): Same process → 15-attempt smoke check → Slack notification
3. **Manual dispatch**: Can target specific environment + image tag

---

## 4. Scheduled Security Scan (Weekly)

Runs every Monday 06:00 UTC:

| Scan | Tool | Scope |
|------|------|-------|
| Frontend deps | `npm audit --audit-level=high` | app/frontend/ |
| Backend deps | `pip-audit` | app/backend/ |
| Backend SAST | `bandit -r src/ -ll` | Python source |
| Secret detection | TruffleHog (full git history) | Entire repo |
| Container images | Trivy (CRITICAL,HIGH,MEDIUM) | GHCR backend:latest |

---

## 5. Rollback

Manual `workflow_dispatch` with `ROLLBACK` confirmation string gate → SSH to target → `docker pull <specific-tag>` → `docker compose up -d` → health check.

---

## 6. Dependabot

| Ecosystem | Directory | Groups |
|-----------|-----------|--------|
| npm | `/app/frontend` | react, nextjs, testing, radix, tailwind |
| pip | `/app/backend` | fastapi, database, testing, ai-ml |
| github-actions | `/` | — |

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | DevOps Engineer | Initial pipeline definition |
| 2.0 | 2026-06-07 | Agent | Restructured into dedicated CI/CD documentation with graphical flow |
