"""Immutable, source-backed inventory for the synthetic evaluation corpus."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, root_validator, validator

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MRN_RE = re.compile(r"patient_MRN(\d{4})_")
_PATIENT_KINDS = {"patient_document", "patient_lab"}
_PUBLIC_KINDS = {"public_guideline", "public_drug"}
_CANONICAL_DOCUMENTS = "patients_documents"
_CANONICAL_LABS = "patients_labs"
_INGESTION_METADATA = "metadata/ingestion_metadata.jsonl"
_PATIENT_SEED = "metadata/generated_patients_seed.csv"


class CorpusManifestValidationError(ValueError):
    """Raised when the evaluation corpus is not a trustworthy source inventory."""


def _validate_relative_path(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or value != value.replace("\\", "/"):
        raise ValueError("source paths must be normalized relative paths")
    if not value or value == ".":
        raise ValueError("source path must not be empty")
    return value


class EvidenceLocator(BaseModel):
    source_path: str
    page_number: int | None = None
    row_number: int | None = None
    record_id: str | None = None

    _source_path_is_relative = validator("source_path", allow_reuse=True)(_validate_relative_path)

    @validator("page_number", "row_number")
    def _positive_positions(cls, value: int | None) -> int | None:
        if value is not None and value < 1:
            raise ValueError("locator positions must be positive")
        return value

    class Config:
        frozen = True


class SourceArtifact(BaseModel):
    source_sha256: str
    canonical_relative_path: str
    kind: Literal[
        "patient_document",
        "patient_lab",
        "public_guideline",
        "public_drug",
        "duplicate",
    ]
    patient_id: UUID | None = None
    mime_type: str
    document_type: str
    generator: str
    generator_version: str
    provenance_status: str
    license_status: str
    access_tags: tuple[str, ...] = ()
    locator: EvidenceLocator
    duplicate_of: str | None = None

    @validator("source_sha256")
    def _source_hash_is_valid(cls, value: str) -> str:
        if not _SHA256_RE.fullmatch(value):
            raise ValueError("source_sha256 must be lowercase SHA-256")
        return value

    _canonical_path_is_relative = validator("canonical_relative_path", allow_reuse=True)(_validate_relative_path)

    @root_validator
    def _enforce_identity_and_duplicate_contract(cls, values: dict) -> dict:
        kind = values.get("kind")
        patient_id = values.get("patient_id")
        duplicate_of = values.get("duplicate_of")
        if kind in _PATIENT_KINDS and patient_id is None:
            raise ValueError("patient artifacts require a patient_id")
        if kind in _PUBLIC_KINDS and patient_id is not None:
            raise ValueError("public artifacts must not have a patient_id")
        if kind == "duplicate" and not duplicate_of:
            raise ValueError("duplicate artifacts require duplicate_of")
        if kind != "duplicate" and duplicate_of is not None:
            raise ValueError("only duplicate artifacts may set duplicate_of")
        if duplicate_of is not None:
            _validate_relative_path(duplicate_of)
        return values

    class Config:
        frozen = True


class CorpusManifestV2(BaseModel):
    schema_version: Literal["2.0"] = "2.0"
    corpus_version: str = "synthetic-100-v2"
    artifacts: tuple[SourceArtifact, ...] = ()
    quarantined_public_artifacts: tuple[SourceArtifact, ...] = ()
    excluded_duplicate_artifacts: tuple[SourceArtifact, ...] = ()

    class Config:
        frozen = True


def _source_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _mime_type_for_path(relative_path: str) -> str:
    suffix = Path(relative_path).suffix.lower()
    return {
        ".pdf": "application/pdf",
        ".csv": "text/csv",
        ".md": "text/markdown",
        ".jsonl": "application/x-ndjson",
    }.get(suffix, "application/octet-stream")


def _relative_path(data_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(data_root).as_posix()
    except ValueError as error:
        raise CorpusManifestValidationError(f"source path escapes data root: {path}") from error


def _load_known_patients(data_root: Path) -> tuple[dict[str, UUID], set[UUID]]:
    seed_path = data_root / _PATIENT_SEED
    if not seed_path.is_file():
        raise CorpusManifestValidationError(f"missing patient seed: {_PATIENT_SEED}")
    with seed_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 100:
        raise CorpusManifestValidationError(f"expected 100 patient seed rows, found {len(rows)}")
    by_mrn = {row.get("mrn", ""): UUID(row["patient_id"]) for row in rows}
    if len(by_mrn) != 100 or len(set(by_mrn.values())) != 100 or "" in by_mrn:
        raise CorpusManifestValidationError("patient seed must contain 100 unique MRN and patient identities")
    return by_mrn, set(by_mrn.values())


def _normalize_storage_uri(storage_uri: str) -> str:
    normalized = storage_uri.replace("\\", "/")
    marker = "/data/"
    if marker in normalized:
        normalized = normalized.split(marker, 1)[1]
    elif normalized.startswith("data/"):
        normalized = normalized[len("data/") :]
    return _validate_relative_path(normalized)


def _load_ingestion_metadata(data_root: Path, known_patient_ids: set[UUID]) -> dict[str, dict]:
    metadata_path = data_root / _INGESTION_METADATA
    if not metadata_path.is_file():
        raise CorpusManifestValidationError(f"missing ingestion metadata: {_INGESTION_METADATA}")
    rows = []
    with metadata_path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise CorpusManifestValidationError(f"invalid metadata JSON at line {line_number}") from error
    if len(rows) != 200:
        raise CorpusManifestValidationError(f"expected 200 ingestion metadata records, found {len(rows)}")

    by_path: dict[str, dict] = {}
    for row in rows:
        try:
            patient_id = UUID(row["patient_id"])
            relative_path = _normalize_storage_uri(row["storage_uri"])
        except (KeyError, ValueError) as error:
            raise CorpusManifestValidationError("ingestion metadata has an invalid patient or source path") from error
        if patient_id not in known_patient_ids:
            raise CorpusManifestValidationError(f"metadata references unknown patient: {patient_id}")
        if relative_path in by_path:
            raise CorpusManifestValidationError(f"duplicate ingestion metadata path: {relative_path}")
        if not (data_root / relative_path).is_file():
            raise CorpusManifestValidationError(f"metadata source is not under data root: {relative_path}")
        by_path[relative_path] = {**row, "patient_id": patient_id}
    return by_path


def _patient_id_for_path(relative_path: str, metadata: dict[str, dict], known_by_mrn: dict[str, UUID]) -> UUID | None:
    logical_path = relative_path
    nested_marker = "/app/backend/data/"
    if nested_marker in logical_path:
        logical_path = logical_path.split(nested_marker, 1)[1]
    row = metadata.get(logical_path)
    if row is None:
        return None
    mrn_match = _MRN_RE.search(logical_path)
    mrn = f"MRN-{mrn_match.group(1)}" if mrn_match is not None else None
    if mrn is None or known_by_mrn.get(mrn) != row["patient_id"]:
        raise CorpusManifestValidationError(f"metadata identity does not match source filename: {logical_path}")
    return row["patient_id"]


def _artifact_from_metadata(relative_path: str, path: Path, metadata_row: dict) -> SourceArtifact:
    kind = "patient_document" if relative_path.startswith(f"{_CANONICAL_DOCUMENTS}/") else "patient_lab"
    locator = EvidenceLocator(
        source_path=relative_path,
        page_number=1 if kind == "patient_document" else None,
        row_number=1 if kind == "patient_lab" else None,
    )
    return SourceArtifact(
        source_sha256=_source_hash(path),
        canonical_relative_path=relative_path,
        kind=kind,
        patient_id=metadata_row["patient_id"],
        mime_type=metadata_row["mime_type"],
        document_type=metadata_row["document_type"],
        generator="synthetic-patient-corpus",
        generator_version="v1",
        provenance_status="synthetic-source",
        license_status="internal-synthetic",
        access_tags=tuple(sorted(metadata_row.get("access_tags", ()))),
        locator=locator,
    )


def _public_artifact(relative_path: str, path: Path) -> SourceArtifact:
    is_guideline = relative_path.startswith("guidelines/")
    return SourceArtifact(
        source_sha256=_source_hash(path),
        canonical_relative_path=relative_path,
        kind="public_guideline" if is_guideline else "public_drug",
        mime_type="text/markdown" if is_guideline else "text/csv",
        document_type="guideline" if is_guideline else "drug_interaction_matrix",
        generator="public-reference",
        generator_version="unreviewed",
        provenance_status="quarantined-pending-review",
        license_status="unreviewed",
        access_tags=("public", "quarantined"),
        locator=EvidenceLocator(source_path=relative_path, row_number=1 if not is_guideline else None),
    )


def _validate_canonical_inventory(data_root: Path) -> tuple[list[Path], list[Path]]:
    documents = sorted((data_root / _CANONICAL_DOCUMENTS).glob("*.pdf"))
    labs = sorted((data_root / _CANONICAL_LABS).glob("*.csv"))
    if len(documents) != 100:
        raise CorpusManifestValidationError(f"expected 100 PDFs in {_CANONICAL_DOCUMENTS}, found {len(documents)}")
    if len(labs) != 100:
        raise CorpusManifestValidationError(f"expected 100 CSVs in {_CANONICAL_LABS}, found {len(labs)}")
    return documents, labs


def build_corpus_manifest(data_root: Path) -> CorpusManifestV2:
    """Build a deterministic manifest from canonical sources without modifying them."""
    root = data_root.resolve()
    if not root.is_dir():
        raise CorpusManifestValidationError(f"data root does not exist: {data_root}")

    known_by_mrn, known_patient_ids = _load_known_patients(root)
    metadata = _load_ingestion_metadata(root, known_patient_ids)
    documents, labs = _validate_canonical_inventory(root)
    canonical_paths = [_relative_path(root, path) for path in documents + labs]
    if set(canonical_paths) != set(metadata):
        raise CorpusManifestValidationError("ingestion metadata must map exactly to canonical patient sources")

    artifacts = tuple(
        _artifact_from_metadata(relative_path, root / relative_path, metadata[relative_path])
        for relative_path in sorted(canonical_paths)
    )
    if len({artifact.patient_id for artifact in artifacts}) != 100:
        raise CorpusManifestValidationError("canonical patient artifacts must represent exactly 100 patients")

    public_paths = sorted(
        [_relative_path(root, path) for path in (root / "guidelines").rglob("*") if path.is_file()]
        + [_relative_path(root, root / "drugs" / "drug_interaction_matrix.csv")]
    )
    if len(public_paths) != 6:
        raise CorpusManifestValidationError("expected five guidelines and one drug matrix for quarantine")
    quarantined = tuple(_public_artifact(relative_path, root / relative_path) for relative_path in public_paths)

    canonical_by_hash = {
        artifact.source_sha256: artifact.canonical_relative_path for artifact in artifacts + quarantined
    }
    duplicate_artifacts: list[SourceArtifact] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative_path = _relative_path(root, path)
        if relative_path in canonical_paths or relative_path in public_paths:
            continue
        source_sha256 = _source_hash(path)
        duplicate_of = canonical_by_hash.get(source_sha256)
        if duplicate_of is None:
            continue
        patient_id = _patient_id_for_path(relative_path, metadata, known_by_mrn)
        duplicate_artifacts.append(
            SourceArtifact(
                source_sha256=source_sha256,
                canonical_relative_path=relative_path,
                kind="duplicate",
                patient_id=patient_id,
                mime_type=_mime_type_for_path(relative_path),
                document_type="duplicate",
                generator="duplicate-source-scan",
                generator_version="v1",
                provenance_status="duplicate-excluded",
                license_status="inherits-canonical-review",
                access_tags=("excluded", "duplicate"),
                locator=EvidenceLocator(source_path=relative_path),
                duplicate_of=duplicate_of,
            )
        )

    return CorpusManifestV2(
        artifacts=artifacts,
        quarantined_public_artifacts=quarantined,
        excluded_duplicate_artifacts=tuple(duplicate_artifacts),
    )
