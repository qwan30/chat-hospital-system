# Deployment Task 2 report — Dokploy release handoff

## Outcome

Implemented the repository-side Dokploy handoff contract. CI already had the
immutable `sha-<short-sha>` release identity and release metadata; this task
kept that contract explicit and replaced the obsolete direct SSH/SCP CD and
rollback paths with environment-scoped Dokploy deploy/rollback hooks.

## Delivered

- `cd.yml` now derives/verifies an immutable image tag from a successful main
  CI run or an explicit manual dispatch, verifies the GHCR image, and sends a
  structured Dokploy handoff payload.
- Staging without a configured deploy hook is recorded as pending and does not
  claim deployment; production requires the hook and fails closed when it is
  absent.
- `rollback.yml` requires `ROLLBACK`, validates the source SHA and immutable
  image tag, verifies the image, requires a separate rollback hook, and never
  performs direct SSH/Compose deployment.
- `ci-cd.md` documents image identity, payloads, environment secrets, and the
  boundary between a webhook acknowledgement and actual runtime health.

## Verification

- PyYAML parsed `.github/workflows/ci.yml`, `cd.yml`, and `rollback.yml`.
- `git diff --check` passed.
- Static search found no `appleboy/ssh-action`, `appleboy/scp-action`, or
  `infra/nginx` reference in the new CD/rollback contract.

## External boundary

Dokploy hooks, GitHub Environment approvals, GHCR package access, VPS health,
and runtime deployment completion remain unverified until configured and run by
an operator. No secrets or production deployment claims were added.
