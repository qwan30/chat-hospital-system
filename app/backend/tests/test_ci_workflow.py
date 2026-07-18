import os

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
