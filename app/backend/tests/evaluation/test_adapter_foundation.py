from __future__ import annotations

import json
from uuid import UUID

import pytest

from hospital_ai.evaluation.adapter_foundation import (
    EvaluatorIsolationConfig,
    EvidenceResolutionError,
    ResolvedEvidence,
    RuntimeEvidenceChunk,
    SourceEvidenceResolver,
    materialize_evaluation_actor,
)
from hospital_ai.evaluation.benchmark import ActorIdentity, EvalCaseV2
from hospital_ai.evaluation.corpus_manifest import EvidenceLocator, build_corpus_manifest
from hospital_ai.evaluation.runner import CaseObservation, _evaluate_observation

DATA_ROOT = __import__("pathlib").Path(__file__).parents[2] / "data"


@pytest.fixture(scope="module")
def resolver() -> SourceEvidenceResolver:
    return SourceEvidenceResolver(build_corpus_manifest(DATA_ROOT))


def _runtime_chunk(resolver: SourceEvidenceResolver, locator: EvidenceLocator, **changes) -> RuntimeEvidenceChunk:
    artifact = resolver.artifact_for(locator)
    values = {
        "runtime_chunk_id": "runtime-chunk-1",
        "source_path": locator.source_path,
        "source_sha256": artifact.source_sha256,
        "patient_id": artifact.patient_id,
        "page_number": locator.page_number,
        "row_number": locator.row_number,
        "record_id": locator.record_id,
    }
    values.update(changes)
    return RuntimeEvidenceChunk(**values)


def test_source_resolver_maps_pdf_locator_by_hash_page_and_patient(resolver: SourceEvidenceResolver) -> None:
    locator = EvidenceLocator(source_path="patients_documents/patient_MRN0001_lab_result.pdf", page_number=1)

    resolved = resolver.resolve(locator, (_runtime_chunk(resolver, locator),))

    assert resolved.runtime_chunk_id == "runtime-chunk-1"
    assert resolved.source_sha256 == resolver.artifact_for(locator).source_sha256
    assert resolved.page_number == 1
    assert resolved.evidence_id == resolver.evidence_id(locator)


def test_source_resolver_maps_csv_locator_by_hash_and_exact_row(resolver: SourceEvidenceResolver) -> None:
    locator = EvidenceLocator(source_path="patients_labs/patient_MRN0001_labs.csv", row_number=2)

    resolved = resolver.resolve(locator, (_runtime_chunk(resolver, locator),))

    assert resolved.row_number == 2
    assert "row=2" in resolved.evidence_id


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"source_sha256": None}, "missing source hash"),
        ({"source_sha256": "f" * 64}, "stale source hash"),
        ({"page_number": 2}, "coordinate"),
        ({"patient_id": UUID("00000000-0000-0000-0000-000000000001")}, "patient"),
    ],
)
def test_source_resolver_fails_closed_for_incomplete_or_stale_provenance(
    resolver: SourceEvidenceResolver, changes: dict, message: str
) -> None:
    locator = EvidenceLocator(source_path="patients_documents/patient_MRN0001_lab_result.pdf", page_number=1)

    with pytest.raises(EvidenceResolutionError, match=message):
        resolver.resolve(locator, (_runtime_chunk(resolver, locator, **changes),))


def test_source_resolver_fails_closed_for_missing_and_ambiguous_runtime_chunks(
    resolver: SourceEvidenceResolver,
) -> None:
    locator = EvidenceLocator(source_path="patients_documents/patient_MRN0001_lab_result.pdf", page_number=1)
    first = _runtime_chunk(resolver, locator)
    second = _runtime_chunk(resolver, locator, runtime_chunk_id="runtime-chunk-2")

    with pytest.raises(EvidenceResolutionError, match="no runtime chunk"):
        resolver.resolve(locator, ())
    with pytest.raises(EvidenceResolutionError, match="ambiguous"):
        resolver.resolve(locator, (first, second))


def test_resolver_revalidates_structured_observations_instead_of_trusting_their_id(
    resolver: SourceEvidenceResolver,
) -> None:
    locator = EvidenceLocator(source_path="patients_documents/patient_MRN0001_lab_result.pdf", page_number=1)
    artifact = resolver.artifact_for(locator)
    forged = ResolvedEvidence(
        evidence_id=resolver.evidence_id(locator),
        runtime_chunk_id="forged-runtime-chunk",
        source_path=locator.source_path,
        source_sha256="f" * 64,
        patient_id=artifact.patient_id,
        page_number=1,
    )

    with pytest.raises(EvidenceResolutionError, match="stale source hash"):
        resolver.validate_resolved(forged)


def test_runner_does_not_accept_unstructured_ids_as_provenance(resolver: SourceEvidenceResolver) -> None:
    first_row = json.loads(
        (DATA_ROOT / "evaluation" / "rag_benchmark_v2.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    case = EvalCaseV2.parse_obj(first_row)
    evidence_id = resolver.evidence_id(case.allowed_evidence[0])

    result = _evaluate_observation(
        case,
        "retrieval",
        CaseObservation(retrieved_ids=(evidence_id,), provenance_ids=(evidence_id,)),
        resolver,
    )

    provenance_gate = next(gate for gate in result.gates if gate.name == "complete_evidence_provenance")
    assert not provenance_gate.passed


def test_isolation_config_rejects_product_or_unmarked_databases() -> None:
    product = "postgresql+asyncpg://hospital_ai:secret@localhost:5432/hospital_ai"

    with pytest.raises(ValueError, match="product database"):
        EvaluatorIsolationConfig(
            evaluation_database_url=product,
            product_database_url=product,
            run_namespace="ai-eval/run-001",
        )
    with pytest.raises(ValueError, match="evaluation-specific"):
        EvaluatorIsolationConfig(
            evaluation_database_url="postgresql+asyncpg://hospital_ai:secret@localhost:5432/hospital_shadow",
            product_database_url=product,
            run_namespace="ai-eval/run-001",
        )


def test_actor_materialization_is_deterministic_and_does_not_write_a_database() -> None:
    isolation = EvaluatorIsolationConfig(
        evaluation_database_url="postgresql+asyncpg://hospital_ai:secret@localhost:5432/hospital_ai_eval",
        product_database_url="postgresql+asyncpg://hospital_ai:secret@localhost:5432/hospital_ai",
        run_namespace="ai-eval/run-001",
    )
    source = ActorIdentity(
        actor_id=UUID("11111111-1111-1111-1111-111111111111"),
        role="clinician",
        allowed_patient_ids=(UUID("22222222-2222-2222-2222-222222222222"),),
    )

    first = materialize_evaluation_actor(source, isolation)
    second = materialize_evaluation_actor(source, isolation)

    assert first == second
    assert first.role == "doctor"
    assert first.allowed_patient_ids == source.allowed_patient_ids
    assert first.email.endswith("@example.invalid")
    assert isolation.transaction_mode == "rollback_only"
