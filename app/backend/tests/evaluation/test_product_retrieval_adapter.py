from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import fitz
import pytest

from hospital_ai.evaluation.adapter_foundation import (
    EvaluationCaseContext,
    EvaluatorIsolationConfig,
    EvidenceResolutionError,
    SourceEvidenceResolver,
    materialize_evaluation_actor,
)
from hospital_ai.evaluation.benchmark import ActorIdentity, EvalCaseV2, ExpectedFact, ReviewRecord
from hospital_ai.evaluation.corpus_manifest import CorpusManifestV2, EvidenceLocator, SourceArtifact
from hospital_ai.evaluation.product_retrieval_adapter import ProductRetrievalAdapter


def _artifact(
    source_root: Path,
    *,
    patient_id: uuid.UUID,
    relative_path: str,
    locator: EvidenceLocator,
) -> SourceArtifact:
    payload = b"Patient has an allergy to penicillin and needs allergy documentation."
    target = source_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return SourceArtifact(
        source_sha256=hashlib.sha256(payload).hexdigest(),
        canonical_relative_path=relative_path,
        kind="patient_document",
        patient_id=patient_id,
        mime_type="text/plain",
        document_type="note",
        generator="test",
        generator_version="1",
        provenance_status="approved",
        license_status="synthetic",
        locator=locator,
    )


def _pdf_artifact(source_root: Path, *, patient_id: uuid.UUID, locator: EvidenceLocator) -> SourceArtifact:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Patient has an allergy to penicillin and needs allergy documentation.")
    payload = document.tobytes()
    document.close()
    target = source_root / locator.source_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return SourceArtifact(
        source_sha256=hashlib.sha256(payload).hexdigest(),
        canonical_relative_path=locator.source_path,
        kind="patient_document",
        patient_id=patient_id,
        mime_type="application/pdf",
        document_type="note",
        generator="test",
        generator_version="1",
        provenance_status="approved",
        license_status="synthetic",
        locator=locator,
    )


def _context(manifest: CorpusManifestV2, *, actor_patient_ids: tuple[uuid.UUID, ...]) -> EvaluationCaseContext:
    source_actor = ActorIdentity(actor_id=uuid.uuid4(), role="clinician", allowed_patient_ids=actor_patient_ids)
    isolation = EvaluatorIsolationConfig(
        evaluation_database_url="sqlite+aiosqlite:///:memory:",
        approved_evaluation_database_url="sqlite+aiosqlite:///:memory:",
        product_database_url="sqlite+aiosqlite:///product.db",
        run_namespace="ai-eval/test-retrieval-adapter",
    )
    return EvaluationCaseContext(
        actor=materialize_evaluation_actor(source_actor, isolation),
        evidence_resolver=SourceEvidenceResolver(manifest),
        isolation=isolation,
    )


def _case(*, patient_id: uuid.UUID, actor_patient_ids: tuple[uuid.UUID, ...], locator: EvidenceLocator) -> EvalCaseV2:
    return EvalCaseV2(
        case_id="adapter-case",
        corpus_version="synthetic-100-v2",
        category="single_hop",
        patient_id=patient_id,
        actor=ActorIdentity(actor_id=uuid.uuid4(), role="clinician", allowed_patient_ids=actor_patient_ids),
        patient_scope=(patient_id,),
        question="What allergy is documented?",
        answer_policy="answer",
        expected_facts=(
            ExpectedFact(
                fact_id="allergy",
                statement="Penicillin allergy",
                evidence=(locator,),
                verification_terms=("penicillin",),
            ),
        ),
        allowed_evidence=(locator,),
        forbidden_evidence=(),
        review=ReviewRecord(status="approved", reviewer_ids=("reviewer",)),
    )


@pytest.mark.asyncio
async def test_adapter_materializes_canonical_source_and_returns_actual_retrieval_provenance(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_documents/patient.pdf", page_number=1, record_id="note-1")
    artifact = _pdf_artifact(tmp_path, patient_id=patient_id, locator=locator)
    manifest = CorpusManifestV2(artifacts=(artifact,))
    context = _context(manifest, actor_patient_ids=(patient_id,))

    case = _case(patient_id=patient_id, actor_patient_ids=(patient_id,), locator=locator)
    observation = await ProductRetrievalAdapter(tmp_path).evaluate(case, context)

    assert len(observation.retrieved_evidence) == 1
    evidence = observation.retrieved_evidence[0]
    assert evidence.runtime_chunk_id
    assert evidence.source_path == locator.source_path
    assert evidence.source_sha256 == artifact.source_sha256
    assert evidence.patient_id == patient_id
    assert evidence.page_number == 1
    assert evidence.record_id == "note-1"
    resolved = context.evidence_resolver.for_case(case).resolve_runtimes(observation.retrieved_evidence)
    assert resolved[0].source_sha256 == artifact.source_sha256


@pytest.mark.asyncio
async def test_adapter_fails_closed_when_actor_lacks_patient_scope(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_documents/patient.txt", page_number=1)
    artifact = _artifact(tmp_path, patient_id=patient_id, relative_path=locator.source_path, locator=locator)
    manifest = CorpusManifestV2(artifacts=(artifact,))
    context = _context(manifest, actor_patient_ids=())

    with pytest.raises(EvidenceResolutionError, match="not authorized"):
        await ProductRetrievalAdapter(tmp_path).evaluate(
            _case(patient_id=patient_id, actor_patient_ids=(), locator=locator), context
        )


@pytest.mark.asyncio
async def test_adapter_rejects_unknown_and_ambiguous_locators(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_documents/patient.txt", page_number=1)
    artifact = _artifact(tmp_path, patient_id=patient_id, relative_path=locator.source_path, locator=locator)
    context = _context(CorpusManifestV2(artifacts=(artifact,)), actor_patient_ids=(patient_id,))
    adapter = ProductRetrievalAdapter(tmp_path)

    unknown = locator.copy(update={"source_path": "patients_documents/missing.txt"})
    with pytest.raises(EvidenceResolutionError, match="not canonical"):
        await adapter.evaluate(_case(patient_id=patient_id, actor_patient_ids=(patient_id,), locator=unknown), context)

    ambiguous_case = _case(patient_id=patient_id, actor_patient_ids=(patient_id,), locator=locator).copy(
        update={"forbidden_evidence": (locator,)}
    )
    with pytest.raises(EvidenceResolutionError, match="ambiguous"):
        await adapter.evaluate(ambiguous_case, context)
