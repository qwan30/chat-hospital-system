# CI/CD release handoff

> Project: AI-Powered Hospital Knowledge Assistant
> Status: Dokploy handoff contract
> Last updated: 2026-08-04

This document describes the repository-side release handoff. It does not provision Dokploy or claim that an accepted webhook completed a deployment. The frontend remains on Vercel; Dokploy manages the backend and worker on the VPS.

## Release identity

CI publishes the backend as:

```text
ghcr.io/<repository-owner>/hospital-ai-backend:sha-<first-7-lowercase-hex-characters-of-commit-sha>
```

Floating tags such as `latest`, branch names, and incomplete SHAs are rejected. CD validates the full 40-character source SHA, verifies that the tag matches its first seven characters, and then resolves the registry's top-level manifest digest with `docker buildx imagetools inspect`. The digest must match `sha256:<64-lowercase-hex>`; lookup or parsing failures stop the workflow before any external request.

## Deployment handoff

`.github/workflows/cd.yml` sends a JSON POST to the selected environment's Dokploy deploy hook. The payload includes the environment, immutable image tag, source SHA, workflow run ID, and—only for production—the reviewed staging smoke run ID.

A 2xx response means the handoff was accepted. It does not prove that migrations completed, containers became healthy, or runtime checks passed.

| Target | Trigger | GitHub environment | Missing deploy hook |
|---|---|---|---|
| Staging | Successful CI `workflow_run`, or manual staging dispatch | `staging` | Records a pending no-op; no deployment is claimed |
| Production | Manual dispatch only | `production` approval/protection | Fails closed |

Production dispatch requires:

- the immutable `sha-<7-hex>` tag;
- the full source SHA;
- `staging-smoke-run-id`, a numeric GitHub Actions run ID for the successful staging CD run reviewed by the production approver.

The repository records and links that run ID but does not automatically prove that it tested the same SHA. The human production approval gate must compare the staging run's source SHA, image identity, and smoke result with the requested production candidate.

## Release record

A release record is written only after the Dokploy hook accepts the request. It includes:

| Field | Source |
|---|---|
| Environment | Trigger/input |
| Git SHA | Validated full source SHA |
| Image Reference | Immutable GHCR tag |
| Image Digest | Validated top-level registry manifest digest |
| Staging smoke evidence | Production-only link to the reviewed staging run |
| Migration Revision | Pending external verification |
| Smoke Test | Pending external verification until runtime validation completes |
| Workflow Run | Current GitHub Actions run ID |
| Timestamp | UTC |

## Blocking staging smoke test

After a successful staging handoff, the `smoke-test` job:

- binds to the GitHub `staging` Environment;
- reads `DOKPLOY_APP_URL` from that environment;
- fails immediately if the value is missing or is not an HTTP(S) base URL;
- waits 30 seconds, then attempts `GET /api/v1/health` five times;
- uses 10-second connection and 20-second total request timeouts;
- sleeps 30, 60, 120, and 240 seconds between failed attempts;
- fails the staging CD workflow when health never becomes ready.

A failed smoke test is not advisory and must not be used as production evidence.

## Production promotion

1. CI builds, tests, scans, and publishes the immutable image.
2. CD hands the image to staging.
3. The blocking staging smoke job passes.
4. An operator verifies authentication, R2 access, both RQ queues, Gemini/DeepSeek behavior, migrations, and SSE streaming.
5. The operator manually dispatches production with the same immutable identity and the successful staging run ID.
6. The production environment approver verifies that evidence before approving the hook.
7. Runtime migration and smoke evidence is recorded after Dokploy completes the deployment.

## Required GitHub Environment configuration

### Secrets

| Environment | Secret | Use |
|---|---|---|
| `staging` | `DOKPLOY_DEPLOY_HOOK_URL` | Staging deploy handoff |
| `production` | `DOKPLOY_DEPLOY_HOOK_URL` | Approved production deploy handoff |
| `staging` | `DOKPLOY_ROLLBACK_HOOK_URL` | Staging rollback handoff |
| `production` | `DOKPLOY_ROLLBACK_HOOK_URL` | Production rollback handoff |

### Variables

| Environment | Variable | Use |
|---|---|---|
| `staging` | `DOKPLOY_APP_URL` | Base URL for the blocking staging health check |

No hook URL, API key, registry credential, or runtime secret belongs in Git.

## Verification boundary

The repository verifies workflow structure, immutable identity, manifest digest format, payload construction, environment-scoped URL configuration, and HTTP health response. Dokploy state, migration revision, R2 behavior, authentication, worker processing, and production approval remain external operational evidence.
