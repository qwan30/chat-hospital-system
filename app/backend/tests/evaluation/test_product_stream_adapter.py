"""Unit tests for ProductStreamAdapter involving SSE parsing and interrupted outcomes."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import pytest

from hospital_ai.evaluation.adapter_foundation import (
    EvaluationCaseContext,
    EvaluatorIsolationConfig,
    SourceEvidenceResolver,
    materialize_evaluation_actor,
)
from hospital_ai.evaluation.benchmark import ActorIdentity, EvalCaseV2, ExpectedFact, ReviewRecord
from hospital_ai.evaluation.corpus_manifest import (
    CorpusManifestV2,
    EvidenceLocator,
    SourceArtifact,
)
from hospital_ai.evaluation.product_stream_adapter import ProductStreamAdapter


def _artifact(
    source_root: Path,
    *,
    patient_id: uuid.UUID,
    relative_path: str,
    locator: EvidenceLocator,
    content: bytes = b"Patient is taking metformin 500mg daily.",
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
        run_namespace="ai-eval/test-stream-adapter",
    )
    return EvaluationCaseContext(
        actor=materialize_evaluation_actor(source_actor, isolation),
        evidence_resolver=SourceEvidenceResolver(manifest),
        isolation=isolation,
    )


def _case(*, patient_id: uuid.UUID, actor_patient_ids: tuple[uuid.UUID, ...], locator: EvidenceLocator) -> EvalCaseV2:
    return EvalCaseV2(
        case_id="STREAM-001",
        corpus_version="synthetic-100-v2",
        category="single_hop",
        patient_id=patient_id,
        actor=ActorIdentity(actor_id=uuid.uuid4(), role="clinician", allowed_patient_ids=actor_patient_ids),
        patient_scope=(patient_id,),
        question="What dose of metformin is the patient taking?",
        answer_policy="answer",
        expected_facts=(
            ExpectedFact(
                fact_id="F-001",
                statement="Patient taking metformin 500mg daily",
                evidence=(locator,),
                verification_terms=("metformin", "500mg"),
            ),
        ),
        allowed_evidence=(locator,),
        forbidden_evidence=(),
        review=ReviewRecord(status="approved", reviewer_ids=("reviewer",)),
    )


@pytest.mark.asyncio
async def test_stream_adapter_parses_sse_and_validates_sequence(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_documents/stream_doc.txt", page_number=1)
    artifact = _artifact(tmp_path, patient_id=patient_id, relative_path=locator.source_path, locator=locator)
    manifest = CorpusManifestV2(artifacts=(artifact,))
    context = _context(manifest, actor_patient_ids=(patient_id,))
    case = _case(patient_id=patient_id, actor_patient_ids=(patient_id,), locator=locator)

    adapter = ProductStreamAdapter(tmp_path)
    observation = await adapter.evaluate(case, context)
    assert observation.stream_safety_outcome == "answered"
    assert observation.sse_sequence_correct is True
    assert observation.sse_event_order_correct is True


@pytest.mark.asyncio
async def test_stream_adapter_handles_interrupted_outcome(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_documents/stream_doc.txt", page_number=1)
    artifact = _artifact(tmp_path, patient_id=patient_id, relative_path=locator.source_path, locator=locator)
    manifest = CorpusManifestV2(artifacts=(artifact,))
    context = _context(manifest, actor_patient_ids=(patient_id,))
    case = _case(patient_id=patient_id, actor_patient_ids=(patient_id,), locator=locator)

    adapter = ProductStreamAdapter(tmp_path)
    observation = await adapter.evaluate(case, context, simulate_interrupt=True)
    assert observation.stream_safety_outcome == "interrupted"
    assert observation.sse_interrupt_correct is True


@pytest.mark.asyncio
async def test_stream_adapter_handles_error_outcome(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_documents/stream_doc.txt", page_number=1)
    artifact = _artifact(tmp_path, patient_id=patient_id, relative_path=locator.source_path, locator=locator)
    manifest = CorpusManifestV2(artifacts=(artifact,))
    context = _context(manifest, actor_patient_ids=(patient_id,))
    case = _case(patient_id=patient_id, actor_patient_ids=(patient_id,), locator=locator)

    adapter = ProductStreamAdapter(tmp_path)
    observation = await adapter.evaluate(case, context, simulate_error=True)
    assert observation.stream_safety_outcome == "error"


@pytest.mark.asyncio
async def test_stream_adapter_refuses_when_actor_lacks_patient_permission(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    other_patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_documents/stream_doc.txt", page_number=1)
    artifact = _artifact(tmp_path, patient_id=patient_id, relative_path=locator.source_path, locator=locator)
    manifest = CorpusManifestV2(artifacts=(artifact,))
    context = _context(manifest, actor_patient_ids=(other_patient_id,))
    case = _case(patient_id=patient_id, actor_patient_ids=(other_patient_id,), locator=locator)

    adapter = ProductStreamAdapter(tmp_path)
    observation = await adapter.evaluate(case, context)
    assert observation.refused is True
    assert observation.stream_safety_outcome == "refused"
