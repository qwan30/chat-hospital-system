import shutil
from pathlib import Path

import pytest

from hospital_ai.evaluation.corpus import (
    CorpusValidationError,
    build_manifest,
    pair_verified_duplicates,
    require_complete_duplicate_pairing,
    validate_manifest,
)


@pytest.fixture
def corpus_root() -> Path:
    return Path(__file__).resolve().parents[2] / "data"


def test_manifest_requires_one_hashed_record_per_patient_file(corpus_root: Path) -> None:
    manifest = build_manifest(corpus_root, None)

    patient_files = [item for item in manifest.files if item.classification == "patient_record"]

    assert len({item.patient_id for item in patient_files}) == 100
    assert len(patient_files) == 200
    assert all(len(item.sha256) == 64 for item in patient_files)


def test_duplicate_pairing_rejects_same_name_with_different_bytes(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    duplicate = tmp_path / "duplicate"
    canonical.mkdir()
    duplicate.mkdir()
    (canonical / "record.csv").write_text("canonical", encoding="utf-8")
    (duplicate / "record.csv").write_text("changed", encoding="utf-8")

    with pytest.raises(CorpusValidationError, match="SHA-256 mismatch"):
        pair_verified_duplicates(canonical, duplicate)


def test_unreviewed_public_knowledge_is_quarantined(corpus_root: Path) -> None:
    manifest = build_manifest(corpus_root, None)

    public_files = [item for item in manifest.files if item.classification == "public_knowledge"]

    assert public_files
    assert all(item.quarantine_state == "excluded_pending_review" for item in public_files)
    assert all(item.runtime_approved is False for item in public_files)


def test_manifest_validation_reports_a_clean_canonical_corpus(corpus_root: Path) -> None:
    manifest = build_manifest(corpus_root, None)

    result = validate_manifest(manifest, corpus_root)

    assert result.is_valid is True
    assert result.patient_count == 100
    assert result.patient_record_count == 200
    assert result.duplicate_digest_count == 0
    assert result.orphan_patient_file_count == 0
    assert result.mismatch_patient_file_count == 0
    assert result.null_ownership_count == 0
    assert result.errors == ()


def test_manifest_validation_rejects_missing_governed_patient_file(corpus_root: Path) -> None:
    manifest = build_manifest(corpus_root, None)
    missing_patient_file = next(item for item in manifest.files if item.classification == "patient_record")
    incomplete_manifest = manifest.copy(
        update={
            "files": tuple(item for item in manifest.files if item != missing_patient_file),
            "patient_record_count": manifest.patient_record_count - 1,
        }
    )

    result = validate_manifest(incomplete_manifest, corpus_root)

    assert result.is_valid is False
    assert result.patient_count == 100
    assert result.patient_record_count == 200
    assert any(error.startswith("Missing manifest entry:") for error in result.errors)


def test_manifest_validation_rechecks_mime_allowlist(corpus_root: Path) -> None:
    manifest = build_manifest(corpus_root, None)
    patient_file = next(item for item in manifest.files if item.classification == "patient_record")
    invalid_mime_file = patient_file.copy(update={"mime_type": "application/x-unknown"})
    invalid_manifest = manifest.copy(
        update={
            "files": tuple(invalid_mime_file if item == patient_file else item for item in manifest.files),
        }
    )

    result = validate_manifest(invalid_manifest, corpus_root)

    assert result.is_valid is False
    assert any(error.startswith("MIME type mismatch:") for error in result.errors)


def test_duplicate_pairing_requires_all_expected_nested_files() -> None:
    with pytest.raises(CorpusValidationError, match="Expected 210 verified duplicate pairs"):
        require_complete_duplicate_pairing({})


def test_manifest_validation_enforces_path_derived_classification(corpus_root: Path) -> None:
    manifest = build_manifest(corpus_root, None)
    public_file = next(item for item in manifest.files if item.classification == "public_knowledge")
    reclassified_file = public_file.copy(
        update={
            "classification": "metadata",
            "license_state": "synthetic-approved",
            "quarantine_state": "active",
            "runtime_approved": True,
        }
    )
    invalid_manifest = manifest.copy(
        update={
            "files": tuple(reclassified_file if item == public_file else item for item in manifest.files),
        }
    )

    result = validate_manifest(invalid_manifest, corpus_root)

    assert result.is_valid is False
    assert any(error.startswith("Classification mismatch:") for error in result.errors)


def test_manifest_validation_requires_fixed_corpus_baseline(corpus_root: Path) -> None:
    manifest = build_manifest(corpus_root, None)
    reduced_manifest = manifest.copy(update={"patient_count": 99, "patient_record_count": 198})

    result = validate_manifest(reduced_manifest, corpus_root)

    assert result.is_valid is False
    assert "Expected exactly 100 patients; manifest declares 99" in result.errors
    assert "Expected exactly 200 patient records; manifest declares 198" in result.errors


def test_manifest_validation_reports_seed_and_patient_pair_removal(corpus_root: Path, tmp_path: Path) -> None:
    copied_root = tmp_path / "data"
    shutil.copytree(corpus_root, copied_root)
    seed_path = copied_root / "metadata" / "generated_patients_seed.csv"
    seed_path.write_text(
        "\n".join(line for line in seed_path.read_text(encoding="utf-8").splitlines() if "MRN-0001" not in line) + "\n",
        encoding="utf-8",
    )
    (copied_root / "patients_documents" / "patient_MRN0001_lab_result.pdf").unlink()
    (copied_root / "patients_labs" / "patient_MRN0001_labs.csv").unlink()
    manifest = build_manifest(corpus_root, None)

    result = validate_manifest(manifest, copied_root)

    assert result.is_valid is False
    assert any(error.startswith("Missing file:") for error in result.errors)
    assert any("Expected exactly 100 patients" in error for error in result.errors)


def test_manifest_validation_collects_malformed_seed_errors(corpus_root: Path, tmp_path: Path) -> None:
    copied_root = tmp_path / "data"
    shutil.copytree(corpus_root, copied_root)
    seed_path = copied_root / "metadata" / "generated_patients_seed.csv"
    seed_path.write_text("patient_id,mrn\nnot-a-uuid,MRN-0001\nnot-a-uuid-2,MRN-0002\n", encoding="utf-8")
    manifest = build_manifest(corpus_root, None)

    result = validate_manifest(manifest, copied_root)

    assert result.is_valid is False
    assert sum("Invalid patient UUID" in error for error in result.errors) == 2


def test_manifest_validation_collects_missing_directory_errors(corpus_root: Path, tmp_path: Path) -> None:
    copied_root = tmp_path / "data"
    shutil.copytree(corpus_root, copied_root)
    shutil.rmtree(copied_root / "patients_labs")
    shutil.rmtree(copied_root / "drugs")
    manifest = build_manifest(corpus_root, None)

    result = validate_manifest(manifest, copied_root)

    assert result.is_valid is False
    assert any("Required corpus directory is missing: patients_labs" in error for error in result.errors)
    assert any("Required corpus directory is missing: drugs" in error for error in result.errors)
