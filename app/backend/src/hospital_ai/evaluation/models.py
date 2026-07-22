"""Pydantic contracts for the canonical RAG corpus."""

from __future__ import annotations

from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class _FrozenModel(BaseModel):
    """Compatibility base for the repository's Pydantic 1.x runtime."""

    class Config:
        allow_mutation = False
        extra = "forbid"


class CorpusFile(_FrozenModel):
    relative_path: str
    sha256: str = Field(regex=r"^[0-9a-f]{64}$")
    byte_size: int = Field(gt=0)
    patient_id: Optional[UUID]  # noqa: UP007  # Pydantic 1.x runs here on Python 3.9.
    document_id: str
    document_type: str
    mime_type: str
    generator: str
    generator_version: str
    source: str
    synthetic: bool
    license_state: Literal["synthetic-approved", "pending-review"]
    classification: Literal["patient_record", "public_knowledge", "audit_fixture", "metadata"]
    quarantine_state: Literal["active", "excluded_pending_review"]
    runtime_approved: bool


class CorpusManifest(_FrozenModel):
    schema_version: Literal["1.0"]
    corpus_version: str
    patient_count: int = Field(ge=0)
    patient_record_count: int = Field(ge=0)
    files: tuple[CorpusFile, ...]


class CorpusValidationResult(_FrozenModel):
    is_valid: bool
    patient_count: int = Field(ge=0)
    patient_record_count: int = Field(ge=0)
    duplicate_digest_count: int = Field(ge=0)
    orphan_patient_file_count: int = Field(ge=0)
    mismatch_patient_file_count: int = Field(ge=0)
    null_ownership_count: int = Field(ge=0)
    errors: tuple[str, ...]
