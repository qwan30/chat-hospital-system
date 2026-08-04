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

## Required environment secrets

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

## Verification boundary

The repository can verify workflow structure, tag validation, and payload
construction. It cannot verify an external Dokploy hook, VPS state, runtime
health, database migration result, R2 availability, or production approval.
Those remain external release gates and must be recorded separately from a
successful GitHub Actions handoff.
