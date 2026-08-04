from pathlib import Path

from hospital_ai.workers.run_worker import WORKER_QUEUE_NAMES

REPO_ROOT = Path(__file__).resolve().parents[3]


def _read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def test_cd_manifest_digest_verification_fails_closed() -> None:
    workflow = _read(".github/workflows/cd.yml")

    assert "docker buildx imagetools inspect" in workflow
    assert "{{json .Manifest}}" in workflow
    assert 'test("^sha256:[0-9a-f]{64}$")' in workflow
    assert "|| echo \"unknown\"" not in workflow
    assert "^sha256:[0-9a-f]{64}$" in workflow


def test_cd_staging_smoke_is_environment_bound_and_blocking() -> None:
    workflow = _read(".github/workflows/cd.yml")
    smoke = workflow.split("  smoke-test:\n", maxsplit=1)[1]

    assert "environment:\n      name: staging" in smoke
    assert "DOKPLOY_APP_URL: ${{ vars.DOKPLOY_APP_URL }}" in smoke
    assert "must be a non-empty HTTP(S) base URL" in smoke
    assert "--connect-timeout 10 --max-time 20" in smoke
    assert "continue-on-error: true" not in smoke


def test_cd_production_requires_staging_smoke_evidence() -> None:
    workflow = _read(".github/workflows/cd.yml")

    assert "staging-smoke-run-id:" in workflow
    assert "staging-smoke-run-id must identify the successful staging CD run" in workflow
    assert "staging_smoke_run_id" in workflow
    assert "actions/runs/${STAGING_SMOKE_RUN_ID}" in workflow


def test_operations_runbooks_use_active_worker_queues() -> None:
    operations = _read("docs/11-operations/operations-guide.md")
    monitoring = _read("docs/11-operations/monitoring-guide.md")
    troubleshooting = _read("docs/11-operations/troubleshooting.md")
    combined = "\n".join((operations, monitoring, troubleshooting))

    assert WORKER_QUEUE_NAMES == ("document-indexing", "cdss-analysis")
    for queue_name in WORKER_QUEUE_NAMES:
        assert queue_name in combined
    assert "rq:queue:default" not in combined
    assert "rq:queue:failed" not in combined
    assert "FailedJobRegistry" in combined


def test_operations_runbooks_do_not_claim_unsupported_recovery_paths() -> None:
    operations = _read("docs/11-operations/operations-guide.md")
    incident = _read("docs/11-operations/incident-response.md")
    troubleshooting = _read("docs/11-operations/troubleshooting.md")
    combined = "\n".join((operations, incident, troubleshooting))

    assert "HOSPITAL_AI_JWT_ALGORITHM=HS256" not in combined
    assert "Object Versioning" not in combined
    assert "non-current object versions" not in combined
    assert "Existing cached documents" not in combined
    assert "docker system prune -f" not in combined
    assert "fails closed" in combined or "fail closed" in combined
    assert "no automatic local-document failover" in combined
