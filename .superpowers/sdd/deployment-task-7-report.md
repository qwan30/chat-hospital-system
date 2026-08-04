# Deployment Task 7 Report

## Status

Repository-side Task 7 implementation is complete on
`feat/deployment-task-7-ghcr-dokploy`. The branch has not been pushed, merged,
or used to perform an external deployment.

## Implemented contracts

- `infra/docker-compose.yml` is image-only for Dokploy/VPS staging and requires
  the same immutable `BACKEND_IMAGE` for backend and worker.
- `infra/docker-compose.local-build.yml` is the only build-enabled override and
  uses `hospital-ai-backend:local` for developer validation.
- GitHub Actions Compose validation receives a synthetic immutable-shaped image;
  the existing GitHub build, scan, GHCR publication, artifact, and Dokploy CD
  handoff remain the image release authority.
- PostgreSQL, Redis, backend, and worker have explicit `768m`, `256m`, `768m`,
  and `1024m` memory ceilings respectively.
- `app/backend/.dockerignore` excludes source-control metadata, environments,
  caches, tests/output, local data, uploads, logs, `.env` files, and docs.
- The deployment validator rejects production build stanzas, missing or
  floating backend image inputs, backend/worker image mismatches, missing
  memory ceilings, invalid local-build boundaries, and incomplete build-context
  exclusions.
- Candidate runs can pass `--backend-image` through the validator; only the
  GHCR `sha-<7-hex>` tag or `sha256` digest forms are accepted. CI validates its
  synthetic candidate with the same option before the image handoff.
- Deployment, migration, rollback, VPS operations, and candidate evidence docs
  use the GitHub → GHCR → Dokploy flow and the `/api/v1` deployed API base.
- Evidence remains pending by default and now includes candidate pull,
  migration revision, same-image rollout, health, memory, and synthetic smoke
  rows.
- CI path filters include the production Compose file, local build override,
  and backend `.dockerignore`, so changes to any Task 7 deployment input reach
  the infrastructure validation job.
- The VPS runbook starts and waits for PostgreSQL/Redis before the one-off
  migration, then waits for backend/worker after migration; the README's local
  Docker commands use the local build override explicitly.

## Verification evidence

| Command | Result |
|---|---|
| `python -m pytest --noconftest app/backend/tests/test_deployment_contracts.py app/backend/tests/test_ci_workflow.py app/backend/tests/test_storage_contracts.py -v` using `app/backend/.venv` Python 3.11.14 | **PASS** — 45 passed, 1 existing Starlette deprecation warning |
| `ruff check app/backend/scripts/verify_deployment_contract.py app/backend/tests/test_deployment_contracts.py app/backend/tests/test_ci_workflow.py` | **PASS** — all checks passed |
| `ruff format --check app/backend/scripts/verify_deployment_contract.py app/backend/tests/test_deployment_contracts.py app/backend/tests/test_ci_workflow.py` | **PASS** — all three files already formatted |
| `docker compose -f infra/docker-compose.yml config --quiet` with synthetic immutable image and non-secret placeholders | **PASS** |
| `docker compose -f infra/docker-compose.yml -f infra/docker-compose.observability.yml config --quiet` with synthetic placeholders | **PASS** |
| `python app/backend/scripts/verify_deployment_contract.py --json` | **PASS** — `valid: true`, no violations |
| `python app/backend/scripts/verify_deployment_contract.py --backend-image ghcr.io/example/hospital-ai-backend:sha-0000000 --json` | **PASS** — valid candidate accepted |
| `python app/backend/scripts/verify_deployment_contract.py --backend-image ghcr.io/example/hospital-ai-backend:latest --json` | **PASSING NEGATIVE GATE** — exit `2`, `invalid_backend_image` reported |
| GitNexus staged change detection for implementation checkpoints | **PASS** — low risk, no affected execution processes reported |
| Full `app/backend/tests/` suite with the repository `.venv` and a 300-second limit | **INCOMPLETE** — the run timed out without a result; this report does not claim the full suite is green |

The system Python 3.9 runtime was not used for the final evidence because it
did not contain `boto3`. The repository-local `.venv` supplied Python 3.11.14
and the required dependency.

## External boundary

The following remain `UNVERIFIED` and require candidate-specific operator
evidence: Dokploy installation and routing, VPS memory/swap/disk/firewall
state, GHCR credential access, DNS/HTTPS, Vercel environment values, R2
availability and backup/restore, migration execution, public health, auth,
worker, Gemini, R2, and SSE smoke tests, rollback execution, and production or
PHI/compliance approval.
