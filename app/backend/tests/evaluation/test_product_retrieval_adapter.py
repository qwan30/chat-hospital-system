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
from hospital_ai.evaluation.benchmark import ActorIdentity, EvalCaseV2, ExpectedFact, GraphExpectation, ReviewRecord
from hospital_ai.evaluation.corpus_manifest import (
    CorpusManifestV2,
    EvidenceLocator,
    SourceArtifact,
    build_corpus_manifest,
)
from hospital_ai.evaluation.product_chat_adapter import ProductChatAdapter
from hospital_ai.evaluation.product_graph_adapter import ProductGraphAdapter
from hospital_ai.evaluation.product_retrieval_adapter import ProductRetrievalAdapter

BACKEND_ROOT = Path(__file__).parents[2]
DATA_ROOT = BACKEND_ROOT / "data"
BENCHMARK_DIR = DATA_ROOT / "evaluation"


def _artifact(
    source_root: Path,
    *,
    patient_id: uuid.UUID,
    relative_path: str,
    locator: EvidenceLocator,
    content: bytes = b"Patient has an allergy to penicillin and needs allergy documentation.",
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
@pytest.mark.parametrize("retrieval_mode", ["bm25", "hybrid"])
async def test_adapter_supports_source_backed_retrieval_ablations(
    tmp_path: Path,
    retrieval_mode: str,
) -> None:
    patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_documents/patient.txt", page_number=1)
    artifact = _artifact(
        tmp_path,
        patient_id=patient_id,
        relative_path=locator.source_path,
        locator=locator,
    )
    context = _context(CorpusManifestV2(artifacts=(artifact,)), actor_patient_ids=(patient_id,))

    observation = await ProductRetrievalAdapter(
        tmp_path,
        evidence_threshold=0.0,
        retrieval_mode=retrieval_mode,
    ).evaluate(
        _case(patient_id=patient_id, actor_patient_ids=(patient_id,), locator=locator),
        context,
    )

    assert len(observation.retrieved_evidence) == 1
    assert observation.retrieved_evidence[0].source_sha256 == artifact.source_sha256


def test_adapter_rejects_an_unknown_retrieval_mode(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="retrieval_mode"):
        ProductRetrievalAdapter(tmp_path, retrieval_mode="unknown")


@pytest.mark.asyncio
async def test_adapter_materializes_whole_pdf_for_absence_checked_locator(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_documents/patient.pdf")
    artifact = _pdf_artifact(tmp_path, patient_id=patient_id, locator=locator)
    context = _context(CorpusManifestV2(artifacts=(artifact,)), actor_patient_ids=(patient_id,))

    observation = await ProductRetrievalAdapter(tmp_path).evaluate(
        _case(patient_id=patient_id, actor_patient_ids=(patient_id,), locator=locator), context
    )

    assert len(observation.retrieved_evidence) == 1
    assert observation.retrieved_evidence[0].source_path == locator.source_path
    assert observation.retrieved_evidence[0].page_number is None


@pytest.mark.asyncio
async def test_adapter_materializes_whole_csv_for_absence_checked_locator(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_labs/patient.csv")
    artifact = _artifact(
        tmp_path,
        patient_id=patient_id,
        relative_path=locator.source_path,
        locator=locator,
        content=b"test,value\ncreatinine,1.1\n",
    ).copy(update={"mime_type": "text/csv", "document_type": "lab_result"})
    context = _context(CorpusManifestV2(artifacts=(artifact,)), actor_patient_ids=(patient_id,))

    observation = await ProductRetrievalAdapter(tmp_path, evidence_threshold=0.0).evaluate(
        _case(patient_id=patient_id, actor_patient_ids=(patient_id,), locator=locator), context
    )

    assert len(observation.retrieved_evidence) == 1
    assert observation.retrieved_evidence[0].source_path == locator.source_path
    assert observation.retrieved_evidence[0].row_number is None


@pytest.mark.asyncio
async def test_adapter_excludes_forbidden_generation_evidence_for_source_backed_safe_refusal() -> None:
    case = next(
        case
        for line in (BENCHMARK_DIR / "rag_sentinel_v2.jsonl").read_text(encoding="utf-8").splitlines()
        for case in (EvalCaseV2.parse_raw(line),)
        if case.category == "safe_refusal"
    )
    manifest = build_corpus_manifest(DATA_ROOT)
    context = _context(manifest, actor_patient_ids=case.actor.allowed_patient_ids)

    observation = await ProductRetrievalAdapter(DATA_ROOT, evidence_threshold=0.2).evaluate(case, context)
    forbidden = {
        (locator.source_path, locator.page_number, locator.row_number, locator.record_id)
        for locator in case.forbidden_evidence
    }
    observed = {
        (evidence.source_path, evidence.page_number, evidence.row_number, evidence.record_id)
        for evidence in observation.retrieved_evidence
    }

    assert observed.isdisjoint(forbidden)


@pytest.mark.asyncio
@pytest.mark.parametrize("retrieval_mode", ["bm25", "hybrid"])
async def test_lexical_retrieval_refuses_safe_no_evidence_without_returning_forbidden_source(
    retrieval_mode: str,
) -> None:
    case = next(
        case
        for line in (BENCHMARK_DIR / "rag_sentinel_v2.jsonl").read_text(encoding="utf-8").splitlines()
        for case in (EvalCaseV2.parse_raw(line),)
        if case.category == "safe_refusal"
    )
    manifest = build_corpus_manifest(DATA_ROOT)
    context = _context(manifest, actor_patient_ids=case.actor.allowed_patient_ids)

    observation = await ProductRetrievalAdapter(
        DATA_ROOT,
        evidence_threshold=0.2,
        retrieval_mode=retrieval_mode,
    ).evaluate(case, context)

    assert observation.retrieved_evidence == ()


@pytest.mark.asyncio
async def test_adapter_records_safe_refusal_when_actor_lacks_patient_scope(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_documents/patient.txt", page_number=1)
    artifact = _artifact(tmp_path, patient_id=patient_id, relative_path=locator.source_path, locator=locator)
    manifest = CorpusManifestV2(artifacts=(artifact,))
    context = _context(manifest, actor_patient_ids=())

    observation = await ProductRetrievalAdapter(tmp_path).evaluate(
        _case(patient_id=patient_id, actor_patient_ids=(), locator=locator), context
    )

    assert observation.refused is True
    assert observation.retrieved_evidence == ()
    assert observation.sync_safety_outcome == "refused"
    assert observation.stream_safety_outcome == "refused"


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


@pytest.mark.asyncio
async def test_graph_adapter_traverses_real_graph_without_cross_patient_evidence(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    other_patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_documents/patient.txt", page_number=1)
    forbidden = EvidenceLocator(source_path="patients_documents/other.txt", page_number=1)
    artifact = _artifact(
        tmp_path,
        patient_id=patient_id,
        relative_path=locator.source_path,
        locator=locator,
        content=b"Metformin treats diabetes. Diabetes causes neuropathy.",
    )
    other = _artifact(
        tmp_path,
        patient_id=other_patient_id,
        relative_path=forbidden.source_path,
        locator=forbidden,
        content=b"Warfarin treats thrombosis.",
    )
    manifest = CorpusManifestV2(artifacts=(artifact, other))
    context = _context(manifest, actor_patient_ids=(patient_id,))
    base_case = _case(patient_id=patient_id, actor_patient_ids=(patient_id,), locator=locator)
    case = base_case.copy(
        update={
            "case_id": "graph-adapter-case",
            "category": "graph_multi_hop",
            "forbidden_evidence": (forbidden,),
            "graph": GraphExpectation(
                required_nodes=("metformin", "diabetes", "neuropathy"),
                required_edges=(
                    ("metformin", "treats", "diabetes"),
                    ("diabetes", "causes", "neuropathy"),
                ),
                evidence=(locator,),
            ),
        }
    )

    observation = await ProductGraphAdapter(tmp_path).evaluate(case, context)

    assert [evidence.source_path for evidence in observation.retrieved_evidence] == [locator.source_path]
    assert observation.graph_node_ids == ("metformin", "diabetes", "neuropathy")
    assert observation.graph_edge_ids == ("diabetes|causes|neuropathy", "metformin|treats|diabetes")
    assert "metformin|treats|diabetes>>diabetes|causes|neuropathy" in observation.graph_path_ids


@pytest.mark.asyncio
async def test_graph_adapter_traverses_source_backed_labeled_lab_observation(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_labs/patient.csv", row_number=2)
    artifact = _artifact(
        tmp_path,
        patient_id=patient_id,
        relative_path=locator.source_path,
        locator=locator,
        content=(
            b"Patient Name,MRN,DOB,Gender,Date,Analyte,Value,Unit,Reference Range,Status\n"
            b"Alice Synthetic,MRN-0001,1978-05-17,Female,2025-12-02,Creatinine,1.55,mg/dL,0.7-1.3,High\n"
        ),
    ).copy(update={"kind": "patient_lab", "mime_type": "text/csv", "document_type": "lab_result"})
    context = _context(CorpusManifestV2(artifacts=(artifact,)), actor_patient_ids=(patient_id,))
    base_case = _case(patient_id=patient_id, actor_patient_ids=(patient_id,), locator=locator)
    case = base_case.copy(
        update={
            "case_id": "source-backed-lab-graph-case",
            "category": "graph_multi_hop",
            "graph": GraphExpectation(
                required_nodes=("patient:mrn-0001", "analyte:creatinine", "status:high"),
                required_edges=(
                    ("patient:mrn-0001", "has_observation", "analyte:creatinine"),
                    ("analyte:creatinine", "has_status", "status:high"),
                ),
                evidence=(locator,),
            ),
        }
    )

    observation = await ProductGraphAdapter(tmp_path).evaluate(case, context)

    assert observation.graph_node_ids == ("patient:mrn-0001", "analyte:creatinine", "status:high")
    assert observation.graph_edge_ids == (
        "analyte:creatinine|has_status|status:high",
        "patient:mrn-0001|has_observation|analyte:creatinine",
    )
    assert (
        "patient:mrn-0001|has_observation|analyte:creatinine>>analyte:creatinine|has_status|status:high"
    ) in observation.graph_path_ids


@pytest.mark.asyncio
async def test_chat_adapter_returns_actual_cited_source_backed_evidence(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_documents/patient.txt", page_number=1)
    artifact = _artifact(
        tmp_path,
        patient_id=patient_id,
        relative_path=locator.source_path,
        locator=locator,
        content=b"Patient has an allergy to penicillin.",
    )
    manifest = CorpusManifestV2(artifacts=(artifact,))
    context = _context(manifest, actor_patient_ids=(patient_id,))
    case = _case(patient_id=patient_id, actor_patient_ids=(patient_id,), locator=locator)

    observation = await ProductChatAdapter(tmp_path).evaluate(case, context)

    assert [evidence.source_path for evidence in observation.retrieved_evidence] == [locator.source_path]
    assert [evidence.source_path for evidence in observation.cited_evidence] == [locator.source_path]
    assert "penicillin" in observation.answer_text.lower()
    assert observation.stream_safety_outcome == "not_evaluated"


@pytest.mark.asyncio
async def test_chat_adapter_refuses_an_actor_without_patient_permission(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_documents/patient.txt", page_number=1)
    artifact = _artifact(tmp_path, patient_id=patient_id, relative_path=locator.source_path, locator=locator)
    manifest = CorpusManifestV2(artifacts=(artifact,))
    context = _context(manifest, actor_patient_ids=())
    case = _case(patient_id=patient_id, actor_patient_ids=(), locator=locator)

    observation = await ProductChatAdapter(tmp_path).evaluate(case, context)

    assert observation.refused is True
    assert observation.retrieved_evidence == ()
    assert observation.sync_safety_outcome == "refused"
    assert observation.stream_safety_outcome == "not_evaluated"


@pytest.mark.asyncio
async def test_chat_adapter_never_retrieves_or_cites_forbidden_patient_evidence(tmp_path: Path) -> None:
    patient_id = uuid.uuid4()
    other_patient_id = uuid.uuid4()
    locator = EvidenceLocator(source_path="patients_documents/patient.txt", page_number=1)
    forbidden = EvidenceLocator(source_path="patients_documents/other.txt", page_number=1)
    artifact = _artifact(
        tmp_path,
        patient_id=patient_id,
        relative_path=locator.source_path,
        locator=locator,
        content=b"Patient has an allergy to penicillin.",
    )
    other = _artifact(
        tmp_path,
        patient_id=other_patient_id,
        relative_path=forbidden.source_path,
        locator=forbidden,
        content=b"Patient uses apixaban.",
    )
    manifest = CorpusManifestV2(artifacts=(artifact, other))
    context = _context(manifest, actor_patient_ids=(patient_id,))
    case = _case(patient_id=patient_id, actor_patient_ids=(patient_id,), locator=locator).copy(
        update={"forbidden_evidence": (forbidden,)}
    )

    observation = await ProductChatAdapter(tmp_path).evaluate(case, context)

    assert [evidence.source_path for evidence in observation.retrieved_evidence] == [locator.source_path]
    assert [evidence.source_path for evidence in observation.cited_evidence] == [locator.source_path]


def test_retrieval_adapter_supports_graph_mode(tmp_path: Path) -> None:
    adapter = ProductRetrievalAdapter(tmp_path, retrieval_mode="graph")
    assert adapter.retrieval_mode == "graph"

