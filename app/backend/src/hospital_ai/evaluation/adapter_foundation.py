"""Fail-closed contracts shared by future live evaluation adapters.

This module deliberately does not call product services or open a database.  It
defines the provenance and isolation boundary that a concrete adapter must
satisfy before the evaluator can trust its observations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID, uuid5

from pydantic import BaseModel, root_validator, validator
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from hospital_ai.evaluation.benchmark import ActorIdentity, EvalCaseV2
from hospital_ai.evaluation.corpus_manifest import CorpusManifestV2, EvidenceLocator, SourceArtifact

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EVALUATION_DATABASE_RE = re.compile(r"(?:^|[_-])(?:eval|evaluation|test)(?:[_-]|$)", re.IGNORECASE)
_ACTOR_NAMESPACE = UUID("eb66d7ba-0ba5-5af7-9daa-d17c10831e4c")
_PRODUCT_ROLES = {
    "doctor",
    "nurse",
    "pharmacist",
    "lab_staff",
    "records_staff",
    "security",
    "admin",
    "front_desk",
}
_ROLE_ALIASES = {"clinician": "doctor"}


class EvidenceResolutionError(ValueError):
    """Raised when a source locator cannot resolve to one trustworthy chunk."""


class EvaluationIsolationError(ValueError):
    """Raised when evaluator execution is not provably isolated from product data."""


class RuntimeEvidenceChunk(BaseModel):
    """Minimum provenance a product adapter must attach to a runtime chunk."""

    runtime_chunk_id: str
    source_path: str
    source_sha256: str | None
    patient_id: UUID | None = None
    page_number: int | None = None
    row_number: int | None = None
    record_id: str | None = None

    @validator("runtime_chunk_id", "source_path")
    def _non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("runtime evidence identifiers must not be blank")
        return value

    @validator("source_sha256")
    def _valid_hash(cls, value: str | None) -> str | None:
        if value is not None and not _SHA256_RE.fullmatch(value):
            raise ValueError("runtime source hash must be lowercase SHA-256")
        return value

    @validator("page_number", "row_number")
    def _positive_coordinate(cls, value: int | None) -> int | None:
        if value is not None and value < 1:
            raise ValueError("runtime evidence coordinates must be positive")
        return value

    class Config:
        frozen = True


class ResolvedEvidence(BaseModel):
    """A runtime chunk cryptographically tied to one canonical locator."""

    evidence_id: str
    runtime_chunk_id: str
    source_path: str
    source_sha256: str
    patient_id: UUID | None = None
    page_number: int | None = None
    row_number: int | None = None
    record_id: str | None = None

    class Config:
        frozen = True


class SourceEvidenceResolver:
    """Resolve source locators without trusting runtime UUIDs as ground truth."""

    def __init__(
        self,
        manifest: CorpusManifestV2,
        candidate_locators: tuple[EvidenceLocator, ...] | None = None,
    ) -> None:
        self._manifest = manifest
        artifacts = manifest.artifacts
        by_path = {artifact.canonical_relative_path: artifact for artifact in artifacts}
        if len(by_path) != len(artifacts):
            raise EvidenceResolutionError("canonical manifest contains ambiguous source paths")
        self._by_path = by_path
        candidates = (
            candidate_locators
            if candidate_locators is not None
            else tuple(EvidenceLocator(source_path=artifact.canonical_relative_path) for artifact in artifacts)
        )
        self._candidates = {self._locator_key(locator): locator for locator in candidates}

    def for_case(self, case: EvalCaseV2) -> SourceEvidenceResolver:
        """Constrain adapter provenance to the exact evidence contract for one case."""

        return SourceEvidenceResolver(
            self._manifest,
            candidate_locators=(case.allowed_evidence + case.forbidden_evidence + case.absence_checked_evidence),
        )

    @staticmethod
    def _locator_key(locator: EvidenceLocator) -> tuple[str, int | None, int | None, str | None]:
        return (locator.source_path, locator.page_number, locator.row_number, locator.record_id)

    def artifact_for(self, locator: EvidenceLocator) -> SourceArtifact:
        artifact = self._by_path.get(locator.source_path)
        if artifact is None:
            raise EvidenceResolutionError(f"locator source is not canonical: {locator.source_path}")
        return artifact

    def evidence_id(self, locator: EvidenceLocator) -> str:
        artifact = self.artifact_for(locator)
        return "|".join(
            (
                f"sha256={artifact.source_sha256}",
                f"path={locator.source_path}",
                f"page={locator.page_number or ''}",
                f"row={locator.row_number or ''}",
                f"record={locator.record_id or ''}",
            )
        )

    def resolve(
        self,
        locator: EvidenceLocator,
        candidates: tuple[RuntimeEvidenceChunk, ...],
    ) -> ResolvedEvidence:
        artifact = self.artifact_for(locator)
        same_source = tuple(candidate for candidate in candidates if candidate.source_path == locator.source_path)
        if not same_source:
            raise EvidenceResolutionError(f"no runtime chunk for source locator: {locator.source_path}")
        if any(candidate.source_sha256 is None for candidate in same_source):
            raise EvidenceResolutionError(f"missing source hash for runtime evidence: {locator.source_path}")
        if any(candidate.source_sha256 != artifact.source_sha256 for candidate in same_source):
            raise EvidenceResolutionError(f"stale source hash for runtime evidence: {locator.source_path}")
        if any(candidate.patient_id != artifact.patient_id for candidate in same_source):
            raise EvidenceResolutionError(f"patient provenance mismatch for runtime evidence: {locator.source_path}")

        exact = tuple(
            candidate
            for candidate in same_source
            if candidate.page_number == locator.page_number
            and candidate.row_number == locator.row_number
            and candidate.record_id == locator.record_id
        )
        if not exact:
            raise EvidenceResolutionError(f"runtime evidence coordinate does not match locator: {locator.source_path}")
        if len(exact) != 1:
            raise EvidenceResolutionError(f"ambiguous runtime chunks for source locator: {locator.source_path}")
        match = exact[0]
        assert match.source_sha256 is not None
        return ResolvedEvidence(
            evidence_id=self.evidence_id(locator),
            runtime_chunk_id=match.runtime_chunk_id,
            source_path=match.source_path,
            source_sha256=match.source_sha256,
            patient_id=match.patient_id,
            page_number=match.page_number,
            row_number=match.row_number,
            record_id=match.record_id,
        )

    def resolve_runtime(self, runtime: RuntimeEvidenceChunk) -> ResolvedEvidence:
        """Resolve only a runtime observation registered before adapter execution."""
        locator = EvidenceLocator(
            source_path=runtime.source_path,
            page_number=runtime.page_number,
            row_number=runtime.row_number,
            record_id=runtime.record_id,
        )
        registered = self._candidates.get(self._locator_key(locator))
        if registered is None:
            raise EvidenceResolutionError("runtime evidence is not a registered canonical candidate")
        return self.resolve(registered, (runtime,))

    def resolve_runtimes(self, runtimes: tuple[RuntimeEvidenceChunk, ...]) -> tuple[ResolvedEvidence, ...]:
        """Resolve an ordered observation after rejecting duplicate locator claims."""

        locator_keys = tuple(
            self._locator_key(
                EvidenceLocator(
                    source_path=runtime.source_path,
                    page_number=runtime.page_number,
                    row_number=runtime.row_number,
                    record_id=runtime.record_id,
                )
            )
            for runtime in runtimes
        )
        if len(set(locator_keys)) != len(locator_keys):
            raise EvidenceResolutionError("duplicate runtime chunks per locator")
        return tuple(self.resolve_runtime(runtime) for runtime in runtimes)

    def validate_resolved(self, evidence: ResolvedEvidence) -> str:
        """Re-check a structured observation; its claimed evidence ID is untrusted."""

        locator = EvidenceLocator(
            source_path=evidence.source_path,
            page_number=evidence.page_number,
            row_number=evidence.row_number,
            record_id=evidence.record_id,
        )
        artifact = self.artifact_for(locator)
        if evidence.source_sha256 != artifact.source_sha256:
            raise EvidenceResolutionError(f"stale source hash for resolved evidence: {evidence.source_path}")
        if evidence.patient_id != artifact.patient_id:
            raise EvidenceResolutionError(f"patient provenance mismatch for resolved evidence: {evidence.source_path}")
        if self._candidates.get(self._locator_key(locator)) is None:
            raise EvidenceResolutionError("resolved evidence is not a registered canonical candidate")
        expected_id = self.evidence_id(locator)
        if evidence.evidence_id != expected_id:
            raise EvidenceResolutionError(
                f"fabricated evidence identifier for resolved evidence: {evidence.source_path}"
            )
        return expected_id


def _database_identity(raw_url: str) -> tuple[str, str | None, int | None, str]:
    try:
        url = make_url(raw_url)
    except ArgumentError as error:
        raise EvaluationIsolationError("evaluator database URL is invalid") from error
    database = url.database or ""
    driver = url.drivername.split("+", 1)[0]
    host = (url.host or "").lower()
    if host in {"localhost", "127.0.0.1", "::1"}:
        host = "loopback"
    port = url.port or (5432 if driver.startswith("postgresql") else None)
    return driver, host, port, database


class EvaluatorIsolationConfig(BaseModel):
    """Configuration proof that adapters cannot target the product database."""

    evaluation_database_url: str
    approved_evaluation_database_url: str
    product_database_url: str
    run_namespace: str
    transaction_mode: Literal["rollback_only"] = "rollback_only"

    @validator("evaluation_database_url", "approved_evaluation_database_url", "product_database_url", "run_namespace")
    def _non_empty_value(cls, value: str) -> str:
        if not value.strip():
            raise EvaluationIsolationError("isolation configuration values must not be blank")
        return value

    @validator("run_namespace")
    def _evaluation_namespace(cls, value: str) -> str:
        if not value.startswith("ai-eval/"):
            raise EvaluationIsolationError("run namespace must start with ai-eval/")
        return value

    @root_validator
    def _database_is_isolated(cls, values: dict) -> dict:
        evaluation_url = values.get("evaluation_database_url")
        approved_url = values.get("approved_evaluation_database_url")
        product_url = values.get("product_database_url")
        if not evaluation_url or not approved_url or not product_url:
            return values
        evaluation_identity = _database_identity(evaluation_url)
        approved_identity = _database_identity(approved_url)
        product_identity = _database_identity(product_url)
        if evaluation_identity == product_identity:
            raise EvaluationIsolationError("isolated evaluator must not use the product database")
        if evaluation_identity != approved_identity:
            raise EvaluationIsolationError("evaluator database identity is not explicitly approved")

        driver, _host, _port, database = evaluation_identity
        is_memory_sqlite = driver.startswith("sqlite") and database == ":memory:"
        database_name = urlsplit(f"file:///{database}").path.rsplit("/", 1)[-1]
        if not is_memory_sqlite and not _EVALUATION_DATABASE_RE.search(database_name):
            raise EvaluationIsolationError("evaluator database name must contain an evaluation-specific marker")
        return values

    class Config:
        frozen = True


class MaterializedEvaluationActor(BaseModel):
    actor_id: UUID
    source_actor_id: UUID
    email: str
    full_name: str
    role: str
    allowed_patient_ids: tuple[UUID, ...]
    run_namespace: str

    class Config:
        frozen = True


def materialize_evaluation_actor(
    source: ActorIdentity,
    isolation: EvaluatorIsolationConfig,
) -> MaterializedEvaluationActor:
    """Create an immutable actor specification; no database write occurs here."""

    role = _ROLE_ALIASES.get(source.role, source.role)
    if role not in _PRODUCT_ROLES:
        raise EvaluationIsolationError(f"benchmark actor role cannot map to a product role: {source.role}")
    actor_id = uuid5(_ACTOR_NAMESPACE, f"{isolation.run_namespace}:{source.actor_id}")
    return MaterializedEvaluationActor(
        actor_id=actor_id,
        source_actor_id=source.actor_id,
        email=f"ai-eval+{actor_id.hex}@example.invalid",
        full_name=f"AI Evaluation Actor {actor_id.hex[:8]}",
        role=role,
        allowed_patient_ids=source.allowed_patient_ids,
        run_namespace=isolation.run_namespace,
    )


@dataclass(frozen=True)
class EvaluationCaseContext:
    actor: MaterializedEvaluationActor
    evidence_resolver: SourceEvidenceResolver
    isolation: EvaluatorIsolationConfig
