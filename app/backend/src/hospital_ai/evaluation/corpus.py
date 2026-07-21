"""Construction and validation of the canonical synthetic RAG corpus."""

from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from uuid import UUID

from hospital_ai.evaluation.models import CorpusFile, CorpusManifest, CorpusValidationResult

_CHUNK_SIZE = 1024 * 1024
_GENERATOR = "HOSP-AI-001 synthetic dataset generator"
_GENERATOR_VERSION = "1.0"
_SOURCE = "dataset_generation_instruction.md"
_EXPECTED_PATIENT_COUNT = 100
_EXPECTED_PATIENT_RECORD_COUNT = 200
_EXPECTED_NESTED_DUPLICATE_PAIR_COUNT = 210
_PATIENT_PDF = re.compile(r"^patient_(MRN\d{4})_(.+)\.pdf$")
_PATIENT_LAB = re.compile(r"^patient_(MRN\d{4})_labs\.csv$")
_MIME_TYPES = {
    ".csv": "text/csv",
    ".jsonl": "application/x-ndjson",
    ".md": "text/markdown",
    ".pdf": "application/pdf",
}
_GOVERNED_DIRECTORIES = (
    ("patients_documents", "patient_record"),
    ("patients_labs", "patient_record"),
    ("drugs", "public_knowledge"),
    ("guidelines/nursing", "public_knowledge"),
    ("security", "audit_fixture"),
    ("metadata", "metadata"),
)


class CorpusValidationError(ValueError):
    """Raised when corpus structure or duplicate content is unsafe to govern."""


def sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 digest for one regular file."""
    resolved_path = path.resolve(strict=True)
    if not resolved_path.is_file():
        raise CorpusValidationError(f"Not a file: {path}")

    digest = hashlib.sha256()
    with resolved_path.open("rb") as source:
        for chunk in iter(lambda: source.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pair_verified_duplicates(canonical_root: Path, duplicate_root: Path) -> dict[Path, Path]:
    """Pair every duplicate file only when its canonical counterpart has identical bytes."""
    canonical = _resolve_root(canonical_root)
    duplicate = _resolve_root(duplicate_root)
    pairs: dict[Path, Path] = {}

    for duplicate_file in sorted(path for path in duplicate.rglob("*") if path.is_file()):
        relative_path = duplicate_file.relative_to(duplicate)
        canonical_file = _resolve_contained(canonical, canonical / relative_path)
        if not canonical_file.is_file():
            raise CorpusValidationError(f"Missing canonical counterpart: {relative_path.as_posix()}")
        if sha256_file(canonical_file) != sha256_file(duplicate_file):
            raise CorpusValidationError(f"SHA-256 mismatch: {relative_path.as_posix()}")
        pairs[canonical_file] = duplicate_file.resolve(strict=True)

    return pairs


def require_complete_duplicate_pairing(pairs: dict[Path, Path]) -> None:
    """Require the full verified nested-copy inventory before it may be removed."""
    if len(pairs) != _EXPECTED_NESTED_DUPLICATE_PAIR_COUNT:
        raise CorpusValidationError(
            f"Expected {_EXPECTED_NESTED_DUPLICATE_PAIR_COUNT} verified duplicate pairs, found {len(pairs)}"
        )


def build_manifest(data_root: Path, duplicate_root: Path | None) -> CorpusManifest:
    """Build a deterministic manifest for the governed synthetic corpus roots."""
    root = _resolve_root(data_root)
    patient_lookup = _load_patient_lookup(root)
    if duplicate_root is not None:
        pair_verified_duplicates(root, duplicate_root)

    files = tuple(
        _build_file(root, path, patient_lookup, classification)
        for classification, paths in _governed_files(root)
        for path in paths
    )
    patient_files = [item for item in files if item.classification == "patient_record"]
    patient_ids = {item.patient_id for item in patient_files if item.patient_id is not None}

    return CorpusManifest(
        schema_version="1.0",
        corpus_version="hosp-ai-001-canonical-1.0",
        patient_count=len(patient_ids),
        patient_record_count=len(patient_files),
        files=files,
    )


def validate_manifest(manifest: CorpusManifest, data_root: Path) -> CorpusValidationResult:
    """Validate all manifest items and return every detected governance error."""
    errors: list[str] = []
    try:
        root = _resolve_root(data_root)
    except (OSError, CorpusValidationError) as exc:
        return CorpusValidationResult(
            is_valid=False,
            patient_count=0,
            patient_record_count=0,
            duplicate_digest_count=0,
            orphan_patient_file_count=0,
            mismatch_patient_file_count=0,
            null_ownership_count=0,
            errors=(str(exc),),
        )

    try:
        patient_lookup = _load_patient_lookup(root, errors)
    except (OSError, ValueError, CorpusValidationError) as exc:
        patient_lookup = {}
        errors.append(str(exc))

    governed_file_groups = _collect_governed_files(root, errors)

    orphan_patient_file_count = 0
    mismatch_patient_file_count = 0
    null_ownership_count = 0
    digest_counts: Counter[str] = Counter()
    expected_classifications = {
        path.relative_to(root).as_posix(): classification
        for classification, paths in governed_file_groups
        for path in paths
    }
    governed_paths = set(expected_classifications)
    expected_patient_record_paths = {
        path.relative_to(root).as_posix()
        for classification, paths in governed_file_groups
        if classification == "patient_record"
        for path in paths
    }
    declared_path_counts = Counter(item.relative_path for item in manifest.files)

    for relative_path, count in declared_path_counts.items():
        if count > 1:
            errors.append(f"Duplicate manifest entry: {relative_path}")
    for relative_path in sorted(governed_paths - set(declared_path_counts)):
        errors.append(f"Missing manifest entry: {relative_path}")
    for relative_path in sorted(set(declared_path_counts) - governed_paths):
        errors.append(f"Unexpected manifest entry: {relative_path}")

    for item in manifest.files:
        expected_classification = expected_classifications.get(item.relative_path)
        if expected_classification is not None and item.classification != expected_classification:
            errors.append(f"Classification mismatch: {item.relative_path}")
        try:
            path = _resolve_contained(root, root / item.relative_path)
            if not path.is_file():
                errors.append(f"Missing file: {item.relative_path}")
                continue
            digest_counts[item.sha256] += 1
            actual_digest = sha256_file(path)
            if actual_digest != item.sha256:
                errors.append(f"SHA-256 mismatch: {item.relative_path}")
            if path.stat().st_size != item.byte_size:
                errors.append(f"Byte-size mismatch: {item.relative_path}")
            expected_mime_type = _MIME_TYPES.get(path.suffix.lower())
            if expected_mime_type is None:
                errors.append(f"MIME type is not allowlisted: {item.relative_path}")
            elif item.mime_type != expected_mime_type:
                errors.append(f"MIME type mismatch: {item.relative_path}")
        except (OSError, CorpusValidationError) as exc:
            errors.append(str(exc))
            continue

        if item.classification == "patient_record":
            if item.patient_id is None:
                null_ownership_count += 1
                errors.append(f"Patient record has null ownership: {item.relative_path}")
                continue
            expected_patient_id = _patient_id_for_path(path, patient_lookup)
            if expected_patient_id is None:
                orphan_patient_file_count += 1
                errors.append(f"Patient record has no MRN mapping: {item.relative_path}")
            elif item.patient_id != expected_patient_id:
                mismatch_patient_file_count += 1
                errors.append(f"Patient ownership mismatch: {item.relative_path}")
        elif item.classification == "public_knowledge":
            if item.quarantine_state != "excluded_pending_review" or item.runtime_approved:
                errors.append(f"Public knowledge is not quarantined: {item.relative_path}")

    duplicate_digest_count = sum(count - 1 for count in digest_counts.values() if count > 1)
    if duplicate_digest_count:
        errors.append(f"Duplicate manifest digests: {duplicate_digest_count}")

    if manifest.patient_count != _EXPECTED_PATIENT_COUNT:
        errors.append(f"Expected exactly 100 patients; manifest declares {manifest.patient_count}")
    if manifest.patient_record_count != _EXPECTED_PATIENT_RECORD_COUNT:
        errors.append(f"Expected exactly 200 patient records; manifest declares {manifest.patient_record_count}")
    if len(patient_lookup) != _EXPECTED_PATIENT_COUNT:
        errors.append(f"Expected exactly 100 patients on disk; found {len(patient_lookup)}")
    if len(expected_patient_record_paths) != _EXPECTED_PATIENT_RECORD_COUNT:
        errors.append(f"Expected exactly 200 patient records on disk; found {len(expected_patient_record_paths)}")
    if manifest.patient_count != len(patient_lookup):
        errors.append("Manifest patient count does not match patient record ownership")
    if manifest.patient_record_count != len(expected_patient_record_paths):
        errors.append("Manifest patient record count does not match patient record files")

    return CorpusValidationResult(
        is_valid=not errors,
        patient_count=len(patient_lookup),
        patient_record_count=len(expected_patient_record_paths),
        duplicate_digest_count=duplicate_digest_count,
        orphan_patient_file_count=orphan_patient_file_count,
        mismatch_patient_file_count=mismatch_patient_file_count,
        null_ownership_count=null_ownership_count,
        errors=tuple(errors),
    )


def _governed_files(root: Path) -> Iterable[tuple[str, tuple[Path, ...]]]:
    for directory, classification in _GOVERNED_DIRECTORIES:
        governed_directory = _resolve_contained(root, root / directory)
        if not governed_directory.is_dir():
            raise CorpusValidationError(f"Required corpus directory is missing: {directory}")
        files = tuple(sorted(path for path in governed_directory.rglob("*") if path.is_file()))
        yield classification, files


def _collect_governed_files(root: Path, errors: list[str]) -> tuple[tuple[str, tuple[Path, ...]], ...]:
    groups: list[tuple[str, tuple[Path, ...]]] = []
    for directory, classification in _GOVERNED_DIRECTORIES:
        try:
            governed_directory = _resolve_contained(root, root / directory)
            if not governed_directory.is_dir():
                raise CorpusValidationError(f"Required corpus directory is missing: {directory}")
            groups.append(
                (classification, tuple(sorted(path for path in governed_directory.rglob("*") if path.is_file())))
            )
        except (OSError, CorpusValidationError) as exc:
            errors.append(str(exc))
    return tuple(groups)


def _build_file(root: Path, path: Path, patient_lookup: dict[str, UUID], classification: str) -> CorpusFile:
    resolved_path = _resolve_contained(root, path)
    mime_type = _MIME_TYPES.get(resolved_path.suffix.lower())
    if mime_type is None:
        raise CorpusValidationError(f"MIME type is not allowlisted: {resolved_path.relative_to(root).as_posix()}")

    patient_id = _patient_id_for_path(resolved_path, patient_lookup) if classification == "patient_record" else None
    if classification == "patient_record" and patient_id is None:
        raise CorpusValidationError(f"Patient record has no MRN mapping: {resolved_path.relative_to(root).as_posix()}")
    quarantine_state = "excluded_pending_review" if classification == "public_knowledge" else "active"

    return CorpusFile(
        relative_path=resolved_path.relative_to(root).as_posix(),
        sha256=sha256_file(resolved_path),
        byte_size=resolved_path.stat().st_size,
        patient_id=patient_id,
        document_id=resolved_path.stem,
        document_type=_document_type(resolved_path, classification),
        mime_type=mime_type,
        generator=_GENERATOR,
        generator_version=_GENERATOR_VERSION,
        source=_SOURCE,
        synthetic=True,
        license_state="pending-review" if classification == "public_knowledge" else "synthetic-approved",
        classification=classification,
        quarantine_state=quarantine_state,
        runtime_approved=False if classification == "public_knowledge" else True,
    )


def _load_patient_lookup(root: Path, errors: list[str] | None = None) -> dict[str, UUID]:
    seed_path = _resolve_contained(root, root / "metadata/generated_patients_seed.csv")
    if not seed_path.is_file():
        message = "Missing patient seed metadata"
        if errors is None:
            raise CorpusValidationError(message)
        errors.append(message)
        return {}

    patient_lookup: dict[str, UUID] = {}
    with seed_path.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            mrn = row.get("mrn", "").strip()
            patient_id = row.get("patient_id", "").strip()
            if not mrn or not patient_id:
                message = "Patient seed metadata has a missing MRN or patient_id"
                if errors is None:
                    raise CorpusValidationError(message)
                errors.append(message)
                continue
            if mrn in patient_lookup:
                message = f"Patient seed metadata has duplicate MRN: {mrn}"
                if errors is None:
                    raise CorpusValidationError(message)
                errors.append(message)
                continue
            try:
                patient_lookup[mrn] = UUID(patient_id)
            except ValueError as exc:
                message = f"Invalid patient UUID for {mrn}: {exc}"
                if errors is None:
                    raise CorpusValidationError(message) from exc
                errors.append(message)
    return patient_lookup


def _patient_id_for_path(path: Path, patient_lookup: dict[str, UUID]) -> UUID | None:
    match = _PATIENT_PDF.match(path.name) or _PATIENT_LAB.match(path.name)
    if match is None:
        return None
    mrn = f"MRN-{match.group(1)[3:]}"
    return patient_lookup.get(mrn)


def _document_type(path: Path, classification: str) -> str:
    if classification == "patient_record":
        pdf_match = _PATIENT_PDF.match(path.name)
        if pdf_match is not None:
            return pdf_match.group(2)
        return "lab_trend"
    if classification == "public_knowledge":
        return "public_knowledge"
    return classification


def _resolve_root(path: Path) -> Path:
    resolved_path = path.resolve(strict=True)
    if not resolved_path.is_dir():
        raise CorpusValidationError(f"Not a directory: {path}")
    return resolved_path


def _resolve_contained(root: Path, candidate: Path) -> Path:
    resolved_candidate = candidate.resolve(strict=False)
    try:
        resolved_candidate.relative_to(root)
    except ValueError as exc:
        raise CorpusValidationError(f"Path escapes corpus root: {candidate}") from exc
    return resolved_candidate
