from __future__ import annotations
from typing import Optional

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from hospital_ai.workers import run_worker

REPO_ROOT = Path(__file__).resolve().parents[3]
DEPLOYMENT_VALIDATOR = REPO_ROOT / "app" / "backend" / "scripts" / "verify_deployment_contract.py"
REQUIRED_DEPLOYMENT_PATHS = [
    ".github/workflows/ci.yml",
    ".github/workflows/cd.yml",
    ".github/workflows/rollback.yml",
    "infra/docker-compose.yml",
    "infra/docker-compose.local-build.yml",
    "docker-compose.yml",
    "app/backend/docker-compose.yml",
    "app/backend/.dockerignore",
    "docs/10-deployment/deployment-guide.md",
    "docs/10-deployment/env-variables.md",
    "docs/10-deployment/ci-cd.md",
    "docs/10-deployment/release-checklist.md",
    "docs/10-deployment/vps-operations.md",
    "docs/10-deployment/vps-preflight-evidence.md",
]
PENDING_CANDIDATE_SHA_ROW = (
    "| PENDING — operator evidence required | Candidate SHA pinned | "
    "`git rev-parse --verify <CANDIDATE_SHA>` | Candidate commit resolves exactly once | "
    "`<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |"
)
VERIFIED_CANDIDATE_SHA_ROW = (
    "| VERIFIED | Candidate SHA pinned | `git rev-parse --verify <CANDIDATE_SHA>` | "
    "Candidate commit resolves exactly once | `<operator-recorded-value>` | "
    "`<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |"
)
PENDING_SECRET_KEY_ROW = (
    "| PENDING — operator evidence required | Secret key presence only | "
    "`printf '%s\\n' POSTGRES_PASSWORD "
    "HOSPITAL_AI_GEMINI_API_KEY HOSPITAL_AI_R2_ENDPOINT HOSPITAL_AI_R2_BUCKET "
    "HOSPITAL_AI_R2_ACCESS_KEY_ID HOSPITAL_AI_R2_SECRET_ACCESS_KEY "
    "HOSPITAL_AI_JWT_ISSUER HOSPITAL_AI_JWKS_URL HOSPITAL_AI_JWT_AUDIENCE` | "
    "Required key names are present in Dokploy; no secret values are exposed | "
    "`<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |"
)
MALFORMED_SECRET_KEY_ROW = (
    "| PENDING — operator evidence required | Secret key presence only | "
    "`printf '%s\\n' HOSPITAL_AI_DATABASE_URL` | malformed row | "
    "`<operator-recorded-value>` |"
)
FRONTEND_SECRET_PROOF_MARKER = "HOSPITAL_AI_DATABASE_URL"


def _load_deployment_validator():
    spec = importlib.util.spec_from_file_location("verify_deployment_contract", DEPLOYMENT_VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _copy_deployment_contract_fixture(tmp_path: Path) -> None:
    for relative in REQUIRED_DEPLOYMENT_PATHS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, target)


def _run_validator(repo_root: Path, backend_image: Optional[str] = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(DEPLOYMENT_VALIDATOR), "--repo-root", str(repo_root), "--json"]
    if backend_image is not None:
        command.extend(["--backend-image", backend_image])
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def test_worker_entrypoint_builds_all_supported_queues(monkeypatch):
    connection = object()
    created_queues: list[str] = []

    class FakeRedis:
        @staticmethod
        def from_url(url: str):
            assert url == "redis://example.test/0"
            return connection

    class FakeQueue:
        def __init__(self, name: str, *, connection):
            assert connection is not None
            created_queues.append(name)

    class FakeWorker:
        def __init__(self, queues, *, connection):
            self.queues = queues
            self.connection = connection

    monkeypatch.setattr(run_worker, "Redis", FakeRedis)
    monkeypatch.setattr(run_worker, "Queue", FakeQueue)
    monkeypatch.setattr(run_worker, "Worker", FakeWorker)

    worker = run_worker.build_worker(SimpleNamespace(redis_url="redis://example.test/0"))

    assert created_queues == [
        "document-indexing",
        "cdss-analysis",
        "document-generation-build",
    ]
    assert len(worker.queues) == 3
    assert worker.connection is connection


def test_worker_entrypoint_forwards_burst_mode(monkeypatch):
    calls: list[bool] = []

    class FakeWorker:
        def work(self, *, burst: bool):
            calls.append(burst)

    monkeypatch.setattr(run_worker, "get_settings", lambda: SimpleNamespace(redis_url="redis://example.test/0"))
    monkeypatch.setattr(run_worker, "build_worker", lambda settings: FakeWorker())

    run_worker.main(["--burst"])

    assert calls == [True]


def test_deployment_files_use_the_real_worker_entrypoint():
    infra_compose = (REPO_ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
    backend_compose = (REPO_ROOT / "app" / "backend" / "docker-compose.yml").read_text(encoding="utf-8")

    assert "hospital_ai.workers.run_worker" in infra_compose
    assert "hospital_ai.workers.queue" not in infra_compose
    assert "hospital_ai.workers.run_worker" in backend_compose
    assert "hospital_ai.workers.runner" not in backend_compose


def test_deployment_files_match_settings_environment_names():
    env_example = (REPO_ROOT / "app" / "backend" / ".env.example").read_text(encoding="utf-8")
    infra_compose = (REPO_ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
    env_docs = (REPO_ROOT / "docs" / "10-deployment" / "env-variables.md").read_text(encoding="utf-8")
    deployment_docs = (REPO_ROOT / "docs" / "10-deployment" / "deployment-guide.md").read_text(encoding="utf-8")

    assert "HOSPITAL_AI_ENVIRONMENT=local" in env_example
    assert "HOSPITAL_AI_ENV=local" not in env_example
    assert "HOSPITAL_AI_OLLAMA_BASE_URL" not in infra_compose
    assert "HOSPITAL_AI_CHAT_PROVIDER: ${HOSPITAL_AI_CHAT_PROVIDER:-gemini}" in infra_compose
    assert "HOSPITAL_AI_EMBEDDING_PROVIDER: ${HOSPITAL_AI_EMBEDDING_PROVIDER:-gemini}" in infra_compose
    assert "HOSPITAL_AI_R2_ENDPOINT" in infra_compose
    assert "HOSPITAL_AI_JWKS_URL" in infra_compose
    assert "HOSPITAL_AI_LLM_BASE_URL" not in infra_compose
    assert "HOSPITAL_AI_JWT_HMAC_SECRET" in infra_compose
    assert "HOSPITAL_AI_JWT_SECRET" not in infra_compose
    assert "HOSPITAL_AI_JWT_ISSUER" in infra_compose
    assert "HOSPITAL_AI_JWT_ALGORITHM: ${HOSPITAL_AI_JWT_ALGORITHM:-RS256}" in infra_compose
    assert "BACKEND_IMAGE" in infra_compose
    assert "nginx:" not in infra_compose
    assert '"5432:5432"' not in infra_compose
    assert '"6379:6379"' not in infra_compose
    assert '"8000:8000"' not in infra_compose
    assert "`HOSPITAL_AI_GEMINI_API_KEY`" in env_docs
    assert "`GEMINI_API_KEY`" not in env_docs
    assert "Dokploy DeepSeek value: `https://api.deepseek.com/v1`" in env_docs
    assert "Dokploy DeepSeek value: `deepseek-chat`" in env_docs
    assert "VITE_API_URL=https://api.example.com" in env_docs
    assert "HOSPITAL_AI_R2_ENDPOINT" in deployment_docs
    assert "HOSPITAL_AI_R2_BUCKET" in deployment_docs


def test_task_7_production_compose_is_image_only_and_bounded():
    production = (REPO_ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")

    assert "\n    build:" not in production
    assert "BACKEND_IMAGE:?" in production
    assert production.count("image: ${BACKEND_IMAGE:?") == 2
    assert "postgres:\n    image: pgvector/pgvector:pg16\n    mem_limit: 768m" in production
    assert "redis:\n    image: redis:7-alpine\n    mem_limit: 256m" in production
    assert "mem_limit: 768m" in production
    assert "mem_limit: 1024m" in production
    assert 'test: ["CMD", "python", "-c", "import os; os.kill(1, 0)"]' in production


def test_task_7_legacy_compose_files_are_explicitly_local_only():
    marker = "Developer-only local Compose file. Not for Dokploy/VPS deployment."

    for relative in ("docker-compose.yml", "app/backend/docker-compose.yml"):
        compose = (REPO_ROOT / relative).read_text(encoding="utf-8")
        assert marker in compose
        assert "build:" in compose


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
                "    image: ${BACKEND_IMAGE:?BACKEND_IMAGE must be set to an immutable GHCR image reference}",
                "    image: ghcr.io/example/hospital-ai-backend:sha-0000000",
                1,
            ),
            "required_backend_image",
        ),
        (
            lambda text: text.replace(
                "    image: ${BACKEND_IMAGE:?BACKEND_IMAGE must be set to an immutable GHCR image reference}",
                "    image: ${BACKEND_IMAGE:-ghcr.io/example/hospital-ai-backend:latest}",
                1,
            ),
            "floating_backend_image",
        ),
        (lambda text: text.replace("    mem_limit: 768m\n", "", 1), "missing_memory_limit"),
    ],
)
def test_task_7_validator_rejects_production_contract_mutations(tmp_path, mutator, expected_code):
    _copy_deployment_contract_fixture(tmp_path)
    compose_path = tmp_path / "infra" / "docker-compose.yml"
    compose_path.write_text(mutator(compose_path.read_text(encoding="utf-8")), encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert any(item["code"] == expected_code for item in payload["violations"])


def test_task_7_validator_rejects_unmarked_legacy_local_compose(tmp_path):
    _copy_deployment_contract_fixture(tmp_path)
    compose_path = tmp_path / "docker-compose.yml"
    compose_path.write_text(
        compose_path.read_text(encoding="utf-8").replace(
            "# Developer-only local Compose file. Not for Dokploy/VPS deployment.\n", ""
        ),
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert any(item["code"] == "local_compose_boundary" for item in payload["violations"])


def test_task_7_validator_rejects_missing_worker_healthcheck(tmp_path):
    _copy_deployment_contract_fixture(tmp_path)
    compose_path = tmp_path / "infra" / "docker-compose.yml"
    compose = compose_path.read_text(encoding="utf-8")
    healthcheck = (
        "    healthcheck:\n"
        '      test: ["CMD", "python", "-c", "import os; os.kill(1, 0)"]\n'
        "      interval: 30s\n"
        "      timeout: 10s\n"
        "      retries: 3\n"
        "      start_period: 20s\n"
    )
    assert compose.count(healthcheck) == 1
    compose_path.write_text(compose.replace(healthcheck, "", 1), encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert any(item["code"] == "missing_worker_healthcheck" for item in payload["violations"])


def test_backend_dockerfile_uses_cloud_run_port_contract():
    dockerfile = (REPO_ROOT / "app" / "backend" / "Dockerfile").read_text(encoding="utf-8")

    assert "--port ${PORT:-8000}" in dockerfile
    assert "os.getenv('PORT', '8000')" in dockerfile
    assert "os.getenv('HOSPITAL_AI_API_V1_PREFIX', '/api/v1')" in dockerfile


def test_backend_compose_uses_frontend_api_variable_name():
    backend_compose = (REPO_ROOT / "app" / "backend" / "docker-compose.yml").read_text(encoding="utf-8")
    frontend_dockerfile = (REPO_ROOT / "app" / "frontend" / "Dockerfile").read_text(encoding="utf-8")

    assert "VITE_API_URL" in backend_compose
    assert "NEXT_PUBLIC_API_URL" not in backend_compose
    assert "VITE_API_URL:" in backend_compose
    assert '"3000:8082"' in backend_compose
    assert "ARG VITE_API_URL" in frontend_dockerfile
    assert "ENV VITE_API_URL=${VITE_API_URL}" in frontend_dockerfile


def test_deployment_contract_validator_accepts_current_repository():
    validator = _load_deployment_validator()

    assert validator.validate_deployment_contract(REPO_ROOT) == []


@pytest.mark.parametrize(
    ("backend_image", "expected_valid"),
    [
        ("ghcr.io/example/hospital-ai-backend:sha-0000000", True),
        ("ghcr.io/example/hospital-ai-backend@sha256:" + "0" * 64, True),
        ("ghcr.io/example/hospital-ai-backend:latest", False),
        ("ghcr.io/example/hospital-ai-backend:sha-000000", False),
        ("docker.io/example/hospital-ai-backend:sha-0000000", False),
    ],
)
def test_deployment_contract_validator_checks_supplied_backend_image(backend_image, expected_valid):
    validator = _load_deployment_validator()

    violations = validator.validate_deployment_contract(REPO_ROOT, backend_image)

    assert bool(violations) is (not expected_valid)
    if not expected_valid:
        assert any(item.code == "invalid_backend_image" for item in violations)


def test_deployment_contract_cli_reports_invalid_fixture(tmp_path):
    _copy_deployment_contract_fixture(tmp_path)

    compose_path = tmp_path / "infra" / "docker-compose.yml"
    compose_path.write_text(
        compose_path.read_text(encoding="utf-8").replace(
            '    expose:\n      - "8000"', '    ports:\n      - "8000:8000"'
        ),
        encoding="utf-8",
    )
    env_docs_path = tmp_path / "docs" / "10-deployment" / "env-variables.md"
    env_docs_path.write_text(
        env_docs_path.read_text(encoding="utf-8").replace(
            "HOSPITAL_AI_CORS_ORIGINS=https://app.example.com",
            "HOSPITAL_AI_CORS_ORIGINS=*",
        ),
        encoding="utf-8",
    )
    evidence_path = tmp_path / "docs" / "10-deployment" / "vps-preflight-evidence.md"
    evidence_path.write_text(
        evidence_path.read_text(encoding="utf-8").replace(
            "| PENDING — operator evidence required | Vercel `VITE_API_URL` route |",
            "| VERIFIED | Vercel `VITE_API_URL` route |",
        ),
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["valid"] is False
    assert any(item["code"] == "public_port" for item in payload["violations"])
    assert any(item["code"] == "wildcard_cors" for item in payload["violations"])
    assert any(item["code"] == "invalid_preflight_status" for item in payload["violations"])
    assert any(item["code"] == "pending_preflight_row_required" for item in payload["violations"])


def test_deployment_contract_cli_rejects_frontend_secret_leak_fixture(tmp_path):
    _copy_deployment_contract_fixture(tmp_path)

    proof_source = REPO_ROOT / "app" / "frontend" / "src" / "lib" / "api-client.ts"
    proof_target = tmp_path / "app" / "frontend" / "src" / "proof-secret.ts"
    proof_target.parent.mkdir(parents=True, exist_ok=True)
    proof_target.write_text(
        f"{proof_source.read_text(encoding='utf-8')}\nexport const proofSecret = '{FRONTEND_SECRET_PROOF_MARKER}';\n",
        encoding="utf-8",
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["valid"] is False
    assert any(
        item["code"] == "frontend_secret_leak"
        and "proof-secret.ts" in item["message"]
        and FRONTEND_SECRET_PROOF_MARKER in item["message"]
        for item in payload["violations"]
    )


@pytest.mark.parametrize(
    ("mutator", "expected_codes"),
    [
        (
            lambda text: text.replace(
                PENDING_CANDIDATE_SHA_ROW,
                f"{PENDING_CANDIDATE_SHA_ROW}\n{VERIFIED_CANDIDATE_SHA_ROW}",
            ),
            {"invalid_preflight_status", "duplicate_preflight_check"},
        ),
        (
            lambda text: text.replace(
                "| PENDING — operator evidence required | CI Run ID recorded |",
                "| PENDING — operator evidence required | Candidate SHA pinned |",
            ),
            {"duplicate_preflight_check", "missing_preflight_row"},
        ),
        (
            lambda text: text.replace(
                PENDING_SECRET_KEY_ROW,
                MALFORMED_SECRET_KEY_ROW,
            ),
            {"invalid_preflight_row", "missing_preflight_row"},
        ),
    ],
)
def test_deployment_contract_cli_rejects_invalid_preflight_rows(tmp_path, mutator, expected_codes):
    _copy_deployment_contract_fixture(tmp_path)

    evidence_path = tmp_path / "docs" / "10-deployment" / "vps-preflight-evidence.md"
    evidence_path.write_text(mutator(evidence_path.read_text(encoding="utf-8")), encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    actual_codes = {item["code"] for item in payload["violations"]}
    assert expected_codes.issubset(actual_codes)


@pytest.mark.parametrize(
    ("relative_path", "original", "replacement"),
    [
        (
            "docs/10-deployment/env-variables.md",
            "HOSPITAL_AI_CORS_ORIGINS=https://app.example.com",
            "HOSPITAL_AI_CORS_ORIGINS=*",
        ),
        (
            "docs/10-deployment/vps-operations.md",
            "HOSPITAL_AI_CORS_ORIGINS=https://<VERCEL_FRONTEND_ORIGIN>",
            "HOSPITAL_AI_CORS_ORIGINS=*",
        ),
        (
            "docs/10-deployment/vps-preflight-evidence.md",
            "printf '%s\\n' \"HOSPITAL_AI_CORS_ORIGINS=https://<VERCEL_FRONTEND_ORIGIN>\"",
            "printf '%s\\n' \"HOSPITAL_AI_CORS_ORIGINS=*\"",
        ),
    ],
)
def test_deployment_contract_cli_rejects_wildcard_cors_in_task_6_docs(tmp_path, relative_path, original, replacement):
    _copy_deployment_contract_fixture(tmp_path)

    target = tmp_path / relative_path
    target.write_text(target.read_text(encoding="utf-8").replace(original, replacement), encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert any(item["code"] == "wildcard_cors" and item["path"] == relative_path for item in payload["violations"])
