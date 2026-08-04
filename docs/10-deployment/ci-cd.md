# CI/CD release handoff

> Project: AI-Powered Hospital Knowledge Assistant
> Status: Dokploy handoff contract
> Last updated: 2026-08-04

This document describes the repository-side release handoff. It does not
provision Dokploy, confirm an external deployment, or claim production
readiness. The frontend remains on Vercel; the backend and worker are managed
by Dokploy on the VPS.

## Release identity

The CI `docker-push` job runs only after the existing backend, migration,
frontend, and observability gates pass. It publishes the backend image with
one release identity:

```text
ghcr.io/<repository-owner>/hospital-ai-backend:sha-<first-7-lowercase-hex-characters-of-commit-sha>
```

`latest`, branch tags, and other floating tags are not release identities. CI
also exposes the image reference, image tag, and source SHA as job outputs,
writes the image digest and provenance to `release-handoff.json`, and uploads
that file as the `backend-release-handoff-sha-<short-sha>` artifact. The CD
workflow can derive the same tag from the successful `workflow_run.head_sha`.

The image digest is the strongest immutable identity when it is available;
the `sha-<short-sha>` tag is the required human-readable handoff identity.

The published image is scanned by Trivy for HIGH and CRITICAL findings before
the release handoff artifact is written. A finding or scan failure fails the
`docker-push` job and the CI summary; only the separate frontend E2E advisory
remains non-blocking.

The image is the only normal release artifact. Dokploy must set
`BACKEND_IMAGE` to the exact tag or digest from the handoff. The one-off
`alembic upgrade head` container, backend service, and worker service must all
use that same candidate image. The VPS source clone is not a normal build
input; `git pull`, `docker compose build`, and the local build override are
developer-only operations.

## Deployment handoff

`.github/workflows/cd.yml` sends a JSON POST to the selected environment's
Dokploy deploy hook. The payload includes:

```json
{
  "action": "deploy",
  "environment": "staging or production",
  "image": "ghcr.io/<repository-owner>/hospital-ai-backend:sha-<short-sha>",
  "image_tag": "sha-<short-sha>",
  "source_sha": "<commit-sha>",
  "repository": "<owner>/<repository>",
  "workflow_run_id": "<github-run-id>"
}
```

The external hook must return a 2xx response after accepting the request. A
2xx response means only that the handoff was accepted; it is not a health
check or deployment-completion proof. Dokploy must be configured to consume
the immutable image reference in the payload and to report runtime health
through its own deployment controls.

| Target | Trigger | GitHub environment gate | Missing deploy hook |
|---|---|---|---|
| Staging | Successful CI `workflow_run` on `main`/`master`; or manual dispatch with an immutable tag | `staging` | Clearly reported **PENDING — unconfigured** no-op; no deployment is claimed |
| Production | Manual dispatch with `environment=production` and an immutable tag | `production` approval/environment protection | **Fails closed**; no deployment is claimed |

Production is never auto-promoted by the CI `workflow_run` event. A manual
production request must provide a CI-produced `sha-<short-sha>` tag. Any
`latest`, branch, semver-floating, empty, or otherwise non-immutable input is
rejected before the hook is called.

Dokploy's webhook and auto-deploy configuration is external to this
repository; configure it in Dokploy according to the [Dokploy auto-deploy
documentation](https://docs.dokploy.com/docs/core/auto-deploy).

## Migration and runtime evidence order

The external Dokploy procedure verifies the immutable candidate and required
key names, pulls the candidate image, runs `alembic upgrade head` as a one-off
container, replaces backend and worker with the same image, waits for health,
and runs synthetic/de-identified smoke checks for auth, R2, worker processing,
Gemini, and SSE. Record the migration revision, image digest, source SHA, and
runtime results together. A 2xx hook response does not prove any of these
runtime steps.

## Rollback handoff

`.github/workflows/rollback.yml` is manual and requires the literal
`ROLLBACK` confirmation. It accepts only `sha-<short-sha>` image tags and sends
an explicit rollback payload to the separately configured rollback hook:

```json
{
  "action": "rollback",
  "environment": "staging or production",
  "image": "ghcr.io/<repository-owner>/hospital-ai-backend:sha-<short-sha>",
  "image_tag": "sha-<short-sha>",
  "repository": "<owner>/<repository>",
  "workflow_run_id": "<github-run-id>"
}
```

The rollback hook is intentionally separate from the deploy hook. If it is
missing, the requested rollback fails closed before any external request is
made. A 2xx response means the rollback handoff was accepted; it does not
claim that the running service has recovered.

## Release record

The CD workflow automatically records a structured release record in the GitHub Actions step summary. This record serves as canonical evidence for a deployment:

| Field | Source |
|---|---|
| Environment | Workflow input or derived from trigger |
| Git SHA | Full 40-character commit SHA |
| Image Reference | `ghcr.io/<repository-owner>/hospital-ai-backend:sha-<short-sha>` |
| Image Digest | SHA-256 digest from `docker manifest inspect` |
| Migration Revision | Recorded by operator after external verification |
| Smoke Test | Recorded by staging smoke test job or operator |
| Workflow Run | GitHub Actions run ID |
| Timestamp | UTC timestamp at record creation |

The migration revision and smoke test fields are initially recorded as pending external verification because they depend on Dokploy completing the deployment asynchronously. Operators must record the finalized values in their deployment evidence log after completion.

## Staging smoke test

The `smoke-test` job in the CD workflow runs automatically after a successful staging deployment handoff:

- It runs only for staging deployments where the deploy hook was actually called.
- It waits 30 seconds for deployment to propagate, then retries the health check with exponential backoff (30s, 60s, 120s, 240s, 480s) up to 5 attempts.
- It validates the target endpoint at `<DOKPLOY_APP_URL>/api/v1/health`.
- The job is advisory (`continue-on-error: true`) and records success or failure directly in the GitHub Actions step summary without failing the pipeline.

## Production promotion

Production promotion remains strictly manual until staging smoke tests pass:

1. CI builds, tests, scans, and pushes an immutable GHCR image (`sha-<short-sha>`).
2. CD auto-deploys to staging (if the deploy hook is configured).
3. The staging smoke test runs and records its validation result.
4. An operator verifies staging health, authentication, R2 document access, background worker job completion, Gemini API connectivity, and SSE chat streaming.
5. The operator records the migration revision and smoke test result in the release evidence.
6. The operator manually dispatches the CD workflow with `environment=production`, supplying the validated immutable tag and source SHA.
7. The production environment enforces GitHub environment protection rules requiring explicit manual approval.
8. Upon approval, the production deploy hook fires and the operator records production verification evidence separately.

`latest`, branch names, or floating tags are never accepted as release identities.

## Required environment secrets and variables

### Required environment secrets

Store these as GitHub Actions environment secrets, not repository files or
workflow literals:

| Environment | Secret | Use |
|---|---|---|
| `staging` | `DOKPLOY_DEPLOY_HOOK_URL` | Staging deploy handoff |
| `production` | `DOKPLOY_DEPLOY_HOOK_URL` | Manually approved production deploy handoff |
| `staging` | `DOKPLOY_ROLLBACK_HOOK_URL` | Staging rollback handoff |
| `production` | `DOKPLOY_ROLLBACK_HOOK_URL` | Production rollback handoff |

No hook URL, token, API key, SSH credential, registry credential, or backend
runtime secret belongs in Git. Backend runtime credentials remain configured
only in the backend/worker Dokploy environment. The workflow uses GitHub's
environment-scoped secret value only at request time and does not print it.

### Required environment variables

Configure these as GitHub Actions environment variables (not secrets):

| Environment | Variable | Use |
|---|---|---|
| `staging` | `DOKPLOY_APP_URL` | Staging application base URL for smoke test health checks |

**Note on GHCR access:** The CI workflow uses `GITHUB_TOKEN` for GHCR image pushes (automatic for same-organization repositories). If the container registry or repository is private, Dokploy requires a read-only GHCR token or registry credential configured externally within its deployment controls.

## Verification boundary

The repository can verify workflow structure, tag validation, and payload
construction. It cannot verify an external Dokploy hook, VPS state, runtime
health, database migration result, R2 availability, or production approval.
Those remain external release gates and must be recorded separately from a
successful GitHub Actions handoff.
