"""Validate inputs for the legacy RAG evaluator.

Execution/scoring is provided by the RAG Value Certification runner. This
compatibility command deliberately refuses the old self-scored golden fixture.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hospital_ai.evaluation.benchmark import BenchmarkCase


def load_certification_dataset(filepath: str | Path) -> tuple[BenchmarkCase, ...]:
    path = Path(filepath)
    if path.name == "golden_dataset.json":
        raise ValueError("legacy golden_dataset.json is not a certification input")
    if path.suffix != ".jsonl":
        raise ValueError("certification datasets must use the v1 JSONL contract")
    cases = tuple(BenchmarkCase.parse_obj(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines())
    if not cases:
        raise ValueError("certification dataset is empty")
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", nargs="?", default="data/rag_value_benchmark_v1.jsonl")
    args = parser.parse_args()
    cases = load_certification_dataset(args.dataset)
    print(f"Validated {len(cases)} RAG Value Certification v1 cases.")
    print("Use the certification runner for retrieval and answer scoring.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
