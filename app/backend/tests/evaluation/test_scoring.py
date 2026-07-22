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
