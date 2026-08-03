from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from hospital_ai.workers import run_worker

REPO_ROOT = Path(__file__).resolve().parents[3]
DEPLOYMENT_VALIDATOR = REPO_ROOT / "app" / "backend" / "scripts" / "verify_deployment_contract.py"


def _load_deployment_validator():
    spec = importlib.util.spec_from_file_location("verify_deployment_contract", DEPLOYMENT_VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
    ]
    assert len(worker.queues) == 2
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


def test_deployment_contract_cli_reports_invalid_fixture(tmp_path):
    required_paths = [
        ".github/workflows/ci.yml",
        ".github/workflows/cd.yml",
        ".github/workflows/rollback.yml",
        "infra/docker-compose.yml",
        "docs/10-deployment/deployment-guide.md",
        "docs/10-deployment/env-variables.md",
        "docs/10-deployment/ci-cd.md",
        "docs/10-deployment/release-checklist.md",
    ]
    for relative in required_paths:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, target)

    compose_path = tmp_path / "infra" / "docker-compose.yml"
    compose_path.write_text(
        compose_path.read_text(encoding="utf-8").replace('    expose:\n      - "8000"', '    ports:\n      - "8000:8000"'),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(DEPLOYMENT_VALIDATOR), "--repo-root", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["valid"] is False
    assert any(item["code"] == "public_port" for item in payload["violations"])
