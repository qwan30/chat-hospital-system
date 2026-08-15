"""Unit tests for the ProductTimelineAdapter."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import pytest

from hospital_ai.evaluation.adapter_foundation import (
    EvaluationCaseContext,
    EvaluatorIsolationConfig,
    EvidenceResolutionError,
    SourceEvidenceResolver,
    materialize_evaluation_actor,
)
from hospital_ai.evaluation.benchmark import ActorIdentity, EvalCaseV2, ExpectedFact, ReviewRecord
from hospital_ai.evaluation.corpus_manifest import (
    CorpusManifestV2,
    EvidenceLocator,
    SourceArtifact,
)
from hospital_ai.evaluation.product_timeline_adapter import ProductTimelineAdapter


def _artifact(
    source_root: Path,
    *,
    patient_id: uuid.UUID,
    relative_path: str,
    locator: EvidenceLocator,
    content: bytes = b"Patient lab results over time.",
) -> SourceArtifact:
    payload = content
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


def _context(manifest: CorpusManifestV2, *, actor_patient_ids: tuple[uuid.UUID, ...]) -> EvaluationCaseContext:
    source_actor = ActorIdentity(actor_id=uuid.uuid4(), role="clinician", allowed_patient_ids=actor_patient_ids)
    isolation = EvaluatorIsolationConfig(
        evaluation_database_url="sqlite+aiosqlite:///:memory:",
        approved_evaluation_database_url="sqlite+aiosqlite:///:memory:",
        product_database_url="sqlite+aiosqlite:///product.db",
        run_namespace="ai-eval/test-timeline-adapter",
    )
    return EvaluationCaseContext(
        actor=materialize_evaluation_actor(source_actor, isolation),
        evidence_resolver=SourceEvidenceResolver(manifest),
        isolation=isolation,
    )


def _case(*, patient_id: uuid.UUID, actor_patient_ids: tuple[uuid.UUID, ...], locator: EvidenceLocator) -> EvalCaseV2:
    return EvalCaseV2(
        case_id="TIMELINE-001",
        corpus_version="synthetic-100-v2",
        category="single_hop",
        patient_id=patient_id,
        actor=ActorIdentity(actor_id=uuid.uuid4(), role="clinician", allowed_patient_ids=actor_patient_ids),
        patient_scope=(patient_id,),
        question="What is the patient's lab history?",
        answer_policy="answer",
        expected_facts=(
            ExpectedFact(
                fact_id="F-001",
                statement="Patient lab results over time",
                evidence=(locator,),
                verification_terms=("lab",),
            ),
        ),
        allowed_evidence=(locator,),
        forbidden_evidence=(),
        review=ReviewRecord(status="approved", reviewer_ids=("reviewer",)),
    )


@pytest.mark.asyncio
async def test_timeline_adapter_calls_real_timeline_service(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_documents/timeline.txt", page_number=1)
    artifact = _artifact(tmp_path, patient_id=patient_id, relative_path=locator.source_path, locator=locator)
    manifest = CorpusManifestV2(artifacts=(artifact,))
    context = _context(manifest, actor_patient_ids=(patient_id,))
    case = _case(patient_id=patient_id, actor_patient_ids=(patient_id,), locator=locator)

    adapter = ProductTimelineAdapter(tmp_path)
    observation = await adapter.evaluate(case, context, filters={"event_type": "all"})
    assert observation.superseded_retrieval_count == 0
    assert hasattr(observation, "timeline_events")
    assert isinstance(observation.timeline_events, tuple)


@pytest.mark.asyncio
async def test_timeline_adapter_rejects_unauthorized_actor(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    other_patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_documents/timeline.txt", page_number=1)
    artifact = _artifact(tmp_path, patient_id=patient_id, relative_path=locator.source_path, locator=locator)
    manifest = CorpusManifestV2(artifacts=(artifact,))
    context = _context(manifest, actor_patient_ids=(other_patient_id,))
    case = _case(patient_id=patient_id, actor_patient_ids=(other_patient_id,), locator=locator)

    adapter = ProductTimelineAdapter(tmp_path)
    with pytest.raises(EvidenceResolutionError, match="not authorized"):
        await adapter.evaluate(case, context)
