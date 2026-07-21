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
