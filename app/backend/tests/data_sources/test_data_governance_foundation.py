from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]


def _registry_payload(*, artifact_path: str, size_bytes: int, sha256: str) -> dict:
    return {
        "schema_version": "1.0",
        "sources": [
            {
                "source_id": "example-public-source",
                "name": "Example public source",
                "upstream": {
                    "repository": "example/source",
                    "commit_sha": "a" * 40,
                },
                "license": {
                    "spdx_id": "CC-BY-4.0",
                    "attribution": "Example attribution",
                    "license_url": "https://creativecommons.org/licenses/by/4.0/",
                },
                "retrieved_at": "2026-08-04T00:00:00Z",
                "intended_use": "Registry contract testing",
                "limitations": "Not clinical evidence",
                "artifacts": [
                    {
                        "upstream_path": "sample.txt",
                        "upstream_blob_sha": "b" * 40,
                        "vendored_path": artifact_path,
                        "media_type": "text/plain",
                        "size_bytes": size_bytes,
                        "sha256": sha256,
                    }
                ],
            }
        ],
    }


def test_generic_registry_validates_an_isolated_temporary_artifact(tmp_path: Path) -> None:
    from hospital_ai.data_sources.registry import validate_vendored_sources

    data_root = tmp_path / "data"
    artifact = data_root / "qualification" / "sample.txt"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("source-backed fixture\n", encoding="utf-8")
    artifact_bytes = artifact.read_bytes()

    registry_path = tmp_path / "sources.json"
    registry_path.write_text(
        json.dumps(
            _registry_payload(
                artifact_path="qualification/sample.txt",
                size_bytes=len(artifact_bytes),
                sha256=hashlib.sha256(artifact_bytes).hexdigest(),
            )
        ),
        encoding="utf-8",
    )

    validated = validate_vendored_sources(data_root, registry_path)

    assert len(validated) == 1
    assert validated[0].path == artifact.resolve()


def test_registry_rejects_path_traversal_without_touching_files(tmp_path: Path) -> None:
    from hospital_ai.data_sources.registry import VendoredDataValidationError, load_source_registry

    registry_path = tmp_path / "sources.json"
    registry_path.write_text(
        json.dumps(
            _registry_payload(
                artifact_path="../outside.txt",
                size_bytes=1,
                sha256="0" * 64,
            )
        ),
        encoding="utf-8",
    )

    with pytest.raises(VendoredDataValidationError, match="relative|traversal"):
        load_source_registry(registry_path)

    assert not (tmp_path.parent / "outside.txt").exists()


def test_public_qualification_sources_are_not_canonical_patient_corpus() -> None:
    corpus_manifest = (
        BACKEND_ROOT / "src" / "hospital_ai" / "evaluation" / "corpus_manifest.py"
    ).read_text(encoding="utf-8")

    assert "approved_public_artifacts" not in corpus_manifest
    assert "public_evaluation_dataset" not in corpus_manifest
    assert "public/sources.json" not in corpus_manifest


def test_backend_image_does_not_bundle_a_standalone_public_dataset() -> None:
    dockerfile = (BACKEND_ROOT / "Dockerfile").read_text(encoding="utf-8")
    dockerignore = (BACKEND_ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert "COPY data/public/ data/public/" not in dockerfile
    assert "!data/public/**" not in dockerignore


def test_repository_contains_no_standalone_medquad_product_fixture() -> None:
    assert not (BACKEND_ROOT / "data" / "public" / "medquad").exists()
    assert not (BACKEND_ROOT / "data" / "public" / "sources.json").exists()
    assert not (REPO_ROOT / ".github" / "workflows" / "vendored-public-data.yml").exists()


def test_misleading_legacy_dataset_scripts_are_absent() -> None:
    scripts = BACKEND_ROOT / "scripts"

    assert not (scripts / "download_hf_notes.py").exists()
    assert not (scripts / "seed_mimic.py").exists()
    assert (scripts / "seed_mock_clinical_notes.py").is_file()
