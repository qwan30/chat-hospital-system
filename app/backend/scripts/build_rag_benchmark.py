"""Build the deterministic RAG Value Certification v1 source benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hospital_ai.evaluation.benchmark import (
    build_patient_graph_facts,
    generate_benchmark,
    load_manifest,
    select_sentinel,
    validate_benchmark,
)
from hospital_ai.evaluation.corpus import build_manifest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = BACKEND_ROOT / "data" / "hosp_ai_synthetic_dataset"
MANIFEST_PATH = DATA_ROOT / "MANIFEST.json"
GRAPH_FACTS_PATH = DATA_ROOT / "metadata" / "patient_graph_facts.jsonl"
BENCHMARK_PATH = BACKEND_ROOT / "data" / "rag_value_benchmark_v1.jsonl"
SENTINEL_PATH = BACKEND_ROOT / "data" / "rag_value_sentinel_v1.jsonl"


def _write_jsonl(path: Path, values: tuple[object, ...]) -> None:
    rendered = "".join(
        (value.json(sort_keys=True) if hasattr(value, "json") else json.dumps(value, sort_keys=True)) + "\n"
        for value in values
    )
    path.write_text(rendered, encoding="utf-8", newline="\n")


def _refresh_graph_facts() -> None:
    manifest = load_manifest(MANIFEST_PATH)
    graph_facts = build_patient_graph_facts(manifest, DATA_ROOT)
    _write_jsonl(GRAPH_FACTS_PATH, graph_facts)
    refreshed = build_manifest(DATA_ROOT, duplicate_root=None)
    MANIFEST_PATH.write_text(refreshed.json(indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _assert_graph_facts_current(manifest) -> None:
    expected = build_patient_graph_facts(manifest, DATA_ROOT)
    actual = GRAPH_FACTS_PATH.read_text(encoding="utf-8")
    rendered = "".join(value.json(sort_keys=True) + "\n" for value in expected)
    if actual != rendered:
        raise SystemExit("Graph facts artifact drift detected; rerun with --write to regenerate explicitly")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260722)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if args.write:
        _refresh_graph_facts()
    manifest = load_manifest(MANIFEST_PATH)
    if not args.write:
        _assert_graph_facts_current(manifest)
    cases = generate_benchmark(manifest, DATA_ROOT, seed=args.seed)
    sentinel = select_sentinel(cases)
    result = validate_benchmark(cases, manifest=manifest, data_root=DATA_ROOT)
    if not result.is_valid:
        raise SystemExit("Benchmark validation failed: " + "; ".join(result.errors))
    if args.write:
        _write_jsonl(BENCHMARK_PATH, cases)
        _write_jsonl(SENTINEL_PATH, sentinel)
    print(
        f"Validated {len(cases)} cases, {len(sentinel)} pending sentinel cases, "
        f"{result.source_file_count} governed files, {result.source_byte_count} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
