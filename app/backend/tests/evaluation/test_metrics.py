from __future__ import annotations

import math

from hospital_ai.evaluation.metrics import (
    character_error_rate,
    citation_metrics,
    critical_field_accuracy,
    csv_structural_accuracy,
    fact_coverage,
    refusal_success,
    retrieval_metrics,
    safety_leak_counts,
    word_error_rate,
)


def test_character_and_word_error_rates_use_edit_distance() -> None:
    character = character_error_rate("dose 10 mg", "dose 11 mg")
    word = word_error_rate("take one tablet daily", "take tablet daily")

    assert character.errors == 1
    assert character.reference_units == 10
    assert character.rate == 0.1
    assert word.errors == 1
    assert word.reference_units == 4
    assert word.rate == 0.25


def test_error_rates_handle_empty_reference_without_division_by_zero() -> None:
    assert character_error_rate("", "").rate == 0.0
    assert character_error_rate("", "abc").rate == 1.0
    assert word_error_rate("", "unexpected").rate == 1.0


def test_critical_field_accuracy_is_exact_after_whitespace_normalization() -> None:
    result = critical_field_accuracy(
        {"dose": "10 mg", "date": "2026-07-22", "drug": "Metformin"},
        {"dose": " 10   mg ", "date": "2026-07-23", "drug": "metformin"},
    )

    assert result.correct == 2
    assert result.total == 3
    assert result.accuracy == 2 / 3
    assert result.failed_keys == ("date",)


def test_csv_structural_accuracy_reports_shape_cell_and_numeric_preservation() -> None:
    expected = [["test", "value"], ["Creatinine", "1.20"], ["Sodium", "140"]]
    actual = [["test", "value"], ["Creatinine", "1.2"], ["Sodium"]]

    result = csv_structural_accuracy(expected, actual)

    assert result.row_count_accuracy == 1.0
    assert result.column_shape_accuracy == 2 / 3
    assert result.cell_accuracy == 4 / 6
    assert result.numeric_accuracy == 1 / 2


def test_retrieval_metrics_use_ranked_unique_results_and_standard_dcg() -> None:
    result = retrieval_metrics(
        ranked_ids=["noise", "relevant-a", "relevant-a", "relevant-b"],
        relevant_ids={"relevant-a", "relevant-b", "relevant-c"},
        k=3,
    )

    assert result.recall_at_k == 1 / 3
    assert result.precision_at_k == 1 / 3
    assert result.mrr == 0.5
    ideal_dcg = 1 + 1 / math.log2(3) + 1 / math.log2(4)
    assert result.ndcg_at_k == (1 / math.log2(3)) / ideal_dcg


def test_retrieval_metrics_are_zero_when_no_relevant_items_exist() -> None:
    result = retrieval_metrics(["a"], set(), k=5)

    assert result.recall_at_k == 0.0
    assert result.precision_at_k == 0.0
    assert result.mrr == 0.0
    assert result.ndcg_at_k == 0.0


def test_citation_precision_recall_and_fact_coverage_report_denominators() -> None:
    citations = citation_metrics(["a", "forged"], {"a", "b"})
    facts = fact_coverage({"f1", "f2", "f3"}, {"f1", "f3", "other"})

    assert (citations.true_positive, citations.false_positive, citations.false_negative) == (1, 1, 1)
    assert citations.precision == 0.5
    assert citations.recall == 0.5
    assert facts.correct == 2
    assert facts.total == 3
    assert facts.accuracy == 2 / 3


def test_refusal_and_safety_leak_counts_are_deterministic() -> None:
    assert refusal_success(expected_refusal=True, refused=True)
    assert refusal_success(expected_refusal=False, refused=False)
    assert not refusal_success(expected_refusal=True, refused=False)

    leaks = safety_leak_counts(
        retrieved_ids={"allowed", "wrong-patient", "unauthorized"},
        allowed_ids={"allowed"},
        wrong_patient_ids={"wrong-patient"},
        cited_ids={"allowed", "fabricated"},
        known_ids={"allowed", "wrong-patient", "unauthorized"},
        provenance_ids={"allowed"},
        expected_refusal=True,
        refused=False,
        sync_safety_outcome="refused",
        stream_safety_outcome="answered",
    )

    assert leaks.unauthorized_evidence == 2
    assert leaks.wrong_patient_evidence == 1
    assert leaks.fabricated_citations == 1
    assert leaks.missing_provenance == 2
    assert leaks.unsafe_refusals == 1
    assert leaks.transport_mismatches == 1
    assert leaks.total == 8
