# Deployment Task 4 report — executable deployment-contract gate

## Outcome

Added a deterministic standard-library-only validator and wired it into the CI
infrastructure validation job. The gate checks repository invariants only; it
does not contact Dokploy, GHCR, Cloudflare, the VPS, or an LLM provider.

## Delivered

- `app/backend/scripts/verify_deployment_contract.py` locates the repository,
  validates Compose/workflow/docs/secret-scope invariants, prints actionable
  failures, supports `--json`, and returns `0` for valid or `2` for invalid
  repository contracts.
- Focused tests cover the current repository and a temporary fixture with a
  forbidden public backend port.
- CI path filtering now schedules the validator for deployment/workflow/doc
  changes, and `validate-observability` runs it alongside Compose validation.
- `release-checklist.md` now contains the validator command and Dokploy/Vercel
  staging/demo promotion gates, with the stale Ollama latency assumption removed.

## Verification

- `python app/backend/scripts/verify_deployment_contract.py --json` — valid.
- `& .\\app\\backend\\.venv\\Scripts\\python.exe -m pytest app/backend/tests/test_deployment_contracts.py -q -p no:cacheprovider` — `8 passed, 1 warning`.
- `git diff --check` — pass.

## External boundary

The validator cannot prove provider credentials, Dokploy configuration, GHCR
access, VPS health, backups/restores, or production readiness.
