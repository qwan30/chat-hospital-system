# Dokploy deployment follow-up plan — Tasks 5–6

## Source and dependency

This follow-up continues the deployment plan recovered from Codex task
`019fc869-4166-7aa2-8b9c-27c802dfdf6e`. Tasks 2–4 are already merged in PR #82
at `062ed94`; this branch starts from that exact `main` state.

The two tasks deliberately separate repository-verifiable contracts from
operator actions on a real Vercel project, VPS, Dokploy instance, DNS zone,
GHCR registry, or secret store.

## Global constraints

- Keep the frontend on Vercel and the backend/worker on Dokploy/Traefik.
- Use `VITE_API_URL=/api` for local Vite proxy development.
- Use a full direct API base including `/api/v1` for Vercel, for example
  `https://api.example.com/api/v1`; do not rely on an implicit proxy rewrite in
  a deployed frontend.
- Keep bearer tokens in React memory only. Persisting an API URL is allowed for
  local developer ergonomics, but a build-time Vercel URL must take precedence
  over stale local storage.
- CORS must use an explicit origin allowlist. Do not use `*`, dynamic reflection,
  or a claim that arbitrary Vercel preview URLs are approved.
- Frontend bundles may contain only public `VITE_*` configuration. Backend,
  database, R2, LLM, HMS, and JWT secrets must remain server-side.
- Use synthetic or de-identified data only. Do not add real domains,
  credentials, tokens, patient identifiers, or provider setup values.
- Task 6 may document operator-run commands and evidence fields, but must not
  install Dokploy, change a VPS, configure DNS/firewalls, contact GHCR/R2, or
  claim runtime/backup/restore/production evidence.
- Every external deployment result remains `UNVERIFIED` until an operator
  records candidate-specific evidence; repository tests are not deployment
  smoke tests.

## Task 5 — Keep the frontend on Vercel

### Scope

Make the deployed frontend use one explicit API-base contract across ordinary
API calls, login and `/auth/me`, upload/blob calls, and `POST /chat/stream`.
Keep local `/api` proxy behavior intact, and prevent a stale persisted local URL
from overriding a Vercel build-time `VITE_API_URL`.

Add a dependency-free public-bundle scanner that can be run against the actual
Vercel output directory after a build. It must fail on backend-only secret names
or values and report the scanned path; it must not claim that a missing build
directory passed.

Document separate local, Vercel preview, and Vercel production values,
including exact API paths and matching backend CORS origins. State that preview
domains must be explicitly approved and supplied to the backend allowlist.

### Owned files

- `app/frontend/src/lib/api-client.ts`
- `app/frontend/src/lib/auth-context.tsx`
- `app/frontend/src/lib/api-client.test.ts`
- `app/frontend/src/lib/auth-context.test.tsx`
- `app/frontend/src/lib/stream-client.test.ts`
- `app/frontend/scripts/verify-public-bundle.mjs`
- `app/frontend/package.json`
- `docs/10-deployment/env-variables.md`
- `.superpowers/sdd/deployment-task-5-report.md`

### Acceptance

- Local API requests still resolve through `/api` and Vite rewrites them to
  `/api/v1`.
- Direct Vercel requests resolve through the configured
  `https://<api-host>/api/v1` base for login, `/auth/me`, normal API calls,
  binary fetches, and SSE.
- Auth tests prove an old `hospital_ai_api_url` local-storage value cannot
  override a non-empty build-time `VITE_API_URL`; tokens are never written to
  storage.
- SSE tests prove the API path and bearer header are preserved and the existing
  abort/watchdog behavior remains intact.
- The bundle scanner has passing and failing fixture tests or an equivalent
  deterministic test harness, and its missing-target behavior is explicit.
- Frontend unit tests, typecheck, lint, build, and the public-bundle scan run
  against synthetic values before Task 5 is reported complete.

## Task 6 — Prepare the VPS and Dokploy operator contract

### Scope

Turn the original VPS/Dokploy preparation task into a safe, auditable operator
preflight package. Cover OS, RAM, disk, swap, SSH key access, firewall, ports
22/80/443/3000, Docker and Compose versions, Dokploy installation/domain,
GitHub/GHCR connection, secret injection, and the required Vercel-to-API route.

The package must include an evidence table with command, expected result,
operator-captured value, timestamp, owner, and status. Every row starts as
`PENDING — operator evidence required`; no repository check may mark it as
passed from static inspection alone.

Extend the repository deployment validator and focused tests to require the
preflight contract, explicit CORS/API-base documentation, no wildcard CORS,
and clear unverified/external-boundary language.

### Owned files

- `docs/10-deployment/vps-operations.md`
- `docs/10-deployment/vps-preflight-evidence.md`
- `app/backend/scripts/verify_deployment_contract.py`
- `app/backend/tests/test_deployment_contracts.py`
- `.superpowers/sdd/deployment-task-6-report.md`

### Acceptance

- Runbook commands are operator-run placeholders and do not contain secrets or
  destructive broad-scope commands.
- The preflight evidence template covers all required VPS/Dokploy checks and
  explicitly distinguishes static repository validation from external proof.
- Validator exit semantics remain `0` for a valid repository contract and `2`
  for an invalid contract, with actionable text and `--json` output.
- Focused tests cover the current repository and at least one invalid fixture
  for the new preflight/CORS/API-base invariants.
- No documentation claims that Dokploy, VPS, DNS, GHCR, R2, backups, restore,
  HTTPS, or runtime health has been configured or verified.

## Validation and delivery gates

- Each task is implemented by a fresh subagent and receives a task-scoped spec
  and quality review before the next task begins.
- Important/Critical review findings block progress until fixed and re-reviewed.
- Final whole-branch review covers the merge base `062ed94` through `HEAD`.
- Run relevant frontend/backend tests, typecheck/lint/build, the deployment
  validator, `git diff --check`, secret scans, and GitNexus `detect_changes()`
  before committing.
- Push `feat/deployment-tasks-5-6` and open one PR to `main` only after all
  required repository gates and the final review are clean. Call out all
  external checks as unverified in the PR body.
