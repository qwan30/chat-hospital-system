from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path

import fitz
import pytest

from hospital_ai.evaluation.benchmark import (
    CATEGORY_COUNTS,
    EvalCaseV2,
    ExpectedFact,
    ReviewRecord,
    build_benchmark,
    select_sentinel,
    validate_benchmark,
    validate_sentinel_review,
)
from hospital_ai.evaluation.corpus_manifest import CorpusManifestV2, EvidenceLocator, build_corpus_manifest

BACKEND_ROOT = Path(__file__).parents[2]
DATA_ROOT = BACKEND_ROOT / "data"
CLI_PATH = BACKEND_ROOT / "scripts" / "build_rag_benchmark.py"


@pytest.fixture(scope="module")
def manifest() -> CorpusManifestV2:
    return build_corpus_manifest(DATA_ROOT)


@pytest.fixture(scope="module")
def cases(manifest: CorpusManifestV2) -> tuple[EvalCaseV2, ...]:
    return build_benchmark(manifest, DATA_ROOT)


def _case_locators(case: EvalCaseV2) -> tuple[EvidenceLocator, ...]:
    fact_locators = tuple(locator for fact in case.expected_facts for locator in fact.evidence)
    graph_locators = case.graph.evidence if case.graph is not None else ()
    return fact_locators + case.allowed_evidence + case.forbidden_evidence + graph_locators


def test_benchmark_has_exact_required_strata(cases: tuple[EvalCaseV2, ...]) -> None:
    assert len(cases) == 300
    assert Counter(case.category for case in cases) == CATEGORY_COUNTS
    assert len({case.case_id for case in cases}) == 300


def test_answer_cases_use_real_source_backed_facts(cases: tuple[EvalCaseV2, ...]) -> None:
    answer_cases = [case for case in cases if case.answer_policy == "answer"]
    assert answer_cases
    for case in answer_cases:
        assert case.expected_facts
        assert case.allowed_evidence
        assert all(fact.evidence for fact in case.expected_facts)
        assert set(case.allowed_evidence).isdisjoint(case.forbidden_evidence)
        assert not any("Canonical " in fact.statement for fact in case.expected_facts)

    multi_document = [case for case in cases if case.category == "multi_document"]
    assert all(len({locator.source_path for locator in case.allowed_evidence}) >= 2 for case in multi_document)


def test_questions_use_source_fact_language_not_internal_ids_or_patient_uuids(
    cases: tuple[EvalCaseV2, ...],
) -> None:
    for case in cases:
        question = case.question.casefold()
        assert str(case.patient_id) not in question
        assert "canonical source" not in question
        if case.answer_policy == "answer":
            fact = next(fact for fact in case.expected_facts if len(fact.verification_terms) >= 2)
            assert fact.fact_id not in question
            assert any(term.casefold() in question for term in fact.verification_terms)
        elif case.category == "safe_refusal":
            assert case.absence_terms[0].casefold() in question


def test_multi_document_facts_match_manifest_document_types(
    cases: tuple[EvalCaseV2, ...], manifest: CorpusManifestV2
) -> None:
    document_type_by_path = {
        artifact.canonical_relative_path: artifact.document_type
        for artifact in manifest.artifacts
        if artifact.kind == "patient_document"
    }
    for case in cases:
        if case.category != "multi_document":
            continue
        document_fact = case.expected_facts[0]
        source_path = document_fact.evidence[0].source_path
        expected_type = document_type_by_path[source_path].replace("_", " ")
        assert expected_type in document_fact.statement.lower()


def test_every_locator_resolves_to_a_canonical_source_and_position(
    cases: tuple[EvalCaseV2, ...], manifest: CorpusManifestV2
) -> None:
    artifacts = {artifact.canonical_relative_path: artifact for artifact in manifest.artifacts}
    for case in cases:
        for locator in _case_locators(case):
            assert locator.source_path in artifacts
            source = DATA_ROOT / locator.source_path
            assert source.is_file()
            if locator.row_number is not None:
                assert locator.row_number <= sum(1 for _ in source.open(encoding="utf-8"))
            if locator.page_number is not None:
                with fitz.open(source) as document:
                    assert locator.page_number <= len(document)


def test_allowed_and_forbidden_evidence_enforce_patient_isolation(
    cases: tuple[EvalCaseV2, ...], manifest: CorpusManifestV2
) -> None:
    patient_by_path = {artifact.canonical_relative_path: artifact.patient_id for artifact in manifest.artifacts}
    for case in cases:
        assert set(case.allowed_evidence).isdisjoint(case.forbidden_evidence)
        assert all(patient_by_path[locator.source_path] == case.patient_id for locator in case.allowed_evidence)
        if case.answer_policy == "answer":
            assert case.patient_id in case.actor.allowed_patient_ids
            assert case.patient_id in case.patient_scope
            assert case.forbidden_evidence
            assert all(patient_by_path[locator.source_path] != case.patient_id for locator in case.forbidden_evidence)
        elif case.category == "permission_adversarial":
            assert not case.allowed_evidence
            assert case.patient_id not in case.actor.allowed_patient_ids
            assert all(patient_by_path[locator.source_path] == case.patient_id for locator in case.forbidden_evidence)
        else:
            assert case.category == "safe_refusal"
            assert not case.allowed_evidence


def test_safe_refusals_are_scoped_to_sources_that_independently_lack_the_requested_terms(
    cases: tuple[EvalCaseV2, ...], manifest: CorpusManifestV2
) -> None:
    safe_refusals = [case for case in cases if case.category == "safe_refusal"]

    assert len(safe_refusals) == CATEGORY_COUNTS["safe_refusal"]
    for case in safe_refusals:
        assert case.absence_terms
        assert len(case.absence_checked_evidence) == 2

    forged_absence = EvalCaseV2.parse_obj(
        {
            **safe_refusals[0].dict(),
            "absence_terms": ["synthetic data warning"],
        }
    )
    result = validate_benchmark((forged_absence, *cases[1:]), manifest, DATA_ROOT)

    assert not result.valid
    assert any("safe-refusal term is present" in error for error in result.errors)


def test_temporal_conflicts_compare_distinct_source_backed_measurements(
    cases: tuple[EvalCaseV2, ...], manifest: CorpusManifestV2
) -> None:
    temporal_cases = [case for case in cases if case.category == "temporal_conflict"]

    assert len(temporal_cases) == CATEGORY_COUNTS["temporal_conflict"]
    assert validate_benchmark(cases, manifest, DATA_ROOT).valid

    unchanged = EvalCaseV2.parse_obj(
        {
            **temporal_cases[0].dict(),
            "expected_facts": [temporal_cases[0].expected_facts[0].dict()] * 2,
            "allowed_evidence": [temporal_cases[0].expected_facts[0].evidence[0].dict()],
        }
    )
    result = validate_benchmark((unchanged, *cases[1:]), manifest, DATA_ROOT)

    assert not result.valid
    assert any("temporal facts" in error for error in result.errors)


def test_validation_resolves_source_content_instead_of_trusting_generated_statements(
    cases: tuple[EvalCaseV2, ...], manifest: CorpusManifestV2
) -> None:
    first = next(case for case in cases if case.answer_policy == "answer")
    forged_fact = ExpectedFact.parse_obj(
        {
            **first.expected_facts[0].dict(),
            "verification_terms": ["not present in any canonical clinical source"],
        }
    )
    forged_case = EvalCaseV2.parse_obj(
        {
            **first.dict(),
            "expected_facts": [forged_fact.dict()],
            "allowed_evidence": [locator.dict() for locator in forged_fact.evidence],
        }
    )
    result = validate_benchmark((forged_case, *cases[1:]), manifest, DATA_ROOT)

    assert not result.valid
    assert any("expected fact is not present" in error for error in result.errors)


def test_validation_rejects_statement_only_forgery_with_original_source_terms(
    cases: tuple[EvalCaseV2, ...], manifest: CorpusManifestV2
) -> None:
    first = next(case for case in cases if case.answer_policy == "answer" and len(case.expected_facts) == 1)
    original_fact = first.expected_facts[0]
    forged_fact = ExpectedFact.parse_obj(
        {
            **original_fact.dict(),
            "statement": "The patient has cancer and requires a chemotherapy regimen.",
        }
    )
    forged_case = EvalCaseV2.parse_obj(
        {
            **first.dict(),
            "expected_facts": [forged_fact.dict()],
            "allowed_evidence": [locator.dict() for locator in forged_fact.evidence],
        }
    )

    result = validate_benchmark((forged_case, *cases[1:]), manifest, DATA_ROOT)

    assert not result.valid
    assert any("statement does not match canonical source" in error for error in result.errors)


def test_validation_rejects_non_resolving_and_overlapping_evidence(
    cases: tuple[EvalCaseV2, ...], manifest: CorpusManifestV2
) -> None:
    first = cases[0]
    bad_locator = EvidenceLocator(source_path="patients_labs/missing.csv", row_number=2)
    broken = EvalCaseV2.parse_obj(
        {
            **first.dict(),
            "allowed_evidence": [bad_locator.dict()],
            "forbidden_evidence": [bad_locator.dict()],
        }
    )

    result = validate_benchmark((broken, *cases[1:]), manifest, DATA_ROOT)

    assert not result.valid
    assert any("does not resolve" in error for error in result.errors)
    assert any("overlap" in error for error in result.errors)


def test_generated_and_persisted_sentinel_are_draft_until_real_review(cases: tuple[EvalCaseV2, ...]) -> None:
    sentinel = select_sentinel(cases)
    persisted_path = DATA_ROOT / "evaluation" / "rag_sentinel_v2.jsonl"
    persisted = tuple(
        EvalCaseV2.parse_raw(line) for line in persisted_path.read_text(encoding="utf-8").splitlines() if line
    )

    assert len(sentinel) == 50
    assert persisted == sentinel
    assert all(case.review.status == "draft" for case in sentinel)
    assert all(not case.review.reviewer_ids for case in sentinel)
    assert not validate_sentinel_review(sentinel).valid


def test_sentinel_gate_requires_two_independent_reviewers_and_resolved_status(cases: tuple[EvalCaseV2, ...]) -> None:
    sentinel = select_sentinel(cases)
    approved = tuple(
        case.copy(
            update={
                "review": ReviewRecord(
                    status="approved",
                    reviewer_ids=("fixture-reviewer-alpha", "fixture-reviewer-beta"),
                )
            }
        )
        for case in sentinel
    )
    duplicated_identity = (
        approved[0].copy(
            update={
                "review": ReviewRecord(
                    status="approved",
                    reviewer_ids=("fixture-reviewer-alpha", "fixture-reviewer-alpha"),
                )
            }
        ),
        *approved[1:],
    )
    unresolved = (
        approved[0].copy(
            update={
                "review": ReviewRecord(
                    status="approved",
                    reviewer_ids=("fixture-reviewer-alpha", "fixture-reviewer-beta"),
                    unresolved_issues=("fixture issue",),
                )
            }
        ),
        *approved[1:],
    )

    assert validate_sentinel_review(approved).valid
    assert not validate_sentinel_review(duplicated_identity).valid
    assert not validate_sentinel_review(unresolved).valid


def test_generation_and_sentinel_selection_are_reproducible(manifest: CorpusManifestV2) -> None:
    first = build_benchmark(manifest, DATA_ROOT)
    second = build_benchmark(manifest, DATA_ROOT)

    assert [case.json(sort_keys=True) for case in first] == [case.json(sort_keys=True) for case in second]
    assert select_sentinel(first) == select_sentinel(second)
    assert json.dumps([case.dict() for case in first], default=str, sort_keys=True) == json.dumps(
        [case.dict() for case in second], default=str, sort_keys=True
    )


def test_cli_writes_reproducible_outputs_and_blocks_unreviewed_sentinel(
    manifest: CorpusManifestV2, tmp_path: Path
) -> None:
    spec = importlib.util.spec_from_file_location("build_rag_benchmark", CLI_PATH)
    assert spec is not None and spec.loader is not None
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    manifest_path = tmp_path / "corpus_manifest_v2.json"
    output_dir = tmp_path / "evaluation"
    manifest_path.write_text(manifest.json(), encoding="utf-8")

    assert cli.main(["--manifest", str(manifest_path), "--output-dir", str(output_dir)]) == 0
    assert (output_dir / "rag_benchmark_v2.jsonl").is_file()
    assert (output_dir / "rag_sentinel_v2.jsonl").is_file()
    assert cli.main(["--manifest", str(manifest_path), "--output-dir", str(output_dir), "--check"]) == 3

    reviewed_lines = []
    for line in (output_dir / "rag_sentinel_v2.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        row["review"] = {
            "status": "approved",
            "reviewer_ids": ["fixture-reviewer-alpha", "fixture-reviewer-beta"],
            "unresolved_issues": [],
        }
        reviewed_lines.append(json.dumps(row, separators=(",", ":"), sort_keys=True))
    (output_dir / "rag_sentinel_v2.jsonl").write_text("\n".join(reviewed_lines) + "\n", encoding="utf-8")

    assert cli.main(["--manifest", str(manifest_path), "--output-dir", str(output_dir), "--check"]) == 0
