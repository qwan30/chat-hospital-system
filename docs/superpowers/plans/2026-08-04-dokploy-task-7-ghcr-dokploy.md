# Dokploy Task 7: GitHub-Built Image and Staging Deployment Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Make staging use one immutable backend image built by GitHub Actions, published to GHCR, and consumed by Dokploy without building from the VPS source clone.

**Execution status (2026-08-04):** Repository-side implementation complete on
`feat/deployment-task-7-ghcr-dokploy`. Focused verification is green; external
Dokploy/VPS/GHCR runtime evidence remains pending and no deployment is claimed.

**Architecture:** infra/docker-compose.yml is the image-only Dokploy contract. GitHub Actions tests, builds, scans, and publishes ghcr.io/<owner>/hospital-ai-backend:sha-<7-lowercase-hex>; the existing CD workflow hands that exact identity to Dokploy. infra/docker-compose.local-build.yml is the only build-enabled Compose file added for the Task 7 deployment contract and is developer-only. The pre-existing root and backend Compose files remain explicitly local-only and are never Dokploy/VPS inputs.

**Tech Stack:** Docker Compose, Docker Buildx, GitHub Actions, GHCR, Dokploy hooks, Python 3.11, pytest, Ruff, Markdown deployment contracts, GitNexus.

## Global Constraints

- Keep Vercel as the frontend host and Dokploy/Traefik as the only public ingress for the VPS backend.
- infra/docker-compose.yml contains no build stanza and requires an explicit BACKEND_IMAGE value.
- Backend and worker resolve to the same immutable BACKEND_IMAGE reference.
- Release tags use sha-<7-lowercase-hex> or an immutable digest; latest is never a release identity.
- The Task 7 local build override is infra/docker-compose.local-build.yml; the
  pre-existing root/backend Compose files are explicitly local-only; the VPS
  staging runbook never uses any of these build-enabled files.
- The deployed frontend API base is https://<api-host>/api/v1; local development keeps VITE_API_URL=/api through the Vite proxy.
- Gemini remains the default provider; DeepSeek is explicit configuration, not automatic fallback; Ollama is not part of the VPS stack.
- Memory ceilings are PostgreSQL 768m, Redis 256m, backend 768m, and worker 1024m.
- The Docker build context excludes .git, virtual environments, caches, tests/output, local storage, datasets, uploads, logs, .env files, and non-runtime documentation.
- Repository checks prove static contracts only. VPS, Dokploy, GHCR credentials, DNS, R2, migrations, public health, smoke tests, backup/restore, and production approval remain UNVERIFIED without operator evidence.
- Use synthetic or de-identified values only; never add credentials, real patient data, or provider secrets.
- Do not provision external infrastructure, run external migrations, push the branch, open a PR, or merge it.

---

## File Map

| File | Responsibility |
|---|---|
| app/backend/tests/test_deployment_contracts.py | RED/GREEN fixtures for image-only Compose, immutable input, memory ceilings, local build separation, and build-context exclusions. |
| app/backend/scripts/verify_deployment_contract.py | Deterministic repository validator for Task 7 invariants. |
| infra/docker-compose.yml | Dokploy production/staging stack using an explicit immutable image and service memory ceilings. |
| infra/docker-compose.local-build.yml | Developer-only Compose override that adds the backend build context and local image name. |
| docker-compose.yml; app/backend/docker-compose.yml | Pre-existing local development stacks; explicitly marked local-only and excluded from Dokploy/VPS deployment. |
| app/backend/.dockerignore | Keeps the GitHub Docker build context limited to runtime inputs. |
| .github/workflows/ci.yml | Supplies a synthetic image to Compose validation while preserving the GitHub image pipeline. |
| .github/workflows/security-scan.yml | Scans the current default-branch immutable short-SHA image instead of an obsolete floating path. |
| app/backend/tests/test_ci_workflow.py | Structural regression test for the synthetic Compose validation image. |
| docs/10-deployment/deployment-guide.md | Control plane, local override, API base, memory budget, and migration sequence. |
| docs/10-deployment/ci-cd.md | Image, digest, source SHA, workflow ID, and Dokploy hook semantics. |
| docs/10-deployment/vps-operations.md | Image pull, migration, rollout, health, smoke, and evidence capture without source builds. |
| docs/10-deployment/rollback-plan.md | Immutable image rollback and migration compatibility instructions. |
| docs/10-deployment/release-checklist.md | Static repository gates and external staging evidence gates. |
| .superpowers/sdd/deployment-task-7-report.md | Task 7 repository-side completion report with the external-evidence boundary. |
| docs/superpowers/plans/2026-08-04-dokploy-task-7-ghcr-dokploy.md | This executable plan and progress checklist. |

---

### Task 1: Add failing contract tests for the image-only production stack

**Files:**
- Modify: app/backend/tests/test_deployment_contracts.py
- Test fixture inputs: infra/docker-compose.yml, infra/docker-compose.local-build.yml, docker-compose.yml, app/backend/docker-compose.yml, app/backend/.dockerignore

**Interfaces:**
- Consumes: the existing _copy_deployment_contract_fixture, _run_validator, and temporary repository fixture pattern.
- Produces: named cases for production_build, required_backend_image, floating_backend_image, image_mismatch, missing_memory_limit, missing_local_build_override, and dockerignore_contract.

- [ ] Step 1: Extend the copied fixture paths.

Add infra/docker-compose.local-build.yml and app/backend/.dockerignore to REQUIRED_DEPLOYMENT_PATHS so the validator fixture represents the complete Task 7 contract.

- [ ] Step 2: Add the valid production-stack assertions.

Add a test that reads the three Task 7 files and asserts that production has no build key, contains the required BACKEND_IMAGE interpolation, contains the four exact mem_limit values, and uses the same image contract in backend and worker. Assert that the local override contains build, the backend context, and hospital-ai-backend:local. Assert that .dockerignore contains .git, .venv/, __pycache__/, tests/, local_storage/, uploads/, *.log, and .env*.

~~~python
def test_task_7_production_compose_is_image_only_and_bounded():
    production = (REPO_ROOT / "infra/docker-compose.yml").read_text(encoding="utf-8")
    local = (REPO_ROOT / "infra/docker-compose.local-build.yml").read_text(encoding="utf-8")
    dockerignore = (REPO_ROOT / "app/backend/.dockerignore").read_text(encoding="utf-8")

    assert "\n    build:" not in production
    assert "BACKEND_IMAGE:?" in production
    assert production.count("image: ${BACKEND_IMAGE:?") == 2
    assert "mem_limit: 768m" in production
    assert "mem_limit: 256m" in production
    assert "mem_limit: 1024m" in production
    assert "build:" in local
    assert "context: ../app/backend" in local
    assert "hospital-ai-backend:local" in local
    for entry in (".git", ".venv/", "__pycache__/", "tests/", "local_storage/", "uploads/", "*.log", ".env*"):
        assert entry in dockerignore
~~~

- [ ] Step 3: Add invalid fixture tests for every new validator invariant.

Use _copy_deployment_contract_fixture(tmp_path) and mutate only the copied production contract for these cases:

~~~python
@pytest.mark.parametrize(
    ("mutator", "expected_code"),
    [
        (
            lambda text: text.replace(
                "    image: ${BACKEND_IMAGE:?",
                "    build:\n      context: ../app/backend\n    image: ${BACKEND_IMAGE:?",
                1,
            ),
            "production_build",
        ),
        (
            lambda text: text.replace(
                "image: ${BACKEND_IMAGE:?",
                "image: ghcr.io/example/hospital-ai-backend:sha-0000000",
                1,
            ),
            "required_backend_image",
        ),
        (
            lambda text: text.replace(
                "BACKEND_IMAGE:?BACKEND_IMAGE must be set to an immutable GHCR image reference",
                "BACKEND_IMAGE:-ghcr.io/example/hospital-ai-backend:latest",
            ),
            "floating_backend_image",
        ),
        (lambda text: text.replace("mem_limit: 768m", "# mem_limit removed", 1), "missing_memory_limit"),
    ],
)
def test_task_7_validator_rejects_production_contract_mutations(tmp_path, mutator, expected_code):
    _copy_deployment_contract_fixture(tmp_path)
    compose_path = tmp_path / "infra/docker-compose.yml"
    compose_path.write_text(mutator(compose_path.read_text(encoding="utf-8")), encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert any(item["code"] == expected_code for item in payload["violations"])
~~~

Add separate tests for deleting the local override, changing only the worker image expression, and removing one required .dockerignore entry. These tests must fail before the validator implementation changes.

- [ ] Step 4: Run only the new tests to verify the RED state.

Run from the repository root:

~~~powershell
python -m pytest --noconftest app/backend/tests/test_deployment_contracts.py -k "task_7" -v
~~~

Expected result: the new tests fail because the current production Compose still has a build stanza, a floating default, and no Task 7 resource/context contract.

- [ ] Step 5: Do not commit the RED-only state.

Commit the tests together with the GREEN validator implementation in Task 2 after the focused suite passes and GitNexus change detection is clean.

---

### Task 2: Implement the repository deployment validator invariants

**Files:**
- Modify: app/backend/scripts/verify_deployment_contract.py
- Test: app/backend/tests/test_deployment_contracts.py

**Interfaces:**
- Consumes: production Compose text, local override text, backend .dockerignore, and existing deployment documentation loaded by validate_deployment_contract(root).
- Produces: deterministic ContractViolation entries with the codes defined in Task 1 while preserving exit code 0 for valid repositories and 2 for invalid repositories.

- [ ] Step 1: Run GitNexus upstream impact before changing validate_deployment_contract.

Call GitNexus impact for validate_deployment_contract in app/backend/scripts/verify_deployment_contract.py with direction=upstream, repo=chat-hospital-system, summaryOnly=true, and includeTests=true. Record direct callers, affected processes, and risk. If risk is HIGH or CRITICAL, stop and review the blast radius before editing.

- [ ] Step 2: Add the new required files to REQUIRED_FILES.

Require infra/docker-compose.local-build.yml and app/backend/.dockerignore. Read them into local_build and dockerignore beside the existing deployment contracts. Missing files use the existing missing_file behavior.

- [ ] Step 3: Add a service-block helper and static Task 7 checks.

Add this private helper:

~~~python
def _compose_service_block(compose: str, service: str) -> str:
    pattern = rf"(?ms)^  {re.escape(service)}:\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)"
    match = re.search(pattern, compose)
    return match.group("body") if match else ""
~~~

Add _validate_task_7_compose_contract(compose, local_build, dockerignore, violations) and call it from validate_deployment_contract after the existing private-port checks. It must:

1. Add production_build when a line matching ^    build: exists in infra/docker-compose.yml.
2. Add required_backend_image unless both backend and worker contain image: ${BACKEND_IMAGE:?BACKEND_IMAGE must be set to an immutable GHCR image reference}.
3. Add floating_backend_image when production contains latest, IMAGE_TAG, IMAGE_PREFIX, or a ${BACKEND_IMAGE:-...} fallback.
4. Add image_mismatch when backend and worker image lines are not identical.
5. Add missing_memory_limit for the exact pairs postgres=768m, redis=256m, backend=768m, and worker=1024m.
6. Add missing_local_build_override unless the local file contains backend and worker build entries, context: ../app/backend, dockerfile: Dockerfile, and hospital-ai-backend:local.
7. Add dockerignore_contract for every missing entry from .git, .venv/, venv/, __pycache__/, .pytest_cache/, .ruff_cache/, .mypy_cache/, tests/, data/, local_storage/, uploads/, *.log, coverage/, htmlcov/, dist/, build/, docs/, and .env*.

The production image check must not require a registry network call. Compose fails configuration when BACKEND_IMAGE is omitted; the validator proves the repository contains the required interpolation rather than a fallback.

- [ ] Step 4: Run the focused suite to reach GREEN.

~~~powershell
python -m pytest --noconftest app/backend/tests/test_deployment_contracts.py -k "task_7 or deployment_contract" -v
~~~

Expected result: all Task 7 and existing deployment-contract tests pass.

- [ ] Step 5: Run the standalone validator with JSON output.

~~~powershell
python app/backend/scripts/verify_deployment_contract.py --json
~~~

Expected result: JSON contains valid=true, an empty violations list, and process exit code 0.

- [ ] Step 6: Commit the validator and tests as one tested unit.

Before committing, stage only the validator and deployment tests, run GitNexus detect_changes with scope=staged, repo=chat-hospital-system, and worktree=D:\projects\chatbot-hospital-system, and confirm the result is limited to the validator/tests with no unexpected execution flow.

~~~powershell
git add app/backend/scripts/verify_deployment_contract.py app/backend/tests/test_deployment_contracts.py
git commit -m "test: enforce Task 7 image deployment contract"
~~~

---

### Task 3: Make production Compose image-only and add the local build boundary

**Files:**
- Modify: infra/docker-compose.yml
- Create: infra/docker-compose.local-build.yml
- Create: app/backend/.dockerignore
- Test: app/backend/tests/test_deployment_contracts.py

**Interfaces:**
- Consumes: validator contract from Task 2 and the existing backend Dockerfile copy list.
- Produces: a production Compose file Dokploy consumes with an immutable image and a separate local developer override.

- [ ] Step 1: Replace the production backend image fallback.

Replace backend and worker image values with this identical required expression:

~~~yaml
image: ${BACKEND_IMAGE:?BACKEND_IMAGE must be set to an immutable GHCR image reference}
~~~

Remove the production backend build block and comments describing a latest or other fallback. Keep expose 8000, the /api/v1/health healthcheck, the shared storage volume, the real worker entrypoint, and add a worker process-liveness healthcheck for `--wait` rollout gating.

- [ ] Step 2: Add explicit service memory ceilings.

Add these keys directly under the corresponding services:

~~~yaml
postgres:
  mem_limit: 768m
redis:
  mem_limit: 256m
backend:
  mem_limit: 768m
worker:
  mem_limit: 1024m
~~~

Keep PostgreSQL, Redis, and backend without host ports mappings. Do not add an observability service or host port.

- [ ] Step 3: Create the developer-only Compose override.

Create infra/docker-compose.local-build.yml:

~~~yaml
# Developer-only override. Never use this file for Dokploy/VPS staging.
services:
  backend:
    image: hospital-ai-backend:local
    build:
      context: ../app/backend
      dockerfile: Dockerfile
  worker:
    image: hospital-ai-backend:local
    build:
      context: ../app/backend
      dockerfile: Dockerfile
~~~

The local command sets BACKEND_IMAGE=hospital-ai-backend:local because Compose interpolates the required base-file variable before applying the override:

~~~powershell
$env:BACKEND_IMAGE = "hospital-ai-backend:local"
docker compose -f infra/docker-compose.yml -f infra/docker-compose.local-build.yml config --quiet
docker compose -f infra/docker-compose.yml -f infra/docker-compose.local-build.yml build backend worker
~~~

- [ ] Step 4: Create app/backend/.dockerignore.

Leave pyproject.toml, src/, alembic/, and alembic.ini available to the Dockerfile. Add:

~~~text
.git
.gitignore
.env*
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.mypy_cache/
tests/
data/
local_storage/
uploads/
*.log
coverage/
htmlcov/
dist/
build/
docs/
~~~

- [ ] Step 5: Render production and local configurations with synthetic values.

Run from the repository root without contacting GHCR or a VPS:

~~~powershell
$env:BACKEND_IMAGE = "ghcr.io/example/hospital-ai-backend:sha-0000000"
$env:POSTGRES_PASSWORD = "synthetic-only"
$env:HOSPITAL_AI_R2_ENDPOINT = "https://r2.example.invalid"
$env:HOSPITAL_AI_R2_BUCKET = "synthetic-bucket"
$env:HOSPITAL_AI_GEMINI_API_KEY = "synthetic-key"
$env:HOSPITAL_AI_JWT_ISSUER = "https://issuer.example.invalid"
$env:HOSPITAL_AI_JWKS_URL = "https://issuer.example.invalid/.well-known/jwks.json"
docker compose -f infra/docker-compose.yml config --quiet
$env:BACKEND_IMAGE = "hospital-ai-backend:local"
docker compose -f infra/docker-compose.yml -f infra/docker-compose.local-build.yml config --quiet
~~~

Expected result: both commands exit 0; the first rendered config has no build section and the second adds builds only for backend and worker.

- [ ] Step 6: Run the Compose and validator regression tests.

~~~powershell
python -m pytest --noconftest app/backend/tests/test_deployment_contracts.py -k "deployment_files or task_7 or deployment_contract" -v
python app/backend/scripts/verify_deployment_contract.py
~~~

Expected result: selected tests pass and the validator exits 0.

---

### Task 4: Keep GitHub as the image construction authority

**Files:**
- Modify: .github/workflows/ci.yml
- Modify: app/backend/tests/test_ci_workflow.py

**Interfaces:**
- Consumes: required BACKEND_IMAGE interpolation from production Compose.
- Produces: CI Compose validation with a synthetic immutable-shaped image while preserving existing test, migration, scan, push, artifact, and CD gates.

- [ ] Step 1: Add a structural CI test before changing the workflow.

Parse ci.yml, retrieve the validate-observability job, and assert that its job-level env.BACKEND_IMAGE equals ghcr.io/example/hospital-ai-backend:sha-0000000. Assert that both Compose validation steps still run config --quiet and that docker-push keeps the existing backend, migration, frontend, and observability dependencies.

~~~python
def test_compose_validation_uses_synthetic_required_backend_image():
    workflow_path = Path(__file__).resolve().parents[3] / ".github/workflows/ci.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    validation_job = workflow["jobs"]["validate-observability"]

    assert validation_job["env"]["BACKEND_IMAGE"] == "ghcr.io/example/hospital-ai-backend:sha-0000000"
    assert _step_by_name(validation_job, "Validate docker-compose.yml")["run"] == (
        "docker compose -f infra/docker-compose.yml config --quiet"
    )
    assert "docker compose -f infra/docker-compose.yml -f infra/docker-compose.observability.yml config --quiet" in (
        _step_by_name(validation_job, "Validate docker-compose.observability.yml")["run"]
    )
~~~

- [ ] Step 2: Run the new CI test in RED.

~~~powershell
python -m pytest --noconftest app/backend/tests/test_ci_workflow.py -k "synthetic_required_backend_image" -v
~~~

Expected result: failure because the job has no synthetic BACKEND_IMAGE yet.

- [ ] Step 3: Add the synthetic environment to the validation job.

Add this job-level block under validate-observability:

~~~yaml
env:
  BACKEND_IMAGE: ghcr.io/example/hospital-ai-backend:sha-0000000
~~~

Do not add registry credentials, runtime secrets, a build step, docker compose build, or a floating tag. Keep the Trivy HIGH/CRITICAL scan blocking, and keep docker-push as the only image construction/publication path.

- [ ] Step 4: Run the CI structural tests in GREEN.

~~~powershell
python -m pytest --noconftest app/backend/tests/test_ci_workflow.py -v
~~~

Expected result: all CI workflow structure tests pass.

- [ ] Step 5: Commit the CI contract.

Stage the workflow and structural test, run GitNexus detect_changes with scope=staged, repo=chat-hospital-system, and worktree=D:\projects\chatbot-hospital-system, confirm only the validation job/test is affected, then commit:

~~~powershell
git add .github/workflows/ci.yml app/backend/tests/test_ci_workflow.py
git commit -m "ci: validate image-only staging compose contract"
~~~

---

### Task 5: Update deployment, migration, rollback, and evidence documentation

**Files:**
- Modify: docs/10-deployment/deployment-guide.md
- Modify: docs/10-deployment/ci-cd.md
- Modify: docs/10-deployment/vps-operations.md
- Modify: docs/10-deployment/rollback-plan.md
- Modify: docs/10-deployment/release-checklist.md
- Create: .superpowers/sdd/deployment-task-7-report.md

**Interfaces:**
- Consumes: Compose and CI contracts from Tasks 3–4 and existing Task 5–6 external-evidence wording.
- Produces: one operator-readable release sequence with no contradictory source-build path and no false runtime/deployment claim.

- [ ] Step 1: Correct the deployment guide control plane and API base.

In deployment-guide.md:
1. change the Vercel example to VITE_API_URL=https://api.<domain>/api/v1;
2. add a Task 7 image control-plane subsection stating that GitHub Actions tests/builds/scans/pushes, CD sends the immutable identity, Dokploy injects BACKEND_IMAGE, and the VPS source clone is not a normal build input;
3. document the developer-only local override with BACKEND_IMAGE=hospital-ai-backend:local and state it is not a VPS command;
4. add the exact four-service memory table and combined 2.75 GiB ceiling;
5. add the controlled migration order: verify image/env, pull, run alembic upgrade head as a one-off candidate container, roll backend/worker on the same image, wait for health, run synthetic smoke checks, and record candidate evidence;
6. state that an immutable GHCR tag or digest is required and a floating tag is not a release.

- [ ] Step 2: Bind ci-cd.md to the same image identity.

Retain the existing immutable tag, digest, source SHA, artifact, workflow ID, staging pending, and production fail-closed contracts. Add that migration, backend, and worker all use the exact image from the Dokploy payload, and that a successful hook response is only handoff acknowledgement. State that no VPS git pull, source build, or docker compose build belongs to the normal release path.

- [ ] Step 3: Replace the ambiguous VPS source-build path with an image rollout sequence.

Add a section after GHCR access in vps-operations.md with this order:

~~~bash
export BACKEND_IMAGE="ghcr.io/<GHCR_NAMESPACE>/hospital-ai-backend:sha-<CANDIDATE_SHORT_SHA>"
docker manifest inspect "$BACKEND_IMAGE"
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" pull postgres redis backend worker
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" run --rm --no-deps backend alembic upgrade head
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" up -d postgres redis backend worker
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" ps
docker stats --no-stream
curl --fail --silent --show-error "https://<API_DOMAIN>/api/v1/health"
~~~

Explain that Dokploy normally performs the equivalent pull/migration/rollout, migration and both application services use the same candidate image, worker health is process-gated, docker compose build and the local override are developer-only, and the operator records migration revision, health, smoke, RAM/swap/disk, and docker stats against the full candidate SHA plus its seven-character image suffix. Commands use placeholders and do not prove external state.

- [ ] Step 4: Align rollback and release checklist language.

In rollback-plan.md, state that rollback changes the immutable image reference for backend and worker together, never rebuilds on the VPS, and must respect migration compatibility. In release-checklist.md, add gates for image-only production Compose, exact BACKEND_IMAGE, the four memory ceilings, candidate migration before rollout, and operator runtime evidence. Keep UNVERIFIED and production-blocked wording.

- [ ] Step 5: Create the Task 7 report after verification.

Create .superpowers/sdd/deployment-task-7-report.md with repository-side status, a list of implemented contracts, an exact command/result table populated from Task 6, and an external-boundary section saying Dokploy, VPS, GHCR credentials, DNS, R2, migrations, public health, worker/SSE smoke tests, backup/restore, and production approval remain UNVERIFIED until candidate-specific operator evidence exists.

- [ ] Step 6: Run documentation contract checks.

~~~powershell
python app/backend/scripts/verify_deployment_contract.py --json
git diff --check
rg -n "git pull|docker compose.*build|latest fallback|VITE_API_URL=https://[^ ]+$" docs/10-deployment infra/docker-compose.yml
~~~

Expected result: validator is valid, whitespace is clean, and no normal VPS source-build instruction or deployed API base missing /api/v1 remains. Existing explanatory uses of latest must be reviewed as forbidden-release wording, not removed blindly.

---

### Task 6: Run full verification, security review, and GitNexus change review

**Files:**
- Review all changed files from Tasks 1–5.
- No new source files beyond those named in this plan.

**Interfaces:**
- Consumes: all Task 7 repository changes and test artifacts.
- Produces: a clean, committed branch with no claims of external deployment.

- [ ] Step 1: Run focused tests and formatting checks.

~~~powershell
python -m pytest --noconftest app/backend/tests/test_deployment_contracts.py app/backend/tests/test_ci_workflow.py -v
ruff check app/backend/scripts/verify_deployment_contract.py app/backend/tests/test_deployment_contracts.py app/backend/tests/test_ci_workflow.py
ruff format --check app/backend/scripts/verify_deployment_contract.py app/backend/tests/test_deployment_contracts.py app/backend/tests/test_ci_workflow.py
~~~

Expected result: all focused tests pass and Ruff reports no violations or formatting drift.

- [ ] Step 2: Run the repository validator and Compose render gate with synthetic values.

~~~powershell
$env:BACKEND_IMAGE = "ghcr.io/example/hospital-ai-backend:sha-0000000"
$env:POSTGRES_PASSWORD = "synthetic-only"
$env:HOSPITAL_AI_R2_ENDPOINT = "https://r2.example.invalid"
$env:HOSPITAL_AI_R2_BUCKET = "synthetic-bucket"
$env:HOSPITAL_AI_GEMINI_API_KEY = "synthetic-key"
$env:HOSPITAL_AI_JWT_ISSUER = "https://issuer.example.invalid"
$env:HOSPITAL_AI_JWKS_URL = "https://issuer.example.invalid/.well-known/jwks.json"
docker compose -f infra/docker-compose.yml config --quiet
docker compose -f infra/docker-compose.yml -f infra/docker-compose.observability.yml config --quiet
python app/backend/scripts/verify_deployment_contract.py --json
~~~

Expected result: both Compose configurations render, validator JSON is valid, and no external registry or VPS is contacted.

- [ ] Step 3: Run the relevant Task 5–6 backend regressions.

~~~powershell
python -m pytest --noconftest app/backend/tests/test_deployment_contracts.py app/backend/tests/test_ci_workflow.py app/backend/tests/test_storage_contracts.py -v
~~~

Expected result: all selected tests pass. Preserve any unrelated existing failure output and do not claim the full gate is green if one occurs.

- [ ] Step 4: Inspect the diff for security and contradictions.

~~~powershell
git diff --check
rg -n "(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|password\s*[:=]\s*[^<\s]+)" app/backend/.dockerignore infra docs/10-deployment .github/workflows app/backend/scripts/verify_deployment_contract.py
rg -n "latest|build:|docker compose.*build|git pull|VITE_API_URL" infra/docker-compose.yml infra/docker-compose.local-build.yml docker-compose.yml app/backend/docker-compose.yml docs/10-deployment .github/workflows/ci.yml
~~~

Review every hit manually. Production Compose has no build or latest; the Task 7
local override and the two explicitly marked pre-existing local Compose files
may contain build; workflow publication remains SHA-tagged; docs may mention
latest only as a forbidden release identity; deployed API examples include
/api/v1.

- [ ] Step 5: Run GitNexus detect_changes before each implementation commit and before the final commit.

For staged changes, call mcp__gitnexus__detect_changes with scope=staged, repo=chat-hospital-system, and worktree=D:\projects\chatbot-hospital-system. Review changed symbols, affected processes, and risk. Expected result is low risk for Compose/docs/CI and validator/test-only impact for Python edits. Restore tooling-only AGENTS.md or CLAUDE.md statistics if GitNexus analysis rewrites them.

- [ ] Step 6: Compare the final branch and commit remaining docs/report.

~~~powershell
git diff --stat main...HEAD
git status --short
git diff --check
git add infra/docker-compose.yml infra/docker-compose.local-build.yml app/backend/.dockerignore docs/10-deployment .superpowers/sdd/deployment-task-7-report.md
git commit -m "feat: route Task 7 staging through GHCR and Dokploy"
~~~

Do not push, open a PR, merge, or claim a live deployment. Report branch, commit(s), verification commands, and remaining external evidence boundary.

---

## Plan Self-Review

- Spec R1 is covered by Tasks 1–3: required immutable image, no production build, same backend/worker image, private ports, and no floating default.
- Spec R2 is covered by Task 3: explicit local override and developer-only command; pre-existing root/backend Compose files are marked local-only and validated as non-Dokploy inputs.
- Spec R3 is covered by Tasks 4–5: existing GitHub image pipeline remains authoritative, Compose CI receives a synthetic image, Trivy HIGH/CRITICAL findings block the image job, and CD/handoff remains immutable.
- Spec R4 is covered by Task 5: pull, one-off migration, same-image rollout, backend/worker health (including worker process liveness), smoke, and candidate evidence sequence.
- Spec R5 is covered by Tasks 1–3 and Task 5: exact memory ceilings, build-context exclusions, and no default observability overlay.
- Spec R6 is covered by Task 5 and existing validator tests: Gemini default, explicit DeepSeek, no Ollama, /api/v1, explicit CORS, and frontend secret isolation.
- Spec R7 is covered by Task 5 report and every verification step: no repository check claims external runtime proof.
- Placeholder scan: no unresolved planning markers remain; angle-bracket values appear only in documented operator commands where environment-specific values are required.
- Type and naming consistency: the validator entry point remains `validate_deployment_contract(root: Path | None, backend_image: str | None = None) -> list[ContractViolation]`; helper names and violation codes are defined in Task 2 and used consistently in Tasks 1 and 6.
