"""Offline validation for explicitly staged public-source artifacts."""
from __future__ import annotations


import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError, root_validator, validator

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SourceRegistryValidationError(ValueError):
    """Raised when a public-source registry or local artifact is untrustworthy."""


def _require_text(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("value must not be empty")
    return value


def _validate_relative_path(value: str) -> str:
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value:
        raise ValueError("path must be a normalized relative path without traversal")
    if path.as_posix() != value:
        raise ValueError("path must be a normalized relative path")
    return value


def _require_https_url(value: str) -> str:
    value = _require_text(value)
    if not value.startswith("https://"):
        raise ValueError("license_url must use HTTPS")
    return value


class UpstreamSource(BaseModel):
    repository: str
    commit_sha: str

    _repository_is_present = validator("repository", allow_reuse=True)(_require_text)

    @validator("commit_sha")
    def _commit_sha_is_valid(cls, value: str) -> str:
        if not _SHA1_RE.fullmatch(value):
            raise ValueError("commit_sha must be a lowercase 40-character Git SHA")
        return value

    class Config:
        allow_mutation = False


class LicenseMetadata(BaseModel):
    spdx_id: str
    attribution: str
    license_url: str

    _text_fields_are_present = validator("spdx_id", "attribution", allow_reuse=True)(_require_text)
    _license_url_is_https = validator("license_url", allow_reuse=True)(_require_https_url)

    class Config:
        allow_mutation = False


class SourceArtifact(BaseModel):
    upstream_path: str
    upstream_blob_sha: str
    local_path: str
    media_type: str
    size_bytes: int
    sha256: str

    _upstream_path_is_relative = validator("upstream_path", allow_reuse=True)(_validate_relative_path)
    _local_path_is_relative = validator("local_path", allow_reuse=True)(_validate_relative_path)
    _media_type_is_present = validator("media_type", allow_reuse=True)(_require_text)

    @validator("upstream_blob_sha")
    def _blob_sha_is_valid(cls, value: str) -> str:
        if not _SHA1_RE.fullmatch(value):
            raise ValueError("upstream_blob_sha must be a lowercase 40-character Git SHA")
        return value

    @validator("size_bytes")
    def _size_is_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("size_bytes must be positive")
        return value

    @validator("sha256")
    def _sha256_is_valid(cls, value: str) -> str:
        if not _SHA256_RE.fullmatch(value):
            raise ValueError("sha256 must be a lowercase SHA-256 digest")
        return value

    class Config:
        allow_mutation = False


class PublicDataSource(BaseModel):
    source_id: str
    name: str
    upstream: UpstreamSource
    license: LicenseMetadata
    retrieved_at: datetime
    intended_use: str
    limitations: str
    artifacts: tuple[SourceArtifact, ...]

    _text_fields_are_present = validator("name", "intended_use", "limitations", allow_reuse=True)(_require_text)

    @validator("source_id")
    def _source_id_is_valid(cls, value: str) -> str:
        if not _SOURCE_ID_RE.fullmatch(value):
            raise ValueError("source_id must be lowercase kebab-case")
        return value

    @validator("retrieved_at")
    def _retrieved_at_has_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("retrieved_at must include timezone information")
        return value

    @validator("artifacts")
    def _artifacts_are_present(cls, value: tuple[SourceArtifact, ...]) -> tuple[SourceArtifact, ...]:
        if not value:
            raise ValueError("source must contain at least one artifact")
        return value

    @root_validator
    def _artifact_paths_are_unique(cls, values: dict) -> dict:
        artifacts = values.get("artifacts") or ()
        upstream_paths = [artifact.upstream_path for artifact in artifacts]
        local_paths = [artifact.local_path for artifact in artifacts]
        if len(set(upstream_paths)) != len(upstream_paths):
            raise ValueError("source contains duplicate upstream paths")
        if len(set(local_paths)) != len(local_paths):
            raise ValueError("source contains duplicate local paths")
        return values

    class Config:
        allow_mutation = False


class SourceRegistry(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    sources: tuple[PublicDataSource, ...]

    @validator("sources")
    def _sources_are_present(cls, value: tuple[PublicDataSource, ...]) -> tuple[PublicDataSource, ...]:
        if not value:
            raise ValueError("registry must contain at least one source")
        return value

    @root_validator
    def _source_ids_are_unique(cls, values: dict) -> dict:
        sources = values.get("sources") or ()
        source_ids = [source.source_id for source in sources]
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("registry contains duplicate source IDs")
        return values

    class Config:
        allow_mutation = False


class ValidatedSourceArtifact(BaseModel):
    source_id: str
    path: Path
    size_bytes: int
    sha256: str

    class Config:
        allow_mutation = False


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_source_registry(registry_path: Path) -> SourceRegistry:
    """Load and validate a public-source registry without side effects."""
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
        return SourceRegistry.parse_obj(payload)
    except (OSError, json.JSONDecodeError, ValidationError, TypeError, ValueError) as error:
        raise SourceRegistryValidationError(f"invalid public-source registry: {error}") from error


def validate_source_registry(
    data_root: Path,
    registry_path: Path,
) -> tuple[ValidatedSourceArtifact, ...]:
    """Validate registered artifacts using only the explicitly supplied local root."""
    root = data_root.resolve()
    registry = load_source_registry(registry_path)
    results: list[ValidatedSourceArtifact] = []

    for source in registry.sources:
        for artifact in source.artifacts:
            path = (root / artifact.local_path).resolve()
            if not path.is_relative_to(root):
                raise SourceRegistryValidationError(f"local path escapes data root: {artifact.local_path}")
            if not path.is_file():
                raise SourceRegistryValidationError(f"missing local artifact: {artifact.local_path}")
            actual_size = path.stat().st_size
            if actual_size != artifact.size_bytes:
                raise SourceRegistryValidationError(
                    "local artifact size mismatch: "
                    f"{artifact.local_path} expected {artifact.size_bytes}, found {actual_size}"
                )
            actual_sha256 = _sha256(path)
            if actual_sha256 != artifact.sha256:
                raise SourceRegistryValidationError(
                    "local artifact SHA-256 mismatch: "
                    f"{artifact.local_path} expected {artifact.sha256}, found {actual_sha256}"
                )
            results.append(
                ValidatedSourceArtifact(
                    source_id=source.source_id,
                    path=path,
                    size_bytes=actual_size,
                    sha256=actual_sha256,
                )
            )

    return tuple(results)
