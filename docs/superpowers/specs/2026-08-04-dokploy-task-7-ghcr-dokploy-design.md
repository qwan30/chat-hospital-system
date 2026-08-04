# Dokploy Task 7: GitHub-Built Image and Staging Deployment Design

> Status: Approved design for implementation on `feat/deployment-task-7-ghcr-dokploy`
> Date: 2026-08-04
> Baseline: `main` at `6b7c8d1`, which includes the merged Task 5–6 repository contracts

## Goal

Make Task 7 deploy staging through one unambiguous release path:

```text
GitHub Actions
  -> test, migration-check, build, scan, and push immutable GHCR image
  -> Dokploy deploy hook with image tag, source SHA, and workflow identity
  -> Dokploy pulls the candidate image and runs the VPS stack
```

The VPS must not build the backend image from the cloned source tree. It should
only pull the selected immutable image, run the controlled migration step, and
start the backend and worker services. The deployment remains a staging/demo
deployment and is not a hospital production certification.

## Context and conflict resolution

Task 5 and Task 6 are already merged into `main`. Their repository-side
contracts intentionally leave live Vercel, VPS, Dokploy, GHCR, DNS, R2, and
runtime evidence to the operator.

The older Task 7 sequence mixed two incompatible deployment control planes:

1. Dokploy/GHCR image deployment; and
2. an SSH operator building and starting Compose from a VPS source clone.

Task 7 resolves this by making GitHub/GHCR/Dokploy the only normal release
control plane. The VPS source clone is not a build input for the normal staging
path. A local build override remains available for developer validation only.

The frontend API base is also fixed to one convention: deployed Vercel builds
use `https://<api-host>/api/v1`; callers append only endpoint-relative paths.
Local development continues to use `/api` through the Vite proxy.

## Architecture

### Normal release flow

```text
Reviewed commit on main
        |
        v
CI tests + migration check + frontend checks + Compose contract check
        |
        v
Build app/backend/Dockerfile on GitHub
        |
        v
Trivy scan + push ghcr.io/<owner>/hospital-ai-backend:sha-<short-sha>
        |
        v
CD verifies image and sends Dokploy hook
        |
        v
Dokploy sets BACKEND_IMAGE to the immutable tag or digest
        |
        v
Dokploy migration job -> backend/worker rollout -> HTTPS health/smoke tests
```

### Runtime service ownership

| Service | Built where | Runs where | Publicly exposed | Persistent data |
|---|---|---|---|---|
| Backend | GitHub Actions | Dokploy/VPS | Through Dokploy/Traefik only | Temporary application state only |
| RQ worker | Same backend image | Dokploy/VPS | No | Temporary application state only |
| PostgreSQL + pgvector | Pulled base image | Dokploy/VPS | No host port | `postgres-data` volume |
| Redis | Pulled base image | Dokploy/VPS | No host port | No durable document source |
| Frontend | Vercel build | Vercel | Vercel HTTPS | None on VPS |
| Documents | Not in image | Cloudflare R2 | Backend-authorized access | R2 is the durable source |

## Functional requirements

### R1. Production Compose is image-only

`infra/docker-compose.yml` is the Dokploy production contract.

- `backend` and `worker` use the same required `BACKEND_IMAGE` value.
- The production Compose file contains no `build:` stanza.
- `BACKEND_IMAGE` must be supplied explicitly; an unset value is a Compose
  configuration error.
- The release value must be a non-floating GHCR tag in the form
  `ghcr.io/<owner>/hospital-ai-backend:sha-<7-lowercase-hex>` or an immutable
  digest reference.
- `latest` is not a staging or production release identity.
- PostgreSQL, Redis, and the application services remain on the internal
  Compose network. Only the backend is reachable through Dokploy/Traefik.

### R2. Local build is explicitly separated

Create `infra/docker-compose.local-build.yml` as a developer-only override.
It adds the backend Docker build context without changing the production
Compose contract. Documentation must show that local builds use an explicit
local image name such as `hospital-ai-backend:local`.

The VPS staging runbook must never instruct an operator to use this override.

### R3. GitHub owns image construction

Keep the existing CI image pipeline as the image construction authority:

- backend tests, migration checks, frontend checks, and infrastructure checks
  must pass before image publication;
- the image is tagged with the source commit's immutable `sha-<7-hex>` tag;
- the image is scanned before it is handed off;
- the release artifact records source SHA, image tag, image digest, repository,
  and workflow run ID;
- the CD workflow verifies the exact image reference before calling Dokploy;
- a missing staging hook is reported as pending and does not claim deployment;
- a missing production hook fails closed.

Task 7 may adjust the Compose validation invocation so the repository can
render the image-only file with a synthetic, structurally valid image value.
It must not weaken the immutable-image checks.

### R4. Controlled migration order

The candidate image must be used for the database migration. The external
Dokploy release procedure must perform the following order:

1. verify the candidate tag or digest and required environment key names;
2. pull the candidate image and dependent base images;
3. run `alembic upgrade head` as a one-off backend container;
4. start or replace backend and worker using the same image reference;
5. wait for container health and query the public HTTPS health endpoint;
6. run synthetic/de-identified smoke tests for auth, R2, worker processing,
   Gemini, and SSE;
7. record the migration revision and runtime results against the candidate SHA.

The repository documents this as an external Dokploy operation. A GitHub hook
acceptance response is not deployment completion or runtime health evidence.

### R5. VPS resource and disk controls

The 4 GB VPS profile must use explicit service ceilings and no optional
observability overlay by default. The initial Compose limits are:

| Service | Memory ceiling | Rationale |
|---|---:|---|
| PostgreSQL | 768 MiB | Keep pgvector metadata bounded on the small VPS |
| Redis | 256 MiB | Queue/cache only; no document source |
| Backend | 768 MiB | API and streaming workload |
| Worker | 1024 MiB | OCR and document-processing headroom |

The combined ceiling is 2.75 GiB, leaving headroom for Dokploy, Traefik, the
OS, and short-lived pull/migration overhead. The operator must still record
actual RAM, swap, disk, and `docker stats` evidence; limits are not proof of
healthy runtime behavior.

Add `app/backend/.dockerignore` so GitHub's Docker build context excludes
`.git`, virtual environments, caches, test output, local storage, datasets,
uploaded files, logs, `.env` files, and documentation that the production
Dockerfile does not copy. The Dockerfile continues to copy only runtime source,
Alembic files, and dependency metadata.

### R6. Provider and API wording

- Gemini remains the default provider.
- DeepSeek is an explicit provider configuration/switch, not an automatic
  fallback claim.
- Ollama is not part of the VPS stack.
- Vercel production and preview API values include `/api/v1`.
- Backend CORS remains an explicit allowlist of approved Vercel origins.
- No backend, R2, LLM, HMS, or JWT secret appears in the frontend bundle.

### R7. Evidence boundaries

Repository validation may prove Compose/workflow/document invariants only. It
must not mark the following as completed without operator evidence:

- Dokploy installation or routing;
- GHCR credential access;
- VPS memory, swap, disk, or firewall state;
- migration execution;
- R2 availability or backup/restore;
- public health, auth, worker, SSE, or runtime smoke tests;
- production approval or PHI/compliance readiness.

## Scope

### In scope

- production Compose/image-source correction;
- local-only build override;
- backend Docker build-context exclusion;
- resource limits and service comments;
- Compose contract validator/tests for image-only production deployment;
- CI Compose validation input if needed;
- Task 7 deployment, migration, rollback, and evidence documentation;
- wording corrections for immutable image, `/api/v1`, and explicit DeepSeek use.

### Out of scope

- provisioning or mutating the VPS, Dokploy, DNS, firewall, R2, or Vercel;
- creating or rotating real credentials;
- changing frontend/business behavior;
- implementing automatic LLM failover;
- merging, pushing, opening a PR, or claiming a live deployment;
- running database migrations against any external database.

## Acceptance criteria

### Repository gates

- `docker compose -f infra/docker-compose.yml config --quiet` passes when
  supplied with a synthetic `BACKEND_IMAGE` and required non-secret placeholders.
- The production Compose file has no `build:` key and no floating image default.
- Backend and worker resolve to the same `BACKEND_IMAGE`.
- PostgreSQL, Redis, and backend have no public host-port mappings.
- Memory ceilings are present for all four VPS services.
- The local build override is the only Compose file that adds a backend build.
- `.dockerignore` excludes the specified non-runtime content.
- Deployment validator tests include a passing contract and failing fixtures
  for production `build:`, missing required image input, floating release input,
  and missing memory ceilings.
- Existing Task 5–6 frontend, contract, and external-boundary tests remain green.

### Release handoff gates

- CI publishes the candidate image only after the existing required gates pass.
- CD verifies the candidate image and sends the documented Dokploy payload.
- The release artifact binds source SHA, image tag, image digest, and workflow ID.
- Staging deployment remains `UNVERIFIED` until the operator records the
  candidate-specific Dokploy/VPS evidence table.

## Verification strategy

1. Run focused validator tests and Compose contract checks with placeholders.
2. Run the existing deployment validator and `git diff --check`.
3. Run relevant backend/frontend tests required by the changed contract.
4. Inspect the final diff for secrets, `latest` release assumptions, public
   ports, accidental VPS build paths, and contradictory API-base wording.
5. Run GitNexus change detection before any commit if code symbols or tracked
   execution-flow files are changed.
6. Do not call external deployment or runtime evidence green from local checks.
