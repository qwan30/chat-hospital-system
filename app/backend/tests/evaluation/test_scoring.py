from uuid import UUID, uuid4

import pytest

from hospital_ai.evaluation.benchmark import (
    ActorFixture,
    BenchmarkCase,
    ExpectedCitation,
    ExpectedFact,
)
from hospital_ai.evaluation.claims import CitedChunk
from hospital_ai.evaluation.scoring import (
    EvaluationTrace,
    GroundTruthLeakageError,
    InvalidMetricError,
    aggregate_scores,
    assert_no_ground_truth_leakage,
    evaluate_gates,
    safe_ratio,
    score_case,
    serialize_expected_facts,
)


@pytest.fixture
def case() -> BenchmarkCase:
    patient_id = uuid4()
    evidence_id = uuid4()
    return BenchmarkCase(
        case_id=uuid4(),
        corpus_version="test-v1",
        patient_id=patient_id,
        actor=ActorFixture(role="doctor", actor_id="doctor-1", allowed_patient_ids=(patient_id,)),
        question="What is the HbA1c?",
        category="single_hop",
        expected_facts=(
            ExpectedFact(
                field="HbA1c",
                value="7.2 %",
                source_path="patients_labs/patient.csv",
                source_sha256="a" * 64,
                source_locator="row:2",
                evidence_id=evidence_id,
                observed_at="2026-01-02",
            ),
        ),
        allowed_evidence_ids=(evidence_id,),
        forbidden_evidence_ids=(),
        expected_citations=(
            ExpectedCitation(
                evidence_id=evidence_id,
                source_path="patients_labs/patient.csv",
                source_sha256="a" * 64,
                source_locator="row:2",
            ),
        ),
        answer_policy="answer",
    )


def _trace(case: BenchmarkCase, **updates: object) -> EvaluationTrace:
    evidence_id = case.expected_facts[0].evidence_id if case.expected_facts else uuid4()
    defaults: dict[str, object] = {
        "answer": "HbA1c was 7.2 % on 2026-01-02 [E1].",
        "mode": "hybrid_graph_off",
        "retrieved_evidence_ids": (evidence_id,),
        "selected_evidence_ids": (evidence_id,),
        "cited_chunks": (
            CitedChunk(
                evidence_id=evidence_id,
                text="HbA1c was 7.2 % on 2026-01-02.",
                citation_label="E1",
            ),
        ),
        "generator_inputs": ("question: What is the HbA1c?",),
        "refused": False,
        "graph_ran": False,
        "graph_selected_evidence_ids": (),
        "latency_ms": 10,
    }
    defaults.update(updates)
    return EvaluationTrace(**defaults)


def test_valid_evidence_id_does_not_credit_unsupported_claim(case: BenchmarkCase) -> None:
    trace = _trace(
        case,
        answer="HbA1c is 4.2 % [E1].",
        cited_chunks=(
            CitedChunk(
                evidence_id=case.expected_facts[0].evidence_id,
                text="HbA1c was 7.2 %.",
                citation_label="E1",
            ),
        ),
    )

    score = score_case(case, trace)

    assert score.citation_precision.value == 0.0
    assert score.unsupported_claim_count == 1


def test_empty_denominator_fails_instead_of_returning_one() -> None:
    with pytest.raises(InvalidMetricError, match="empty denominator"):
        safe_ratio(0, 0, metric="citation_precision")


def test_expected_output_substitution_is_detected(case: BenchmarkCase) -> None:
    leaked = _trace(case, generator_inputs=(serialize_expected_facts(case.expected_facts),))

    with pytest.raises(GroundTruthLeakageError):
        assert_no_ground_truth_leakage(case, leaked.generator_inputs)


def test_graph_display_without_selected_cited_evidence_gets_no_graph_credit(case: BenchmarkCase) -> None:
    trace = _trace(
        case,
        graph_ran=True,
        graph_selected_evidence_ids=(),
        cited_chunks=(),
    )

    assert score_case(case, trace).graph_value_credit is False


def test_retrieval_and_fact_metrics_record_real_denominators(case: BenchmarkCase) -> None:
    score = score_case(case, _trace(case))

    assert score.retrieval_recall_at_5.numerator == 1
    assert score.retrieval_recall_at_5.denominator == 1
    assert score.retrieval_recall_at_5.value == 1.0
    assert score.mrr_at_5.value == 1.0
    assert score.fact_f1.value == 1.0
    assert score.citation_recall.value == 1.0


def test_forbidden_selected_evidence_is_counted_as_leakage(case: BenchmarkCase) -> None:
    forbidden = uuid4()
    restricted = case.copy(update={"forbidden_evidence_ids": (forbidden,)})

    score = score_case(restricted, _trace(restricted, selected_evidence_ids=(forbidden,)))

    assert score.unauthorized_selected_count == 1


def test_unknown_selected_evidence_is_unauthorized(case: BenchmarkCase) -> None:
    score = score_case(case, _trace(case, selected_evidence_ids=(uuid4(),)))

    assert score.unauthorized_selected_count == 1


def test_attached_but_uncited_chunk_gets_no_citation_credit(case: BenchmarkCase) -> None:
    score = score_case(case, _trace(case, answer="HbA1c was 7.2 % on 2026-01-02."))

    assert score.citation_recall.value == 0.0


def test_unexpected_claim_is_a_severe_hallucination(case: BenchmarkCase) -> None:
    score = score_case(case, _trace(case, answer="Sodium is critically low."))

    assert score.unsupported_claim_count == 1


def test_uncited_claim_is_not_in_citation_precision_denominator(case: BenchmarkCase) -> None:
    score = score_case(case, _trace(case, answer="Sodium is critically low."))

    assert score.citation_precision.denominator == 0
    assert score.citation_precision.exclusion_reason == "no_citations_produced"


def test_safe_refusal_scores_without_invalid_citation_denominator(case: BenchmarkCase) -> None:
    refusal = case.copy(
        update={
            "answer_policy": "safe_no_evidence",
            "expected_facts": (),
            "expected_citations": (),
            "allowed_evidence_ids": (),
        }
    )
    score = score_case(
        refusal,
        _trace(
            refusal,
            answer="I cannot answer from the available evidence.",
            retrieved_evidence_ids=(),
            selected_evidence_ids=(),
            cited_chunks=(),
            refused=True,
        ),
    )

    assert score.refusal_correct is True
    assert score.citation_precision.exclusion_reason == "no_citations_produced"
    assert score.citation_precision.value is None


def test_aggregate_and_gates_fail_closed_for_leakage(case: BenchmarkCase) -> None:
    forbidden = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
    restricted = case.copy(update={"forbidden_evidence_ids": (forbidden,)})
    metrics = aggregate_scores((score_case(restricted, _trace(restricted, selected_evidence_ids=(forbidden,))),))

    gates = {gate.name: gate for gate in evaluate_gates(metrics)}

    assert gates["unauthorized_selected_context"].status == "fail"
    assert gates["unauthorized_selected_context"].actual == 1.0


def test_refusal_metrics_use_only_eligible_populations(case: BenchmarkCase) -> None:
    refusal = case.copy(
        update={
            "case_id": uuid4(),
            "answer_policy": "safe_no_evidence",
            "expected_facts": (),
            "expected_citations": (),
            "allowed_evidence_ids": (),
        }
    )
    scores = (
        score_case(case, _trace(case)),
        score_case(case.copy(update={"case_id": uuid4()}), _trace(case)),
        score_case(refusal, _trace(refusal, answer="fabricated", refused=False, cited_chunks=())),
    )

    metrics = aggregate_scores(scores)

    assert metrics.safe_refusal_recall.denominator == 1
    assert metrics.safe_refusal_recall.value == 0.0
    assert metrics.false_refusal_rate.denominator == 2
    assert metrics.false_refusal_rate.value == 0.0


def test_aggregate_mrr_preserves_rank(case: BenchmarkCase) -> None:
    expected = case.expected_facts[0].evidence_id
    fillers = tuple(uuid4() for _ in range(4))
    score = score_case(case, _trace(case, retrieved_evidence_ids=fillers + (expected,)))

    assert score.mrr_at_5.value == 0.2
    assert aggregate_scores((score,)).mrr_at_5.value == 0.2


def test_partial_ground_truth_leakage_is_detected(case: BenchmarkCase) -> None:
    with pytest.raises(GroundTruthLeakageError):
        assert_no_ground_truth_leakage(case, ("HbA1c|7.2 %|2026-01-02",))

    with pytest.raises(GroundTruthLeakageError):
        assert_no_ground_truth_leakage(case, ('{"value":"7.2 %","field":"HbA1c"}',))


def test_wrong_observation_date_gets_no_citation_recall(case: BenchmarkCase) -> None:
    score = score_case(
        case,
        _trace(
            case,
            answer="HbA1c was 7.2 % on 2025-01-02 [E1].",
            cited_chunks=(
                CitedChunk(
                    evidence_id=case.expected_facts[0].evidence_id,
                    text="HbA1c was 7.2 % on 2025-01-02.",
                    citation_label="E1",
                ),
            ),
        ),
    )

    assert score.citation_recall.value == 0.0


def test_expected_fact_alias_is_bounded(case: BenchmarkCase) -> None:
    aliased_fact = case.expected_facts[0].copy(update={"aliases": ("7.20 %",)})
    aliased = case.copy(update={"expected_facts": (aliased_fact,)})

    score = score_case(aliased, _trace(aliased, answer="HbA1c was 7.20 % on 2026-01-02 [E1]."))

    assert score.fact_recall.value == 1.0


def test_only_critical_facts_enter_critical_support(case: BenchmarkCase) -> None:
    noncritical = case.expected_facts[0].copy(update={"critical": False})
    changed = case.copy(update={"expected_facts": (noncritical,)})

    score = score_case(changed, _trace(changed))

    assert score.critical_fact_support.value is None
    assert score.critical_fact_support.denominator == 0


def test_ablation_and_latency_gates_are_aggregated(case: BenchmarkCase) -> None:
    graph_case = case.copy(update={"category": "graph_only"})
    semantic_case = case.copy(update={"case_id": uuid4(), "category": "single_hop"})
    scores = (
        score_case(graph_case, _trace(graph_case, mode="rag_off", answer="No evidence", cited_chunks=())),
        score_case(graph_case, _trace(graph_case, mode="hybrid_graph_off", answer="No evidence", cited_chunks=())),
        score_case(graph_case, _trace(graph_case, mode="hybrid_graph_on", latency_ms=30)),
        score_case(semantic_case, _trace(semantic_case, mode="rag_off", answer="No evidence", cited_chunks=())),
        score_case(semantic_case, _trace(semantic_case, mode="hybrid_graph_off")),
        score_case(semantic_case, _trace(semantic_case, mode="hybrid_graph_on")),
    )

    metrics = aggregate_scores(scores)
    gates = {gate.name: gate for gate in evaluate_gates(metrics)}

    assert metrics.rag_lift.value == 0.5
    assert metrics.graph_lift.value == 1.0
    assert metrics.graph_semantic_regression.value == 0.0
    assert metrics.p95_latency_ms.value == 30.0
    assert gates["rag_lift"].status == "pass"
    assert gates["graph_lift"].status == "pass"
    assert gates["graph_semantic_regression"].status == "pass"
    assert gates["p95_latency_ms"].status == "pass"


def test_ablation_blocks_on_unpaired_case_populations(case: BenchmarkCase) -> None:
    scores = (
        score_case(case, _trace(case, mode="rag_off", answer="No evidence", cited_chunks=())),
        score_case(case.copy(update={"case_id": uuid4()}), _trace(case, mode="hybrid_graph_off")),
    )

    metrics = aggregate_scores(scores)

    assert metrics.rag_lift.value is None
    assert metrics.rag_lift.exclusion_reason == "missing_rag_off"


def test_graph_credit_requires_supported_graph_claim(case: BenchmarkCase) -> None:
    evidence_id = case.expected_facts[0].evidence_id
    score = score_case(
        case,
        _trace(
            case,
            graph_ran=True,
            graph_selected_evidence_ids=(evidence_id,),
            answer="HbA1c was 4.2 % [E1].",
        ),
    )

    assert score.graph_value_credit is False


def test_graph_credit_requires_graph_evidence_in_selected_context(case: BenchmarkCase) -> None:
    evidence_id = case.expected_facts[0].evidence_id
    score = score_case(
        case,
        _trace(
            case,
            graph_ran=True,
            graph_selected_evidence_ids=(evidence_id,),
            selected_evidence_ids=(),
        ),
    )

    assert score.graph_value_credit is False


def test_all_excluded_aggregate_records_every_exclusion(case: BenchmarkCase) -> None:
    refusal_a = case.copy(update={"expected_facts": (), "expected_citations": (), "allowed_evidence_ids": ()})
    refusal_b = refusal_a.copy(update={"case_id": uuid4()})
    scores = (
        score_case(refusal_a, _trace(refusal_a, answer="No evidence", cited_chunks=())),
        score_case(refusal_b, _trace(refusal_b, answer="No evidence", cited_chunks=())),
    )

    metrics = aggregate_scores(scores)

    assert metrics.citation_precision.excluded_count == 2
    assert metrics.fact_f1.excluded_count == 2


def test_scoring_contracts_are_immutable(case: BenchmarkCase) -> None:
    trace = _trace(case)

    with pytest.raises(TypeError):
        trace.answer = "changed"
