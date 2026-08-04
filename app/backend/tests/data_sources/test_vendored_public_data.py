from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_ROOT = BACKEND_ROOT / "data"
REGISTRY_PATH = DATA_ROOT / "public" / "sources.json"
REGISTRY_MODULE = BACKEND_ROOT / "src" / "hospital_ai" / "data_sources" / "registry.py"
EXPECTED_UPSTREAM_PATHS = {
    "2_GARD_QA/0003206.xml",
    "2_GARD_QA/0003638.xml",
    "2_GARD_QA/0004425.xml",
    "2_GARD_QA/0004873.xml",
    "2_GARD_QA/0005459.xml",
}


def _load_api():
    assert REGISTRY_MODULE.is_file(), "vendored source registry implementation is missing"
    from hospital_ai.data_sources.registry import (  # noqa: PLC0415
        VendoredDataValidationError,
        load_source_registry,
        validate_vendored_sources,
    )

    return VendoredDataValidationError, load_source_registry, validate_vendored_sources


def test_registry_declares_a_pinned_medquad_gard_sample() -> None:
    assert REGISTRY_PATH.is_file(), "public source registry is missing"
    _, load_source_registry, _ = _load_api()

    registry = load_source_registry(REGISTRY_PATH)

    assert len(registry.sources) == 1
    source = registry.sources[0]
    assert source.source_id == "medquad-gard-evaluation-sample"
    assert source.upstream.repository == "abachaa/MedQuAD"
    assert source.upstream.commit_sha == "577bd37b96c02d1833b2c9eed2de9f96964e96cb"
    assert source.license.spdx_id == "CC-BY-4.0"
    assert "MedQuAD" in source.license.attribution
    assert "evaluation" in source.intended_use.lower()
    assert "not" in source.limitations.lower()
    assert "clinical" in source.limitations.lower()
    assert {artifact.upstream_path for artifact in source.artifacts} == EXPECTED_UPSTREAM_PATHS


def test_registry_paths_are_relative_and_contained_by_data_root() -> None:
    _, load_source_registry, _ = _load_api()
    registry = load_source_registry(REGISTRY_PATH)

    for artifact in registry.sources[0].artifacts:
        assert not Path(artifact.vendored_path).is_absolute()
        resolved = (DATA_ROOT / artifact.vendored_path).resolve()
        assert resolved.is_relative_to(DATA_ROOT.resolve())
        assert resolved.name == Path(artifact.upstream_path).name


def test_vendored_xml_files_match_registry_hashes_and_sizes() -> None:
    _, load_source_registry, validate_vendored_sources = _load_api()
    registry = load_source_registry(REGISTRY_PATH)

    results = validate_vendored_sources(DATA_ROOT, REGISTRY_PATH)

    assert len(results) == len(EXPECTED_UPSTREAM_PATHS)
    results_by_path = {result.path: result for result in results}
    for artifact in registry.sources[0].artifacts:
        path = (DATA_ROOT / artifact.vendored_path).resolve()
        assert path.is_file(), f"vendored MedQuAD XML is missing: {path}"
        result = results_by_path[path]
        assert result.source_id == "medquad-gard-evaluation-sample"
        assert result.size_bytes == artifact.size_bytes == path.stat().st_size
        assert result.sha256 == artifact.sha256


def test_missing_artifact_fails_closed_without_repair(tmp_path: Path) -> None:
    error_type, _, validate_vendored_sources = _load_api()
    isolated_data = tmp_path / "data"
    isolated_registry = isolated_data / "public" / "sources.json"
    isolated_registry.parent.mkdir(parents=True)
    shutil.copyfile(REGISTRY_PATH, isolated_registry)

    with pytest.raises(error_type, match="missing"):
        validate_vendored_sources(isolated_data, isolated_registry)

    assert not (isolated_data / "public" / "medquad" / "sample").exists()


def test_modified_artifact_fails_closed(tmp_path: Path) -> None:
    error_type, load_source_registry, validate_vendored_sources = _load_api()
    isolated_data = tmp_path / "data"
    isolated_registry = isolated_data / "public" / "sources.json"
    isolated_registry.parent.mkdir(parents=True)
    shutil.copyfile(REGISTRY_PATH, isolated_registry)
    registry = load_source_registry(isolated_registry)
    first = registry.sources[0].artifacts[0]
    isolated_artifact = isolated_data / first.vendored_path
    isolated_artifact.parent.mkdir(parents=True)
    isolated_artifact.write_bytes(b"tampered")

    with pytest.raises(error_type, match="size|SHA-256"):
        validate_vendored_sources(isolated_data, isolated_registry)


def test_registry_rejects_a_path_escape(tmp_path: Path) -> None:
    error_type, load_source_registry, _ = _load_api()
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    payload["sources"][0]["artifacts"][0]["vendored_path"] = "../outside.xml"
    invalid_registry = tmp_path / "sources.json"
    invalid_registry.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises((ValueError, error_type), match="relative|escape|traversal"):
        load_source_registry(invalid_registry)


def test_github_actions_do_not_download_public_datasets() -> None:
    workflow_root = REPO_ROOT / ".github" / "workflows"
    patterns = (
        re.compile(r"load_dataset\s*\(", re.IGNORECASE),
        re.compile(r"hf_hub_download", re.IGNORECASE),
        re.compile(r"huggingface-cli\s+download", re.IGNORECASE),
        re.compile(r"\bhf\s+download", re.IGNORECASE),
        re.compile(r"(?:curl|wget).*(?:medquad|maccrobat|noteevents)", re.IGNORECASE),
        re.compile(r"download_hf_notes\.py", re.IGNORECASE),
    )
    violations: list[str] = []

    for workflow in sorted((*workflow_root.glob("*.yml"), *workflow_root.glob("*.yaml"))):
        content = workflow.read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern.search(content):
                violations.append(f"{workflow.relative_to(REPO_ROOT)}: {pattern.pattern}")

    assert violations == []


def test_backend_container_includes_only_vendored_public_data() -> None:
    dockerfile = (BACKEND_ROOT / "Dockerfile").read_text(encoding="utf-8")
    dockerignore = (BACKEND_ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert "COPY data/public/ data/public/" in dockerfile
    assert "data/*" in dockerignore
    assert "!data/public/" in dockerignore
    assert "!data/public/**" in dockerignore
    assert "\ndata/\n" not in f"\n{dockerignore}"


def test_misleading_legacy_dataset_scripts_are_absent() -> None:
    scripts = BACKEND_ROOT / "scripts"

    assert not (scripts / "download_hf_notes.py").exists()
    assert not (scripts / "seed_mimic.py").exists()
    assert (scripts / "seed_mock_clinical_notes.py").is_file()
