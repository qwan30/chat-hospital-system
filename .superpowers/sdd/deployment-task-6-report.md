# Task 6 report - VPS and Dokploy preflight contract

Status: DONE

## What I implemented

- Expanded `docs/10-deployment/vps-operations.md` into a placeholder-only,
  auditable preflight runbook for VPS and Dokploy operators.
- Added `docs/10-deployment/vps-preflight-evidence.md` with a required-evidence
  table for candidate SHA, CI Run ID, synthetic/de-identified data, OS/version,
  RAM, disk, swap, SSH key access, firewall, ports `22/80/443/3000`, Docker,
  Docker Compose, Dokploy, GitHub, GHCR, secret-key presence, CORS, and the
  Vercel-to-API route.
- Extended `app/backend/scripts/verify_deployment_contract.py` so repository
  validation now requires:
  - the new preflight runbook and evidence template;
  - explicit frontend API-base and CORS documentation;
  - no wildcard CORS contract text;
  - explicit external-boundary / UNVERIFIED language;
  - deterministic, repository-only validation with unchanged exit semantics
    (`0` valid, `2` invalid, `--json` supported).
- Extended `app/backend/tests/test_deployment_contracts.py` with an invalid
  fixture that breaks the new CORS and preflight-row invariants.

## Files changed

- `docs/10-deployment/vps-operations.md`
- `docs/10-deployment/vps-preflight-evidence.md`
- `app/backend/scripts/verify_deployment_contract.py`
- `app/backend/tests/test_deployment_contracts.py`
- `.superpowers/sdd/deployment-task-6-report.md`

## Test commands and results

- `python -m pytest --noconftest tests/test_deployment_contracts.py`
  - Result: `8 passed in 0.83s`
- `python app/backend/scripts/verify_deployment_contract.py --json`
  - Result: `{"valid": true, "violations": []}`
- `ruff check app/backend/scripts/verify_deployment_contract.py app/backend/tests/test_deployment_contracts.py`
  - Result: passed
- `ruff format --check app/backend/scripts/verify_deployment_contract.py app/backend/tests/test_deployment_contracts.py`
  - Result: passed after formatting the validator file once with `ruff format`
- Docs sanity check:
  - Command: inline Python check for required markers plus pending evidence rows
  - Result: `docs sanity ok: 20 pending rows`
- `git diff --check`
  - Result: passed (only CRLF normalization warnings from git)

## Notes

- An initial run of `python -m pytest tests/test_deployment_contracts.py`
  loaded the repository `conftest.py` and failed in this local environment
  because `cryptography` is not installed. The focused Task 6 file itself passed
  cleanly with `--noconftest`, which avoids unrelated backend fixture loading.
- No live provisioning, VPS mutation, Dokploy installation, DNS change, GHCR
  login, R2 check, backup/restore proof, or runtime proof was performed or is
  claimed by this task.

## Review-fix follow-up - 2026-08-04

- Hardened the evidence-table validator so it parses the Markdown table
  structurally, requires every required check exactly once, requires the exact
  `PENDING — operator evidence required` status, and rejects duplicate,
  unexpected, or malformed data rows with actionable violation codes.
- Restored the frontend secret gate to walk the full `app/frontend` tree while
  still ignoring `.git`, `node_modules`, `.next`, `dist`, `coverage`,
  `__pycache__`, unreadable files, and binary files. The validator keeps a
  narrow allowlist for `app/frontend/scripts/verify-public-bundle.mjs` because
  that file intentionally embeds the denylist markers and leak fixtures used by
  the frontend scanner itself.
- Applied wildcard CORS rejection to `env-variables.md`, `vps-operations.md`,
  and `vps-preflight-evidence.md`, including dynamic-origin-reflection contract
  text.
- Expanded focused invalid-fixture coverage for:
  - extra non-pending evidence rows;
  - duplicate/changed evidence rows that would otherwise mask missing checks;
  - malformed evidence rows;
  - wildcard CORS in each Task 6 deployment document.

Review-fix verification:

- `python -m pytest --noconftest tests/test_deployment_contracts.py`
  - Result: `14 passed in 7.50s`
- `python app/backend/scripts/verify_deployment_contract.py --json`
  - Result: `{"valid": true, "violations": []}`
- `ruff format app/backend/scripts/verify_deployment_contract.py app/backend/tests/test_deployment_contracts.py`
  - Result: `2 files reformatted` on the first pass, then clean
- `ruff check app/backend/scripts/verify_deployment_contract.py app/backend/tests/test_deployment_contracts.py`
  - Result: passed
- `ruff format --check app/backend/scripts/verify_deployment_contract.py app/backend/tests/test_deployment_contracts.py`
  - Result: passed
- Docs sanity
  - Result: `docs sanity ok: 20 pending rows`

Final-review frontend-secret fix - 2026-08-04

- Mirrored the backend validator's frontend denylist to the same backend-only
  markers used by `app/frontend/scripts/verify-public-bundle.mjs` for DB,
  Redis, R2, LLM, HMS, JWT, and postgres/redis/ollama leak detection, while
  keeping the existing allowlist for the scanner source itself.
- Added a focused invalid fixture that copies a frontend source file to
  `app/frontend/src/proof-secret.ts`, injects `HOSPITAL_AI_DATABASE_URL`, and
  asserts `--json` exits `2` with `frontend_secret_leak`.

Final-review fix verification:

- `python -m pytest --noconftest tests/test_deployment_contracts.py`
  - Result: `15 passed in 6.61s`
- `python app/backend/scripts/verify_deployment_contract.py --json`
  - Result: `{"valid": true, "violations": []}`
- `ruff check app/backend/scripts/verify_deployment_contract.py app/backend/tests/test_deployment_contracts.py`
  - Result: passed
- `ruff format --check app/backend/scripts/verify_deployment_contract.py app/backend/tests/test_deployment_contracts.py`
  - Result: `2 files already formatted`
- `git diff --check`
  - Result: exit `0`; Git reported only existing LF→CRLF working-copy warnings
