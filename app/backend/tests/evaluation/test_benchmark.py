from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path

import pytest
from pydantic import ValidationError

from hospital_ai.evaluation.benchmark import (
    ActorFixture,
    BenchmarkCase,
    ExpectedFact,
    GraphExpectation,
    GraphRelation,
    assert_graph_facts_current,
    generate_benchmark,
    load_manifest,
    select_sentinel,
    validate_benchmark,
)
from hospital_ai.evaluation.corpus import build_manifest

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
    assert result.source_byte_count == 12_649_758
    assert result.source_errors == ()


def test_generation_fails_closed_when_a_source_is_missing(tmp_path: Path) -> None:
    manifest = load_manifest(MANIFEST_PATH)

    with pytest.raises(ValueError, match="Missing governed source"):
        generate_benchmark(manifest, tmp_path, seed=20260722)

    assert list(tmp_path.iterdir()) == []


def test_validation_of_missing_root_is_side_effect_free(tmp_path: Path) -> None:
    manifest = load_manifest(MANIFEST_PATH)
    missing_root = tmp_path / "does-not-exist"

    result = validate_benchmark((), manifest=manifest, data_root=missing_root)

    assert not result.is_valid
    assert any("does-not-exist" in error for error in result.source_errors)
    assert not missing_root.exists()


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


def test_validation_rejects_fact_and_citation_misbinding(benchmark_cases: tuple[BenchmarkCase, ...]) -> None:
    original = benchmark_cases[0]
    fact = original.expected_facts[0]
    bad_fact = ExpectedFact.parse_obj({**fact.dict(), "source_locator": "csv-row:999999"})
    bad_case = BenchmarkCase.parse_obj(
        {
            **original.dict(),
            "expected_facts": [bad_fact.dict()],
            "expected_citations": [{**original.expected_citations[0].dict(), "source_sha256": "0" * 64}],
        }
    )
    result = validate_benchmark(
        (bad_case, *benchmark_cases[1:]),
        manifest=load_manifest(MANIFEST_PATH),
        data_root=DATA_ROOT,
    )

    assert not result.is_valid
    assert any("expected fact is misbound" in error for error in result.errors)
    assert any("citation is misbound" in error for error in result.errors)


def test_validation_rejects_graph_relation_misbinding(benchmark_cases: tuple[BenchmarkCase, ...]) -> None:
    index, original = next((index, case) for index, case in enumerate(benchmark_cases) if case.category == "graph_only")
    relation = original.graph.required_relations[0]  # type: ignore[union-attr]
    bad_relation = GraphRelation.parse_obj({**relation.dict(), "source_locator": "csv-row:999999"})
    bad_graph = GraphExpectation(required_relations=(bad_relation, *original.graph.required_relations[1:]))  # type: ignore[union-attr]
    bad_case = BenchmarkCase.parse_obj({**original.dict(), "graph": bad_graph.dict()})
    cases = (*benchmark_cases[:index], bad_case, *benchmark_cases[index + 1 :])
    result = validate_benchmark(
        cases,
        manifest=load_manifest(MANIFEST_PATH),
        data_root=DATA_ROOT,
    )

    assert not result.is_valid
    assert any("graph relation is misbound" in error for error in result.errors)


def test_graph_artifact_matches_deterministic_derivation() -> None:
    assert_graph_facts_current(
        load_manifest(MANIFEST_PATH),
        DATA_ROOT,
        DATA_ROOT / "metadata" / "patient_graph_facts.jsonl",
    )


def test_graph_artifact_drift_fails_even_when_manifest_digest_is_updated(tmp_path: Path) -> None:
    copied_root = tmp_path / "corpus"
    shutil.copytree(DATA_ROOT, copied_root)
    graph_path = copied_root / "metadata" / "patient_graph_facts.jsonl"
    graph_path.write_text(graph_path.read_text(encoding="utf-8") + "{}\n", encoding="utf-8", newline="\n")
    refreshed_manifest = build_manifest(copied_root, duplicate_root=None)

    with pytest.raises(ValueError, match="Graph facts artifact drift"):
        assert_graph_facts_current(refreshed_manifest, copied_root, graph_path)


def test_validation_rejects_wrong_patient_forbidden_evidence(benchmark_cases: tuple[BenchmarkCase, ...]) -> None:
    index, original = next(
        (index, case) for index, case in enumerate(benchmark_cases) if case.category == "permission_adversarial"
    )
    other = next(
        case for case in benchmark_cases if case.category == "single_hop" and case.patient_id != original.patient_id
    )
    bad_case = BenchmarkCase.parse_obj({**original.dict(), "forbidden_evidence_ids": [other.allowed_evidence_ids[0]]})
    cases = (*benchmark_cases[:index], bad_case, *benchmark_cases[index + 1 :])
    result = validate_benchmark(cases, manifest=load_manifest(MANIFEST_PATH), data_root=DATA_ROOT)

    assert not result.is_valid
    assert any("forbidden evidence belongs to another patient" in error for error in result.errors)


def test_validation_rejects_authorized_patient_as_overlap_forbidden_evidence(
    benchmark_cases: tuple[BenchmarkCase, ...],
) -> None:
    index, original = next(
        (index, case) for index, case in enumerate(benchmark_cases) if case.category == "overlapping_patient"
    )
    bad_case = BenchmarkCase.parse_obj(
        {**original.dict(), "forbidden_evidence_ids": [original.allowed_evidence_ids[0]]}
    )
    cases = (*benchmark_cases[:index], bad_case, *benchmark_cases[index + 1 :])
    result = validate_benchmark(cases, manifest=load_manifest(MANIFEST_PATH), data_root=DATA_ROOT)

    assert not result.is_valid
    assert any("overlap forbidden evidence belongs to the authorized patient" in error for error in result.errors)


def test_validation_rejects_forbidden_evidence_on_non_adversarial_category(
    benchmark_cases: tuple[BenchmarkCase, ...],
) -> None:
    original = benchmark_cases[0]
    bad_case = BenchmarkCase.parse_obj(
        {**original.dict(), "forbidden_evidence_ids": [original.allowed_evidence_ids[0]]}
    )
    result = validate_benchmark(
        (bad_case, *benchmark_cases[1:]),
        manifest=load_manifest(MANIFEST_PATH),
        data_root=DATA_ROOT,
    )

    assert not result.is_valid
    assert any("category must not contain forbidden evidence" in error for error in result.errors)


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


def test_manifest_models_forbid_unknown_fields() -> None:
    raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    raw["unexpected"] = True

    with pytest.raises(ValidationError):
        type(load_manifest(MANIFEST_PATH)).parse_obj(raw)


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
