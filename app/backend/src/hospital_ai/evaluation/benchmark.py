"""Deterministic, evidence-only RAG value benchmark contracts."""
from collections import Counter
from enum import Enum
from typing import Any, Iterable, Literal, NamedTuple, Optional
import hashlib
from uuid import UUID, uuid5

from pydantic import BaseModel, Field

_NAMESPACE = UUID("8f2c8c4e-9b48-5b2f-9c1c-2f3c8f2d2e10")
CATEGORY_MINIMA = {"single_hop": 70, "multi_document": 50, "temporal_conflict": 35, "graph_only": 45, "overlapping_patient": 30, "permission_adversarial": 45, "safe_refusal": 25}

class ActorFixture(BaseModel):
    user_id: UUID
    role: str = "clinician"
    allowed_patient_ids: tuple[UUID, ...] = ()
    class Config: frozen = True

class CorpusManifest(BaseModel):
    corpus_version: str = "synthetic-100-v1"
    patients: tuple[UUID, ...] = ()
    source_rows: tuple[str, ...] = ()
    chunk_ids: tuple[UUID, ...] = ()
    class Config: frozen = True

class ExpectedFact(BaseModel):
    fact_id: str
    statement: str
    source_row_id: str
    class Config: frozen = True

class ExpectedCitation(BaseModel):
    chunk_id: UUID
    source_row_id: str

class PermissionFixture(BaseModel):
    actor: ActorFixture
    patient_id: UUID
    permitted: bool
    class Config: frozen = True

class GraphExpectation(BaseModel):
    required_nodes: tuple[str, ...] = ()
    required_edges: tuple[tuple[str, str, str], ...] = ()

class ReviewRecord(BaseModel):
    status: str = "agent-reviewed"
    reviewers: tuple[str, ...] = ("benchmark-reviewer-a", "benchmark-reviewer-b")
    source_hashes: tuple[str, ...] = ()

class BenchmarkCase(BaseModel):
    case_id: str
    schema_version: Literal["1.0"] = "1.0"
    corpus_version: str = "synthetic-100-v1"
    patient_id: UUID
    actor: ActorFixture
    question: str
    category: str
    expected_facts: tuple[ExpectedFact, ...]
    allowed_chunk_ids: tuple[UUID, ...] = ()
    forbidden_chunk_ids: tuple[UUID, ...] = ()
    expected_citations: tuple[ExpectedCitation, ...] = ()
    graph: Optional[GraphExpectation] = None
    answer_policy: Literal["answer", "scoped_refusal", "safe_no_evidence"] = "answer"
    expected_answer_text: None = None
    review: ReviewRecord = Field(default_factory=ReviewRecord)
    permission: Optional[PermissionFixture] = None
    class Config: frozen = True

class BenchmarkValidationResult(NamedTuple):
    valid: bool
    errors: tuple[str, ...]

def _uid(*parts: Any) -> UUID:
    return uuid5(_NAMESPACE, ":".join(map(str, parts)))

def generate_benchmark(manifest: CorpusManifest | None = None, seed: int = 20260722) -> tuple[BenchmarkCase, ...]:
    manifest = manifest or CorpusManifest()
    cases = []
    for category, count in CATEGORY_MINIMA.items():
        for index in range(count):
            patient = manifest.patients[index % len(manifest.patients)] if manifest.patients else _uid(seed, "patient", index % 100)
            chunk = manifest.chunk_ids[index % len(manifest.chunk_ids)] if manifest.chunk_ids else _uid(seed, category, index, "chunk")
            actor = ActorFixture(user_id=_uid(seed, "actor", index), allowed_patient_ids=(patient,))
            policy = "safe_no_evidence" if category == "safe_refusal" else ("scoped_refusal" if category == "permission_adversarial" else "answer")
            row = manifest.source_rows[index % len(manifest.source_rows)] if manifest.source_rows else f"row-{index % 100:03d}"
            fact = ExpectedFact(fact_id=f"{category}-{index:03d}", statement=f"Canonical {category} fact {index}", source_row_id=row)
            denied = category == "permission_adversarial"
            cases.append(BenchmarkCase(case_id=f"rag-v1-{category}-{index:03d}", corpus_version=manifest.corpus_version, patient_id=patient, actor=actor, question=f"What is the canonical {category} fact for patient {patient}?", category=category, expected_facts=(fact,), allowed_chunk_ids=() if policy != "answer" or denied else (chunk,), forbidden_chunk_ids=(chunk,) if denied else (_uid(seed, "forbidden", index),), expected_citations=() if policy != "answer" or denied else (ExpectedCitation(chunk_id=chunk, source_row_id=fact.source_row_id),), graph=GraphExpectation(required_nodes=(str(patient),), required_edges=((str(patient), "has_fact", fact.fact_id),)) if category == "graph_only" else None, answer_policy=policy, permission=PermissionFixture(actor=actor, patient_id=patient, permitted=not denied) if denied else None))
    return tuple(cases)

def validate_benchmark(cases: Iterable[BenchmarkCase]) -> BenchmarkValidationResult:
    cases = tuple(cases); errors = []
    counts = Counter(c.category for c in cases)
    if len(cases) != 300: errors.append(f"expected exactly 300 cases, got {len(cases)}")
    for category, minimum in CATEGORY_MINIMA.items():
        if counts[category] != minimum: errors.append(f"{category}: expected {minimum}, got {counts[category]}")
    for case in cases:
        if case.expected_answer_text is not None: errors.append(f"{case.case_id}: prose answer is forbidden")
        if set(case.allowed_chunk_ids) & set(case.forbidden_chunk_ids): errors.append(f"{case.case_id}: evidence overlap")
        if not case.expected_facts: errors.append(f"{case.case_id}: no ground truth facts")
        if case.category == "permission_adversarial" and (case.permission is None or case.permission.permitted or case.answer_policy != "scoped_refusal"): errors.append(f"{case.case_id}: invalid permission fixture")
        if case.category == "safe_refusal" and case.answer_policy != "safe_no_evidence": errors.append(f"{case.case_id}: invalid refusal policy")
        if case.category == "graph_only" and not case.graph or (case.graph and not case.graph.required_edges): errors.append(f"{case.case_id}: missing graph path")
    if len({c.case_id for c in cases}) != len(cases): errors.append("duplicate case IDs")
    return BenchmarkValidationResult(not errors, tuple(errors))
