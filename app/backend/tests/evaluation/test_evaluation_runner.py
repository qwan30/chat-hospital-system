from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree

import pytest

from hospital_ai.evaluation.adapter_foundation import (
    EvaluatorIsolationConfig,
    RuntimeEvidenceChunk,
    SourceEvidenceResolver,
)
from hospital_ai.evaluation.benchmark import EvalCaseV2
from hospital_ai.evaluation.contracts import CaseResult, GateResult, OcrEngineStatus
from hospital_ai.evaluation.corpus_manifest import build_corpus_manifest
from hospital_ai.evaluation.runner import (
    CaseObservation,
    EvaluationConfig,
    _evaluate_observation,
    _graph_case_coverage_gate,
    _retrieval_quality_gates,
    run_evaluation,
    run_evaluation_async,
    write_run_artifacts,
)

BACKEND_ROOT = Path(__file__).parents[2]
DATA_ROOT = BACKEND_ROOT / "data"
BENCHMARK_DIR = DATA_ROOT / "evaluation"
CLI_PATH = BACKEND_ROOT / "scripts" / "run_ai_evaluation.py"


def _load_cli():
    spec = importlib.util.spec_from_file_location("run_ai_evaluation", CLI_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _safe_refusal_case() -> EvalCaseV2:
    for line in (BENCHMARK_DIR / "rag_sentinel_v2.jsonl").read_text(encoding="utf-8").splitlines():
        case = EvalCaseV2.parse_raw(line)
        if case.category == "safe_refusal":
            return case
    raise AssertionError("sentinel must contain a safe-refusal case")


def _runtime_evidence(case: EvalCaseV2, locator, resolver: SourceEvidenceResolver) -> RuntimeEvidenceChunk:
    artifact = resolver.artifact_for(locator)
    return RuntimeEvidenceChunk(
        runtime_chunk_id=f"runtime-{locator.source_path}-{locator.page_number}-{locator.row_number}",
        source_path=locator.source_path,
        source_sha256=artifact.source_sha256,
        patient_id=artifact.patient_id,
        page_number=locator.page_number,
        row_number=locator.row_number,
        record_id=locator.record_id,
    )


def _approved_benchmark_dir(tmp_path: Path) -> Path:
    output = tmp_path / "benchmarks"
    output.mkdir()
    (output / "rag_benchmark_v2.jsonl").write_bytes((BENCHMARK_DIR / "rag_benchmark_v2.jsonl").read_bytes())
    reviewed = []
    for line in (BENCHMARK_DIR / "rag_sentinel_v2.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise
        row["review"] = {
            "status": "approved",
            "reviewer_ids": ["independent-reviewer-alpha", "independent-reviewer-beta"],
            "unresolved_issues": [],
        }
        reviewed.append(json.dumps(row, separators=(",", ":"), sort_keys=True))
    (output / "rag_sentinel_v2.jsonl").write_text("\n".join(reviewed) + "\n", encoding="utf-8")
    
    if (BENCHMARK_DIR / "corpus-v3-smoke-manifest.json").exists():
        (output / "corpus-v3-smoke-manifest.json").write_bytes((BENCHMARK_DIR / "corpus-v3-smoke-manifest.json").read_bytes())
        
    return output


def _config(
    tmp_path: Path,
    benchmark_dir: Path,
    *,
    suite: str = "smoke",
    lane: str = "deterministic",
    components: tuple[str, ...] = ("corpus", "retrieval", "graph", "chat"),
    environment: dict[str, Optional[str]] = None,
) -> EvaluationConfig:
    return EvaluationConfig(
        suite=suite,
        lane=lane,
        components=components,
        output_dir=tmp_path / "artifacts",
        data_root=DATA_ROOT,
        benchmark_dir=benchmark_dir,
        environment=environment or {},
        git_sha="fixture-git-sha",
        clock=lambda: "2026-07-22T12:00:00Z",
    )


def _isolation() -> EvaluatorIsolationConfig:
    return EvaluatorIsolationConfig(
        evaluation_database_url="postgresql+asyncpg://hospital_ai:test@localhost:5432/hospital_ai_eval",
        approved_evaluation_database_url="postgresql://hospital_ai:test@127.0.0.1/hospital_ai_eval",
        product_database_url="postgresql+asyncpg://hospital_ai:test@localhost:5432/hospital_ai",
        run_namespace="ai-eval/test-run",
    )


def test_result_contracts_preserve_machine_readable_scalar_types() -> None:
    result = CaseResult(
        case_id="contract-fixture",
        component="harness",
        status="passed",
        metrics={"score": 0.5, "count": 2, "ok": True},
    )
    gate = GateResult(
        name="typed-observation",
        component="harness",
        passed=True,
        hard=True,
        observed=2,
        threshold="= 2",
    )

    assert result.metrics == {"score": 0.5, "count": 2, "ok": True}
    assert isinstance(result.metrics["score"], float)
    assert isinstance(result.metrics["count"], int)
    assert isinstance(result.metrics["ok"], bool)
    assert gate.observed == 2
    assert isinstance(gate.observed, int)


def test_retrieval_quality_gates_fail_when_answer_cases_have_nearly_no_evidence() -> None:
    cases = tuple(
        EvalCaseV2.parse_raw(line)
        for line in (BENCHMARK_DIR / "rag_sentinel_v2.jsonl").read_text(encoding="utf-8").splitlines()
    )
    results = tuple(
        CaseResult(
            case_id=case.case_id,
            component="retrieval",
            status="passed",
            metrics={
                "recall_at_5": 1.0 if index == 0 else 0.0,
                "precision_at_5": 0.2 if index == 0 else 0.0,
                "mrr": 1.0 if index == 0 else 0.0,
                "ndcg_at_5": 1.0 if index == 0 else 0.0,
            },
        )
        for index, case in enumerate(case for case in cases if case.answer_policy == "answer")
    )

    gates = {gate.name: gate for gate in _retrieval_quality_gates(cases, results)}

    assert not gates["retrieval_recall_at_5"].passed
    assert not gates["retrieval_mrr"].passed
    assert not gates["retrieval_ndcg_at_5"].passed
    assert gates["retrieval_recall_at_5"].threshold == "> 0.85"
    assert gates["retrieval_mrr"].threshold == "> 0.85"
    assert gates["retrieval_ndcg_at_5"].threshold == "> 0.85"


def test_retrieval_quality_gates_exclude_refusal_cases_from_quality_denominator() -> None:
    cases = tuple(
        EvalCaseV2.parse_raw(line)
        for line in (BENCHMARK_DIR / "rag_sentinel_v2.jsonl").read_text(encoding="utf-8").splitlines()
    )
    results = tuple(
        CaseResult(
            case_id=case.case_id,
            component="retrieval",
            status="passed",
            metrics={
                "recall_at_5": 1.0 if case.answer_policy == "answer" else 0.0,
                "precision_at_5": 1.0 if case.answer_policy == "answer" else 0.0,
                "mrr": 1.0 if case.answer_policy == "answer" else 0.0,
                "ndcg_at_5": 1.0 if case.answer_policy == "answer" else 0.0,
            },
        )
        for case in cases
    )

    gates = {gate.name: gate for gate in _retrieval_quality_gates(cases, results)}

    assert gates["retrieval_recall_at_5"].passed
    assert gates["retrieval_mrr"].passed
    assert gates["retrieval_ndcg_at_5"].passed
    assert gates["retrieval_recall_at_5"].observed == 1.0


class _SafeButEmptyRetrievalAdapter:
    def evaluate(self, case, _context) -> CaseObservation:
        refused = case.category == "permission_adversarial"
        return CaseObservation(
            covered_fact_ids=tuple(fact.fact_id for fact in case.expected_facts),
            refused=refused,
            sync_safety_outcome="refused" if refused else "answered",
            stream_safety_outcome="refused" if refused else "answered",
        )


def test_runner_fails_when_safe_retrieval_has_insufficient_aggregate_quality(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("retrieval",))

    run = run_evaluation(
        config,
        adapters={"retrieval": _SafeButEmptyRetrievalAdapter()},
        isolation=_isolation(),
    )

    assert run.exit_code == 1
    assert run.manifest.status == "failed"
    assert any(gate.name == "retrieval_recall_at_5" and not gate.passed for gate in run.gates)
    assert "retrieval_recall_at_5" in run.manifest.failure_reason


def test_deterministic_smoke_validates_reviewed_sentinel_and_writes_all_artifacts(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("corpus",))

    run = run_evaluation(config)
    write_run_artifacts(run, config.output_dir)

    assert run.exit_code == 0
    assert run.manifest.status == "passed"
    assert run.manifest.selected_case_count >= 50
    for filename in ("run.json", "cases.jsonl", "junit.xml", "summary.md"):
        assert (config.output_dir / filename).is_file()
    run_json = json.loads((config.output_dir / "run.json").read_text(encoding="utf-8"))
    assert run_json["dataset_version"] == "synthetic-100-v2"
    assert run_json["git_sha"] == "fixture-git-sha"
    assert run_json["prompt_version"] == "not-applicable-deterministic"
    assert "token_usage" in run_json
    assert run_json["configuration"]["retrieval_mode"] == "vector"
    ElementTree.parse(config.output_dir / "junit.xml")
    assert "not product quality evidence" in (config.output_dir / "summary.md").read_text(encoding="utf-8")


def test_requested_product_component_without_adapter_fails_required_component_gate(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("retrieval",))

    run = run_evaluation(config)

    assert run.exit_code == 1
    assert run.manifest.status == "failed"
    assert any(
        gate.name == "evaluation_adapter_configured" and gate.component == "retrieval" and gate.hard and not gate.passed
        for gate in run.gates
    )
    retrieval_results = [result for result in run.cases if result.component == "retrieval"]
    assert retrieval_results
    assert all(result.status == "skipped" for result in retrieval_results)


def test_runner_rejects_unknown_retrieval_mode_as_invalid_configuration(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("corpus",))
    config = EvaluationConfig(**{**config.__dict__, "retrieval_mode": "unknown"})

    run = run_evaluation(config)

    assert run.exit_code == 2
    assert run.manifest.status == "invalid"


def test_unreviewed_real_sentinel_is_a_gate_failure_not_invalid_data(tmp_path: Path) -> None:
    run = run_evaluation(_config(tmp_path, BENCHMARK_DIR, components=("corpus",)))

    assert run.exit_code == 1
    assert run.manifest.status == "failed"
    review_gate = next(gate for gate in run.gates if gate.name == "sentinel_independent_review")
    assert review_gate.hard
    assert not review_gate.passed
    assert review_gate.observed == 5


def test_requested_image_ocr_fails_explicitly_when_engine_is_unavailable(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("ocr",))

    run = run_evaluation(
        config,
        ocr_probe=lambda: OcrEngineStatus(
            status="engine_unavailable",
            available=False,
            reason="missing paddleocr and paddlepaddle",
        ),
    )

    assert run.exit_code == 1
    result = next(result for result in run.cases if result.case_id == "ocr-image-engine")
    assert result.status == "failed"
    assert result.reason == "missing paddleocr and paddlepaddle"
    assert not any(result.metrics.get("cer") == 0 for result in run.cases if result.case_id == "ocr-image-engine")


def test_live_lane_without_credentials_is_explicitly_skipped_without_scores(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(
        tmp_path,
        benchmark_dir,
        lane="live",
        components=("retrieval", "graph", "chat"),
        environment={},
    )

    run = run_evaluation(config)

    assert run.exit_code == 0
    assert run.manifest.status == "skipped"
    product_results = [result for result in run.cases if result.component in {"retrieval", "graph", "chat"}]
    assert product_results
    assert all(result.status == "skipped" for result in product_results)
    assert all("credentials" in result.reason for result in product_results)
    assert all(1.0 not in result.metrics.values() for result in product_results)


class _LeakingAdapter:
    def evaluate(self, _case, _context) -> CaseObservation:
        return CaseObservation(
            retrieved_ids=("fabricated-source",),
            cited_ids=("fabricated-source",),
            provenance_ids=(),
            covered_fact_ids=(),
            refused=False,
            sync_safety_outcome="answered",
            stream_safety_outcome="answered",
        )


def test_adapter_observation_that_leaks_evidence_fails_hard_gates(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("chat",))

    run = run_evaluation(config, adapters={"chat": _LeakingAdapter()}, isolation=_isolation())

    assert run.exit_code == 1
    assert any(gate.hard and not gate.passed and gate.name == "zero_unauthorized_evidence" for gate in run.gates)
    assert any(gate.hard and not gate.passed and gate.name == "zero_fabricated_citations" for gate in run.gates)


def test_retrieval_may_inspect_absence_sources_without_claiming_chat_refusal() -> None:
    case = _safe_refusal_case()
    resolver = SourceEvidenceResolver(build_corpus_manifest(DATA_ROOT))
    evidence = _runtime_evidence(case, case.absence_checked_evidence[0], resolver)

    result = _evaluate_observation(
        case,
        case.patient_id,
        "retrieval",
        CaseObservation(retrieved_evidence=(evidence,)),
        resolver,
    )
    gates = {gate.name: gate for gate in result.gates}

    assert gates["zero_unauthorized_evidence"].passed
    assert gates["zero_wrong_patient_evidence"].passed
    assert gates["safe_refusal_behavior"].passed


def test_same_patient_forbidden_evidence_is_unauthorized_but_not_wrong_patient() -> None:
    case = _safe_refusal_case()
    resolver = SourceEvidenceResolver(build_corpus_manifest(DATA_ROOT))
    evidence = _runtime_evidence(case, case.forbidden_evidence[0], resolver)

    result = _evaluate_observation(
        case,
        case.patient_id,
        "retrieval",
        CaseObservation(retrieved_evidence=(evidence,)),
        resolver,
    )
    gates = {gate.name: gate for gate in result.gates}

    assert not gates["zero_unauthorized_evidence"].passed
    assert gates["zero_wrong_patient_evidence"].passed


def test_cross_patient_evidence_still_fails_wrong_patient_gate() -> None:
    resolver = SourceEvidenceResolver(build_corpus_manifest(DATA_ROOT))
    case = next(
        case
        for line in (BENCHMARK_DIR / "rag_sentinel_v2.jsonl").read_text(encoding="utf-8").splitlines()
        for case in (EvalCaseV2.parse_raw(line),)
        if case.forbidden_evidence and resolver.artifact_for(case.forbidden_evidence[0]).patient_id != case.patient_id
    )
    evidence = _runtime_evidence(case, case.forbidden_evidence[0], resolver)

    result = _evaluate_observation(
        case,
        case.patient_id,
        "retrieval",
        CaseObservation(retrieved_evidence=(evidence,)),
        resolver,
    )
    gates = {gate.name: gate for gate in result.gates}

    assert not gates["zero_unauthorized_evidence"].passed
    assert not gates["zero_wrong_patient_evidence"].passed


class _AsyncSafeAdapter:
    def __init__(self) -> None:
        self.loop_ids: set[int] = set()
        self.actor_ids: set[str] = set()

    async def evaluate(self, case, context) -> CaseObservation:
        await asyncio.sleep(0)
        self.loop_ids.add(id(asyncio.get_running_loop()))
        self.actor_ids.add(str(context.actor.actor_id))
        refused = case.category == "permission_adversarial"
        evidence = (
            tuple(_runtime_evidence(case, locator, context.evidence_resolver) for locator in case.allowed_evidence)
            if getattr(case, "answer_policy", None) == "answer"
            else ()
        )
        return CaseObservation(
            retrieved_evidence=evidence,
            covered_fact_ids=tuple(fact.fact_id for fact in case.expected_facts),
            refused=refused,
            sync_safety_outcome="refused" if refused else "answered",
            stream_safety_outcome="refused" if refused else "answered",
        )


@pytest.mark.asyncio
async def test_async_runner_uses_one_event_loop_for_all_adapter_cases(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("retrieval",))
    adapter = _AsyncSafeAdapter()

    run = await run_evaluation_async(config, adapters={"retrieval": adapter}, isolation=_isolation())

    for case in run.cases:
        if case.status == "failed":
            print(f"FAILED CASE {case.case_id}: {vars(case)}")
            break
    assert run.exit_code == 0
    assert adapter.loop_ids == {id(asyncio.get_running_loop())}
    assert len(adapter.actor_ids) >= 50


class _ConcurrencyTrackingAdapter:
    def __init__(self) -> None:
        self.in_flight = 0
        self.peak_in_flight = 0

    async def evaluate(self, case, context) -> CaseObservation:
        self.in_flight += 1
        self.peak_in_flight = max(self.peak_in_flight, self.in_flight)
        await asyncio.sleep(0.001)
        self.in_flight -= 1
        refused = case.category == "permission_adversarial"
        evidence = (
            tuple(_runtime_evidence(case, locator, context.evidence_resolver) for locator in case.allowed_evidence)
            if getattr(case, "answer_policy", None) == "answer"
            else ()
        )
        return CaseObservation(
            retrieved_evidence=evidence,
            covered_fact_ids=tuple(fact.fact_id for fact in case.expected_facts),
            refused=refused,
            sync_safety_outcome="refused" if refused else "answered",
            stream_safety_outcome="refused" if refused else "answered",
        )


@pytest.mark.asyncio
async def test_adapter_cases_are_serial_by_default_to_bound_local_resources(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("retrieval",))
    adapter = _ConcurrencyTrackingAdapter()

    run = await run_evaluation_async(config, adapters={"retrieval": adapter}, isolation=_isolation())

    assert run.exit_code == 0
    assert adapter.peak_in_flight == 1


class _GraphIncompleteAdapter:
    def evaluate(self, case, _context) -> CaseObservation:
        return CaseObservation(
            covered_fact_ids=tuple(fact.fact_id for fact in case.expected_facts),
            sync_safety_outcome="answered",
            stream_safety_outcome="answered",
        )


def test_graph_adapter_result_without_required_path_fails_graph_gate(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("graph",))

    run = run_evaluation(config, adapters={"graph": _GraphIncompleteAdapter()}, isolation=_isolation())

    assert run.exit_code == 1
    assert any(gate.name == "graph_path_recall" and gate.hard and not gate.passed for gate in run.gates)


def test_graph_coverage_gate_rejects_a_selected_suite_without_graph_cases() -> None:
    gate = _graph_case_coverage_gate(())

    assert gate.hard
    assert not gate.passed
    assert gate.observed == 0


class _GraphOnlyAdapter:
    def __init__(self) -> None:
        self.seen_case_ids: list[str] = []

    def evaluate(self, case, _context) -> CaseObservation:
        assert case.graph is not None
        self.seen_case_ids.append(case.case_id)
        return CaseObservation(
            graph_node_ids=case.graph.required_nodes,
            graph_edge_ids=tuple("|".join(edge) for edge in case.graph.required_edges),
            graph_path_ids=(">>".join("|".join(edge) for edge in case.graph.required_edges),),
            sync_safety_outcome="answered",
            stream_safety_outcome="answered",
        )


def test_graph_adapter_receives_only_cases_with_graph_expectations(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("graph",))
    adapter = _GraphOnlyAdapter()

    run = run_evaluation(config, adapters={"graph": adapter}, isolation=_isolation())

    selected = [
        EvalCaseV2.parse_raw(line)
        for line in (benchmark_dir / "rag_sentinel_v2.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    expected_case_ids = {case.case_id for case in selected if case.graph is not None}
    assert set(adapter.seen_case_ids) == expected_case_ids
    assert {result.case_id for result in run.cases if result.component == "graph"} == expected_case_ids


class _GraphDisconnectedEdgesAdapter:
    def evaluate(self, case, _context) -> CaseObservation:
        graph = case.graph
        return CaseObservation(
            covered_fact_ids=tuple(fact.fact_id for fact in case.expected_facts),
            sync_safety_outcome="answered",
            stream_safety_outcome="answered",
            graph_node_ids=graph.required_nodes if graph else (),
            graph_edge_ids=tuple("|".join(edge) for edge in graph.required_edges) if graph else (),
            graph_path_ids=tuple("|".join(edge) for edge in graph.required_edges) if graph else (),
        )


def test_graph_adapter_disconnected_edges_do_not_satisfy_multi_hop_path(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("graph",))

    run = run_evaluation(config, adapters={"graph": _GraphDisconnectedEdgesAdapter()}, isolation=_isolation())

    assert run.exit_code == 1
    assert any(gate.name == "graph_edge_recall" and gate.passed for gate in run.gates)
    assert any(gate.name == "graph_path_recall" and gate.hard and not gate.passed for gate in run.gates)


class _NonStreamingChatAdapter:
    def evaluate(self, case, _context) -> CaseObservation:
        return CaseObservation(
            covered_fact_ids=tuple(fact.fact_id for fact in case.expected_facts),
            refused=case.answer_policy != "answer",
            sync_safety_outcome="refused" if case.answer_policy != "answer" else "answered",
            stream_safety_outcome="not_evaluated",
        )


def test_non_streaming_chat_result_requires_explicit_sse_coverage(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("chat",))

    run = run_evaluation(config, adapters={"chat": _NonStreamingChatAdapter()}, isolation=_isolation())

    assert run.exit_code == 1
    assert any(gate.name == "sse_transport_coverage" and gate.hard and not gate.passed for gate in run.gates)
    assert all(gate.passed for gate in run.gates if gate.name == "sync_sse_safety_parity")


class _SiblingEvidenceAdapter:
    def evaluate(self, case, context) -> CaseObservation:
        registered = case.allowed_evidence + case.forbidden_evidence + case.absence_checked_evidence
        sibling = next(
            other_case.allowed_evidence[0]
            for other_case in (
                EvalCaseV2.parse_obj(json.loads(line))
                for line in (BENCHMARK_DIR / "rag_benchmark_v2.jsonl").read_text(encoding="utf-8").splitlines()
            )
            if other_case.allowed_evidence[0] not in registered
        )
        artifact = build_corpus_manifest(DATA_ROOT).artifacts_by_path[sibling.source_path]
        return CaseObservation(
            retrieved_evidence=(
                RuntimeEvidenceChunk(
                    runtime_chunk_id="unregistered-sibling",
                    source_path=sibling.source_path,
                    source_sha256=artifact.source_sha256,
                    patient_id=artifact.patient_id,
                    page_number=sibling.page_number,
                    row_number=sibling.row_number,
                    record_id=sibling.record_id,
                ),
            )
        )


def test_adapter_runner_rejects_a_canonical_sibling_not_registered_for_the_case(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("retrieval",))

    run = run_evaluation(config, adapters={"retrieval": _SiblingEvidenceAdapter()}, isolation=_isolation())

    assert run.exit_code == 1
    assert all(
        any(gate.name == "evaluation_adapter_execution" and not gate.passed for gate in result.gates)
        for result in run.cases
        if result.component == "retrieval"
    )


def test_adapter_run_without_isolated_database_configuration_is_invalid(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("chat",))

    run = run_evaluation(config, adapters={"chat": _LeakingAdapter()})

    assert run.exit_code == 2
    assert run.manifest.status == "invalid"
    assert "isolated evaluator" in run.manifest.failure_reason


def test_release_selects_all_300_cases(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, suite="release", components=("corpus",))

    run = run_evaluation(config)

    assert run.exit_code == 0
    assert run.manifest.selected_case_count >= 300


def test_invalid_dataset_returns_two_and_still_writes_diagnostic_artifacts(tmp_path: Path) -> None:
    config = EvaluationConfig(
        suite="smoke",
        lane="deterministic",
        components=("corpus",),
        output_dir=tmp_path / "artifacts",
        data_root=tmp_path / "missing-data",
        benchmark_dir=tmp_path / "missing-benchmarks",
        environment={},
        git_sha="fixture",
        clock=lambda: "2026-07-22T12:00:00Z",
    )

    run = run_evaluation(config)
    write_run_artifacts(run, config.output_dir)

    assert run.exit_code == 2
    assert run.manifest.status == "invalid"
    assert (config.output_dir / "run.json").is_file()
    assert "data root" in (config.output_dir / "summary.md").read_text(encoding="utf-8").lower()


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["--suite", "unknown"], 2),
        (["--lane", "invalid"], 2),
        (["--components", "corpus,unknown"], 2),
        (["--retrieval-mode", "unknown"], 2),
    ],
)
def test_cli_invalid_configuration_returns_two_without_argparse_escape(
    tmp_path: Path, argv: list[str], expected: int
) -> None:
    cli = _load_cli()
    base = ["--output-dir", str(tmp_path / "out")]

    assert cli.main(base + argv) == expected


def test_cli_builds_only_requested_deterministic_product_adapters() -> None:
    cli = _load_cli()

    adapters, isolation = cli._deterministic_product_adapters(
        DATA_ROOT,
        ("retrieval", "graph"),
        retrieval_mode="bm25",
    )

    assert set(adapters) == {"retrieval", "graph"}
    assert adapters["retrieval"].retrieval_mode == "bm25"
    assert isolation.evaluation_database_url == "sqlite+aiosqlite:///:memory:"
    assert isolation.product_database_url != isolation.evaluation_database_url


def test_cli_main_returns_gate_exit_and_writes_artifacts(tmp_path: Path) -> None:
    cli = _load_cli()
    output = tmp_path / "out"

    exit_code = cli.main(
        [
            "--suite",
            "smoke",
            "--lane",
            "deterministic",
            "--components",
            "corpus",
            "--output-dir",
            str(output),
            "--data-root",
            str(DATA_ROOT),
            "--benchmark-dir",
            str(BENCHMARK_DIR),
            "--retrieval-mode",
            "hybrid",
        ]
    )

    assert exit_code == 1
    assert (output / "run.json").is_file()
    run_json = json.loads((output / "run.json").read_text(encoding="utf-8"))
    assert run_json["configuration"]["retrieval_mode"] == "hybrid"


def test_graph_multi_hop_path_normalization() -> None:
    from hospital_ai.evaluation.product_graph_adapter import ProductGraphAdapter
    from hospital_ai.services.graph_rag import ExtractedRelation

    relations = [
        ExtractedRelation("patient:mrn-0001", "analyte:potassium", "has_observation"),
        ExtractedRelation("analyte:potassium", "status:normal", "has_status"),
    ]
    paths = ProductGraphAdapter._path_ids(relations)
    expected_path = "patient:mrn-0001|has_observation|analyte:potassium>>analyte:potassium|has_status|status:normal"
    assert expected_path in paths


def test_cli_accepts_llm_judge_provider_flag(tmp_path: Path) -> None:
    cli = _load_cli()
    output_dir = tmp_path / "artifacts"
    result = cli.main(
        ["--components", "chat", "--output-dir", str(output_dir), "--llm-judge-provider", "gemini", "--suite", "smoke"]
    )
    assert result == 1
    assert (output_dir / "run.json").exists()


def test_jsonl_threshold_check(tmp_path: Path) -> None:
    from hospital_ai.evaluation.artifact_generator import load_measured_artifacts, check_measured_thresholds

    output_dir = tmp_path / "artifacts"
    output_dir.mkdir()
    cases_path = output_dir / "cases.jsonl"
    
    # Write a dummy cases.jsonl with poor metrics
    cases_path.write_text(json.dumps({"metrics": {"precision_at_5": 0.5, "recall_at_5": 0.5}}) + "\n", encoding="utf-8")
    
    artifacts = load_measured_artifacts(cases_path)
    assert not check_measured_thresholds(artifacts)

    # Write a dummy cases.jsonl with good metrics
    cases_path.write_text(json.dumps({"metrics": {"precision_at_5": 0.9, "recall_at_5": 0.9}}) + "\n", encoding="utf-8")
    
    artifacts = load_measured_artifacts(cases_path)
    assert check_measured_thresholds(artifacts)
