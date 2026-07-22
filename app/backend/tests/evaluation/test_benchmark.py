import json
from collections import Counter
from pathlib import Path
from hospital_ai.evaluation.benchmark import CATEGORY_MINIMA, generate_benchmark, validate_benchmark

def test_benchmark_has_required_category_minima():
    assert Counter(c.category for c in generate_benchmark()) == CATEGORY_MINIMA

def test_cases_have_independent_ground_truth():
    for case in generate_benchmark():
        assert case.expected_facts
        assert case.allowed_chunk_ids or case.answer_policy != "answer"
        assert set(case.allowed_chunk_ids).isdisjoint(case.forbidden_chunk_ids)
        assert case.expected_answer_text is None

def test_sentinel_is_reviewed():
    path = Path(__file__).parents[2] / "data/rag_value_sentinel_v1.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 50
    assert all(r["review"]["status"] == "agent-reviewed" and len(r["review"]["reviewers"]) >= 2 for r in rows)

def test_validation_passes():
    assert validate_benchmark(generate_benchmark()).valid
