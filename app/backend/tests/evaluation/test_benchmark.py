from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest
from pydantic import ValidationError

from hospital_ai.evaluation.benchmark import (
    ActorFixture,
    BenchmarkCase,
    ExpectedFact,
    generate_benchmark,
    load_manifest,
    select_sentinel,
    validate_benchmark,
)

DATA_ROOT = Path(__file__).parents[2] / "data" / "hosp_ai_synthetic_dataset"
MANIFEST_PATH = DATA_ROOT / "MANIFEST.json"


@pytest.fixture(scope="module")
def benchmark_cases() -> tuple[BenchmarkCase, ...]:
    return generate_benchmark(load_manifest(MANIFEST_PATH), DATA_ROOT, seed=20260722)


def test_manifest_requires_all_governed_source_bytes() -> None:
    manifest = load_manifest(MANIFEST_PATH)
    result = validate_benchmark((), manifest=manifest, data_root=DATA_ROOT)

    # 210 canonical source files plus one governed, source-derived graph artifact.
    assert result.source_file_count == 211
    assert result.source_byte_count == 9_503_158
    assert result.source_errors == ()


def test_generation_fails_closed_when_a_source_is_missing(tmp_path: Path) -> None:
    manifest = load_manifest(MANIFEST_PATH)

    with pytest.raises(ValueError, match="Missing governed source"):
        generate_benchmark(manifest, tmp_path, seed=20260722)


def test_benchmark_has_required_category_minima(benchmark_cases: tuple[BenchmarkCase, ...]) -> None:
    assert Counter(case.category for case in benchmark_cases) == {
        "single_hop": 70,
        "multi_document": 50,
        "temporal_conflict": 35,
        "graph_only": 45,
        "overlapping_patient": 30,
        "permission_adversarial": 45,
        "safe_refusal": 25,
    }


def test_cases_are_corpus_backed_without_expected_prose(benchmark_cases: tuple[BenchmarkCase, ...]) -> None:
    for case in benchmark_cases:
        assert case.expected_answer_text is None
        assert set(case.allowed_evidence_ids).isdisjoint(case.forbidden_evidence_ids)
        assert all(fact.source_sha256 for fact in case.expected_facts)
        assert all(fact.source_locator for fact in case.expected_facts)
        assert all(citation.evidence_id in case.allowed_evidence_ids for citation in case.expected_citations)


def test_category_semantics_are_structural(benchmark_cases: tuple[BenchmarkCase, ...]) -> None:
    for case in benchmark_cases:
        source_paths = {fact.source_path for fact in case.expected_facts}
        if case.category == "multi_document":
            assert len(source_paths) >= 2
        elif case.category == "temporal_conflict":
            assert len({fact.observed_at for fact in case.expected_facts}) >= 2
            assert case.temporal_rule == "latest_observation_wins"
        elif case.category == "graph_only":
            assert case.graph is not None
            assert len(case.graph.required_relations) >= 2
        elif case.category == "overlapping_patient":
            assert case.forbidden_evidence_ids
        elif case.category == "permission_adversarial":
            assert case.answer_policy == "scoped_refusal"
            assert case.patient_id not in case.actor.allowed_patient_ids
        elif case.category == "safe_refusal":
            assert case.answer_policy == "safe_no_evidence"
            assert not case.expected_facts
            assert not case.expected_citations


def test_source_cases_are_not_falsely_certification_ready(benchmark_cases: tuple[BenchmarkCase, ...]) -> None:
    result = validate_benchmark(benchmark_cases, require_indexed=True)

    assert not result.is_valid
    assert result.unresolved_evidence_count > 0


def test_sentinel_is_stratified_and_pending(benchmark_cases: tuple[BenchmarkCase, ...]) -> None:
    sentinel = select_sentinel(benchmark_cases, count=50)

    assert len(sentinel) == 50
    assert set(Counter(case.category for case in sentinel)) == set(Counter(case.category for case in benchmark_cases))
    assert all(case.review.status == "pending" for case in sentinel)
    assert all(case.review.reviews == () for case in sentinel)


def test_nested_models_are_frozen_and_forbid_extras() -> None:
    actor = ActorFixture(role="doctor", actor_id="benchmark-doctor", allowed_patient_ids=())
    with pytest.raises(TypeError):
        actor.role = "admin"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        ExpectedFact(
            field="test",
            value="value",
            source_path="x.csv",
            source_sha256="0" * 64,
            source_locator="row:2",
            evidence_id="00000000-0000-0000-0000-000000000001",
            invented=True,
        )


def test_generation_is_byte_stable(benchmark_cases: tuple[BenchmarkCase, ...]) -> None:
    rendered_once = "".join(case.json(sort_keys=True) + "\n" for case in benchmark_cases)
    rendered_twice = "".join(
        case.json(sort_keys=True) + "\n"
        for case in generate_benchmark(load_manifest(MANIFEST_PATH), DATA_ROOT, seed=20260722)
    )

    assert rendered_once == rendered_twice


def test_checked_in_benchmark_matches_generator(benchmark_cases: tuple[BenchmarkCase, ...]) -> None:
    path = DATA_ROOT.parent / "rag_value_benchmark_v1.jsonl"
    checked_in = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    assert checked_in == [json.loads(case.json()) for case in benchmark_cases]
