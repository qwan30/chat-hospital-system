from __future__ import annotations

import os
from pathlib import Path

import yaml


def test_ci_workflow_parsing_and_structure():
    # Locate the ci.yml file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workflow_path = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".github", "workflows", "ci.yml"))

    assert os.path.exists(workflow_path), f"Workflow file not found at {workflow_path}"

    # Parse yaml file
    with open(workflow_path, encoding="utf-8") as f:
        workflow_data = yaml.safe_load(f)

    assert isinstance(workflow_data, dict), "Parsed workflow is not a dictionary"
    assert "jobs" in workflow_data, "No jobs defined in the CI workflow"

    jobs = workflow_data["jobs"]

    # Assert split CodeQL jobs
    assert "codeql-backend" in jobs, "Optimized 'codeql-backend' job is missing"
    assert "codeql-frontend" in jobs, "Optimized 'codeql-frontend' job is missing"
    assert "codeql" not in jobs, "Legacy un-split 'codeql' job is still present"

    # Assert venv caching steps in python jobs
    for python_job_name in ["backend-test", "backend-migration", "rag-evaluation"]:
        assert python_job_name in jobs, f"Job '{python_job_name}' is missing"
        job_def = jobs[python_job_name]
        steps = job_def.get("steps", [])

        # Verify there is a step using actions/cache for virtual environments
        has_venv_cache = False
        for step in steps:
            uses = step.get("uses", "")
            if "actions/cache" in uses:
                # Check path or key
                path = step.get("with", {}).get("path", "")
                if "venv" in path or "site-packages" in path:
                    has_venv_cache = True
                    break
        assert has_venv_cache, f"Job '{python_job_name}' does not configure virtual environment caching"


def _step_by_name(job: dict, name: str) -> dict:
    return next(step for step in job.get("steps", []) if step.get("name") == name)


def test_compose_validation_uses_synthetic_required_backend_image():
    workflow_path = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "ci.yml"
    workflow_text = workflow_path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(workflow_text)
    validation_job = workflow["jobs"]["validate-observability"]

    assert "- 'infra/docker-compose.local-build.yml'" in workflow_text
    assert "- 'app/backend/docker-compose.yml'" in workflow_text
    assert "- 'app/backend/.dockerignore'" in workflow_text
    assert validation_job.get("env", {}).get("BACKEND_IMAGE") == ("ghcr.io/example/hospital-ai-backend:sha-0000000")
    assert _step_by_name(validation_job, "Validate docker-compose.yml")["run"] == (
        "docker compose -f infra/docker-compose.yml config --quiet"
    )
    assert _step_by_name(validation_job, "Validate docker-compose.observability.yml")["run"] == (
        "docker compose -f infra/docker-compose.yml -f infra/docker-compose.observability.yml config --quiet"
    )
    assert (
        '--backend-image "$BACKEND_IMAGE"'
        in _step_by_name(validation_job, "Validate repository deployment contract")["run"]
    )
    assert set(workflow["jobs"]["docker-push"]["needs"]) == {
        "backend-test",
        "backend-migration",
        "frontend-test",
        "validate-observability",
    }


def test_docker_image_scan_is_a_blocking_release_gate():
    workflow_path = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "ci.yml"
    workflow_text = workflow_path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(workflow_text)
    docker_push = workflow["jobs"]["docker-push"]
    scan = _step_by_name(docker_push, "Scan backend image (Trivy)")
    _ = _step_by_name(workflow["jobs"]["ci-summary"], "Check results")["run"]

    assert scan.get("continue-on-error") is not True
    assert scan["with"]["exit-code"] == 1


def test_ai_evaluation_ci_uses_source_backed_runner_and_publishes_artifacts():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workflow_path = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".github", "workflows", "ci.yml"))

    with open(workflow_path, encoding="utf-8") as f:
        jobs = yaml.safe_load(f)["jobs"]

    evaluation = jobs["rag-evaluation"]
    assert set(evaluation["needs"]) == {"changes", "backend-test", "backend-migration"}

    run_step = _step_by_name(evaluation, "Run deterministic AI evaluation")
    command = run_step["run"]
    assert "scripts/run_ai_evaluation.py" in command
    assert "--lane deterministic" in command
    assert '--suite "$AI_EVAL_SUITE"' in command
    assert '--components "$AI_EVAL_COMPONENTS"' in command
    assert "tests/test_rag_eval.py" not in command
    assert not run_step.get("continue-on-error", False)
    assert "evaluation_status" in command
    assert "sentinel_independent_review" in command
    assert '"$AI_EVAL_SUITE" != "smoke"' in command

    upload = _step_by_name(evaluation, "Upload deterministic AI evaluation artifacts")
    assert upload["if"] == "always()"
    assert upload["with"]["if-no-files-found"] == "error"
    assert "app/backend/evaluation-artifacts/deterministic/" in upload["with"]["path"]

    environment = evaluation["env"]
    assert "inputs.ai_eval_suite" in environment["AI_EVAL_SUITE"]
    assert "inputs.ai_eval_components" in environment["AI_EVAL_COMPONENTS"]


def test_manual_ai_evaluation_dispatch_accepts_bounded_suite_and_component_inputs():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workflow_path = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".github", "workflows", "ci.yml"))

    with open(workflow_path, encoding="utf-8") as f:
        workflow = f.read()

    assert "ai_eval_suite:" in workflow
    assert "type: choice" in workflow
    assert "ai_eval_components:" in workflow
    assert 'default: "corpus,retrieval,graph"' in workflow


def test_live_ai_evaluation_is_manual_and_never_falls_back_to_mock_scores():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workflow_path = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".github", "workflows", "ci.yml"))

    with open(workflow_path, encoding="utf-8") as f:
        jobs = yaml.safe_load(f)["jobs"]

    live = jobs["live-ai-evaluation"]
    assert "workflow_dispatch" in live["if"]
    assert "run_live_ai_evaluation" in live["if"]
    assert "rag-evaluation" in live["needs"]

    run_step = _step_by_name(live, "Run live AI evaluation")
    command = run_step["run"]
    assert "scripts/run_ai_evaluation.py" in command
    assert "--lane live" in command
    assert "--components retrieval,graph,chat" in command
    assert not run_step.get("continue-on-error", False)
    assert run_step["env"] == {
        "AI_EVAL_PROVIDER": "${{ secrets.AI_EVAL_PROVIDER }}",
        "AI_EVAL_MODEL": "${{ secrets.AI_EVAL_MODEL }}",
        "AI_EVAL_API_KEY": "${{ secrets.AI_EVAL_API_KEY }}",
    }

    upload = _step_by_name(live, "Upload live AI evaluation artifacts")
    assert upload["if"] == "always()"
    assert upload["with"]["if-no-files-found"] == "error"
    assert "app/backend/evaluation-artifacts/live/" in upload["with"]["path"]


def test_readme_reports_the_current_source_backed_evaluation_gate():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    readme_path = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "README.md"))
    with open(readme_path, encoding="utf-8") as f:
        readme = f.read()

    assert "6/6 RAG" not in readme
    assert "6/6 scenarios" not in readme
    assert "100% Pass Rate" not in readme
    assert "50-case sentinel" in readme
    assert "blocks release" in readme
    assert "scripts/run_ai_evaluation.py" in readme
    assert "--components corpus --output-dir" in readme
    assert "--components corpus,retrieval,graph,chat" not in readme


def test_cdi_v2_release_gates_are_blocking():
    workflow_path = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "ci.yml"
    workflow_text = workflow_path.read_text(encoding="utf-8")

    assert "alembic check || true" not in workflow_text
    assert "alembic check" in workflow_text

    assert "⚠️ Frontend E2E: advisory — does not block merge" not in workflow_text

    assert "python scripts/verify_cdi_v2_release.py --mode source" in workflow_text
    assert "python -m pytest tests/cdi_v2/test_normative_acceptance.py -q" in workflow_text
    assert "bun run test:e2e -- cdi-v2-document-intelligence.spec.ts" in workflow_text
