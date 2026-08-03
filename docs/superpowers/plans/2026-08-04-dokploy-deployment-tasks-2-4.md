# Dokploy deployment follow-up plan — Tasks 2–4

## Context

Task 1 froze the deployment shape as Vercel frontend + Dokploy/Traefik
backend and worker on the VPS, Cloudflare R2 for durable documents, Gemini as
the VPS default provider, and no Supabase/Ollama/Nginx in the VPS stack.

The remaining repository gap is that the older GitHub Actions CD and rollback
workflows still describe direct SSH/SCP Compose deployment. Tasks 2–4 close
that gap without provisioning external infrastructure or placing secrets in
Git.

## Task 2 — Dokploy release handoff

- Make CI publish an explicit immutable `sha-<short-sha>` backend image tag.
- Replace direct SSH/SCP deployment in CD with a Dokploy webhook handoff.
- Keep staging automatic after successful main CI; keep production manual and
  environment-gated.
- Fail closed for invalid `latest`/floating image inputs, while allowing a
  clearly reported no-op when the external Dokploy hook is not configured.
- Replace the rollback workflow's obsolete SSH deployment with a validated
  rollback handoff contract and document the required environment secret.

## Task 3 — VPS operational safety

- Document Dokploy-specific rollback, PostgreSQL backup/restore, R2 object
  retention, secret rotation, and incident escalation procedures.
- Keep observability opt-in on the 4 GB VPS and specify resource/port/backup
  preflight controls.
- Remove stale Ollama and direct-Nginx assumptions from operational docs.

## Task 4 — Executable contract gate

- Add a standard-library-only validator for Compose, workflow, secret-scope,
  provider, and public-port invariants.
- Add focused tests for both passing and failing contract fixtures.
- Run the validator in the CI infrastructure validation job and expose its
  output as a release-checklist gate.

## Non-goals

- Do not provision Dokploy, Cloudflare, R2, DNS, or VPS resources from GitHub
  Actions.
- Do not add automatic Gemini/DeepSeek failover.
- Do not move the frontend from Vercel to the VPS.
- Do not claim a production deployment or PHI/compliance approval.
