from __future__ import annotations
import importlib.util
from pathlib import Path

import pytest
from pydantic import ValidationError

from hospital_ai.evaluation.corpus_manifest import (
    CorpusManifestV2,
    EvidenceLocator,
    SourceArtifact,
    build_corpus_manifest,
)

DATA_ROOT = Path(__file__).parents[2] / "data"
CLI_PATH = Path(__file__).parents[2] / "scripts" / "build_eval_manifest.py"


def test_builds_canonical_patient_inventory_from_live_data():
    manifest = build_corpus_manifest(DATA_ROOT)

    assert len(manifest.artifacts) == 200
    assert sum(artifact.kind == "patient_document" for artifact in manifest.artifacts) == 100
    assert sum(artifact.kind == "patient_lab" for artifact in manifest.artifacts) == 100
    assert len({artifact.patient_id for artifact in manifest.artifacts}) == 100
    assert all(not Path(artifact.canonical_relative_path).is_absolute() for artifact in manifest.artifacts)


def test_public_knowledge_is_quarantined_and_has_no_patient_identity():
    manifest = build_corpus_manifest(DATA_ROOT)

    public_paths = {artifact.canonical_relative_path for artifact in manifest.quarantined_public_artifacts}
    assert len(manifest.quarantined_public_artifacts) == 6
    assert "drugs/drug_interaction_matrix.csv" in public_paths
    assert all(path.startswith("guidelines/") or path.startswith("drugs/") for path in public_paths)
    assert all(artifact.patient_id is None for artifact in manifest.quarantined_public_artifacts)


def test_manifest_is_deterministic_and_excludes_nested_duplicate_files():
    first = build_corpus_manifest(DATA_ROOT)
    second = build_corpus_manifest(DATA_ROOT)

    assert first.dict() == second.dict()
    assert all("hosp_ai_synthetic_dataset" not in artifact.canonical_relative_path for artifact in first.artifacts)
    assert len(first.excluded_duplicate_artifacts) >= 200
    assert all(artifact.duplicate_of for artifact in first.excluded_duplicate_artifacts)
    assert {
        artifact.mime_type
        for artifact in first.excluded_duplicate_artifacts
        if artifact.canonical_relative_path.endswith(".md")
    } == {"text/markdown"}


def test_locator_serializes_and_contracts_reject_public_patient_identity():
    locator = EvidenceLocator(source_path="patients_labs/patient_MRN0001_labs.csv", row_number=2)
    assert locator.dict() == {
        "source_path": "patients_labs/patient_MRN0001_labs.csv",
        "page_number": None,
        "row_number": 2,
        "record_id": None,
    }

    with pytest.raises(ValidationError):
        SourceArtifact(
            source_sha256="0" * 64,
            canonical_relative_path="guidelines/example.md",
            kind="public_guideline",
            patient_id="20000000-0000-0000-0000-000000000001",
            mime_type="text/markdown",
            document_type="guideline",
            generator="public-reference",
            generator_version="unreviewed",
            provenance_status="unreviewed",
            license_status="unreviewed",
            access_tags=("public",),
            locator=EvidenceLocator(source_path="guidelines/example.md"),
        )


def test_contracts_are_immutable_and_reject_noncanonical_hashes():
    manifest = CorpusManifestV2()
    with pytest.raises(TypeError):
        manifest.corpus_version = "changed"

    with pytest.raises(ValidationError):
        SourceArtifact(
            source_sha256="A" * 64,
            canonical_relative_path="patients_documents/patient_MRN0001_lab_result.pdf",
            kind="patient_document",
            patient_id="20000000-0000-0000-0000-000000000001",
            mime_type="application/pdf",
            document_type="lab_result",
            generator="synthetic-patient-corpus",
            generator_version="v1",
            provenance_status="synthetic-source",
            license_status="internal-synthetic",
            locator=EvidenceLocator(source_path="patients_documents/patient_MRN0001_lab_result.pdf"),
        )


def test_cli_returns_exit_two_for_invalid_corpus_data(monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location("build_eval_manifest", CLI_PATH)
    assert spec is not None and spec.loader is not None
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)

    class InvalidCorpusError(ValueError):
        pass

    def invalid_builder(_data_root):
        raise KeyError("mime_type")

    monkeypatch.setattr(cli, "_load_manifest_builder", lambda: (InvalidCorpusError, invalid_builder))

    assert cli.main(["--check"]) == 2
    assert "invalid evaluation corpus" in capsys.readouterr().err
