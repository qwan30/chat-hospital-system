# PR #85 Release and Operations Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the PR #85 review findings by making CD evidence fail-closed and aligning operations documentation with the repository's actual queue, JWT, R2, and backup behavior.

**Architecture:** Keep workflow enforcement in `.github/workflows/cd.yml` and encode its invariants in one focused contract-test module. Keep operational procedures in the existing runbooks, removing unsupported recovery paths instead of adding new runtime features.

**Tech Stack:** GitHub Actions YAML, Bash, Docker Buildx, jq, Python 3.12, pytest, RQ/Redis, Markdown runbooks.

## Global Constraints

- Production deployment remains manual and protected by the GitHub `production` Environment.
- Staging health failure must fail the staging CD workflow.
- Release identity must be an immutable `sha-<7-hex>` tag paired with a full source SHA and a validated `sha256:<64-hex>` registry digest.
- The active worker queues remain exactly `document-indexing` and `cdss-analysis`.
- JWKS outages fail closed; no RS256-to-HS256 emergency switch is documented.
- R2 has no application-level local-document fallback in this change.
- No repository change provisions external schedulers, Dokploy, R2, or GitHub Environment configuration.

---

### Task 1: Add regression contract tests

**Files:**
- Create: `app/backend/tests/test_cd_operations_contracts.py`
- Read: `.github/workflows/cd.yml`
- Read: `app/backend/src/hospital_ai/workers/run_worker.py`
- Read: `docs/10-deployment/ci-cd.md`
- Read: `docs/11-operations/operations-guide.md`
- Read: `docs/11-operations/monitoring-guide.md`
- Read: `docs/11-operations/incident-response.md`
- Read: `docs/11-operations/troubleshooting.md`

**Interfaces:**
- Consumes: repository files as UTF-8 text.
- Produces: pytest contract tests named `test_cd_*` and `test_operations_*`.

- [ ] **Step 1: Write failing workflow tests**

Add assertions that require `docker buildx imagetools inspect`, reject `|| echo "unknown"`, require full digest validation, require `environment: staging`, reject `continue-on-error: true`, require URL validation/timeouts, and require `staging-smoke-run-id` for production.

- [ ] **Step 2: Write failing runbook tests**

Import `WORKER_QUEUE_NAMES`, assert the runbooks mention both active queues, and reject `rq:queue:default`, `rq:queue:failed`, `HOSPITAL_AI_JWT_ALGORITHM=HS256`, `Object Versioning`, `non-current object versions`, `Existing cached documents`, and `docker system prune -f`.

- [ ] **Step 3: Run tests to verify failure**

Run:

```bash
cd app/backend
pytest tests/test_cd_operations_contracts.py -q
```

Expected: failures identify every pre-fix workflow and documentation defect.

- [ ] **Step 4: Commit the red tests**

```bash
git add app/backend/tests/test_cd_operations_contracts.py
git commit -m "test: cover CD and operations review findings"
```

### Task 2: Make CD verification and smoke testing fail closed

**Files:**
- Modify: `.github/workflows/cd.yml`
- Test: `app/backend/tests/test_cd_operations_contracts.py`

**Interfaces:**
- Consumes: `source-sha`, `image-tag`, optional staging deploy hook, staging environment variable `DOKPLOY_APP_URL`.
- Produces: validated `steps.verify.outputs.digest`, blocking staging smoke result, production handoff evidence containing `staging_smoke_run_id`.

- [ ] **Step 1: Replace manifest parsing**

Use:

```bash
MANIFEST_JSON=$(docker buildx imagetools inspect "$IMAGE_REF" --format '{{json .Manifest}}')
DIGEST=$(jq -er '.digest | select(test("^sha256:[0-9a-f]{64}$"))' <<<"$MANIFEST_JSON")
```

Then validate the digest again with Bash and write it to `$GITHUB_OUTPUT`. Do not provide a fallback value.

- [ ] **Step 2: Fail production configuration before evidence**

Move the production deploy-hook check before the deploy step. Emit the release record only when `steps.deploy.outputs.deployed == 'true'`.

- [ ] **Step 3: Add manual production staging evidence**

Add optional workflow-dispatch input `staging-smoke-run-id`. For production, require it to match `^[0-9]+$`; for staging, normalize it to an empty value. Include the ID and GitHub Actions run URL in the deploy payload and release summary.

- [ ] **Step 4: Bind and harden the smoke job**

Set the job's environment to `staging`, export `DOKPLOY_APP_URL`, reject empty/non-HTTP(S) values, normalize the trailing slash, and call curl with `--connect-timeout 10 --max-time 20`. Remove `continue-on-error: true`.

- [ ] **Step 5: Run focused tests**

```bash
cd app/backend
pytest tests/test_cd_operations_contracts.py -q
```

Expected: workflow-related tests pass while runbook tests still fail.

- [ ] **Step 6: Parse workflow YAML**

```bash
python - <<'PY'
from pathlib import Path
import yaml
yaml.safe_load(Path('.github/workflows/cd.yml').read_text(encoding='utf-8'))
print('cd.yml syntax OK')
PY
```

Expected: `cd.yml syntax OK`.

- [ ] **Step 7: Commit**

```bash
git add .github/workflows/cd.yml
git commit -m "fix: harden release evidence and staging smoke checks"
```

### Task 3: Correct queue, JWKS, R2, backup, and disk runbooks

**Files:**
- Modify: `docs/10-deployment/ci-cd.md`
- Modify: `docs/11-operations/operations-guide.md`
- Modify: `docs/11-operations/monitoring-guide.md`
- Modify: `docs/11-operations/incident-response.md`
- Modify: `docs/11-operations/troubleshooting.md`
- Test: `app/backend/tests/test_cd_operations_contracts.py`

**Interfaces:**
- Consumes: workflow behavior from Task 2 and queue constants from `run_worker.py`.
- Produces: operator procedures that match the implemented system.

- [ ] **Step 1: Correct CI/CD documentation**

Document Buildx manifest digest extraction, blocking staging smoke behavior, exact retry sleeps, `staging` environment variable scope, and the manual `staging-smoke-run-id` production approval evidence boundary.

- [ ] **Step 2: Correct PostgreSQL and R2 recovery procedures**

State that an external scheduler must run backups, protect/remove plaintext dumps, require off-host R2 copies with timestamped keys, and state that R2 mode has no automatic local-document failover.

- [ ] **Step 3: Correct queue monitoring**

Use `document-indexing` and `cdss-analysis` in every command and table. Use `FailedJobRegistry` per queue for failed counts.

- [ ] **Step 4: Correct JWKS and disk incident procedures**

Require fail-closed recovery of the configured JWKS endpoint, explicitly prohibit emergency signing-algorithm changes, and replace blanket Docker pruning with inspection plus targeted image pruning.

- [ ] **Step 5: Run focused tests**

```bash
cd app/backend
pytest tests/test_cd_operations_contracts.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add docs/10-deployment/ci-cd.md docs/11-operations
git commit -m "docs: align operations runbooks with runtime behavior"
```

### Task 4: Final verification and PR update

**Files:**
- Verify all modified files.

**Interfaces:**
- Consumes: completed Tasks 1-3.
- Produces: one updated PR head SHA with fresh CI.

- [ ] **Step 1: Run the focused contract suite**

```bash
cd app/backend
pytest tests/test_cd_operations_contracts.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run repository deployment-contract tests**

```bash
cd app/backend
pytest tests/test_deployment_contracts.py -q
```

Expected: all tests pass.

- [ ] **Step 3: Review the diff for unsupported claims and secrets**

```bash
git diff --check
git grep -nE 'unknown|rq:queue:default|rq:queue:failed|HOSPITAL_AI_JWT_ALGORITHM=HS256|non-current object versions|docker system prune -f' -- .github docs app/backend/tests
```

Expected: no defect-pattern matches except explicit negative assertions inside the regression test.

- [ ] **Step 4: Push the existing PR branch**

```bash
git push origin feat/deployment-tasks-8-9
```

- [ ] **Step 5: Verify GitHub state**

Confirm PR #85 points to the new head SHA and inspect the fresh CI run. Do not report completion until the workflow and contract checks are green, or explicitly report any still-running/external checks.
