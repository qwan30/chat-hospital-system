"""Build or verify the deterministic, source-backed RAG benchmark."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_FILE = "rag_benchmark_v2.jsonl"
SENTINEL_FILE = "rag_sentinel_v2.jsonl"


def _load_contracts():
    sys.path.insert(0, str(BACKEND_ROOT / "src"))
    from hospital_ai.evaluation.benchmark import (
        EvalCaseV2,
        ReviewRecord,
        build_benchmark,
        select_sentinel,
        validate_benchmark,
        validate_sentinel_review,
    )
    from hospital_ai.evaluation.corpus_manifest import CorpusManifestV2

    return (
        CorpusManifestV2,
        EvalCaseV2,
        ReviewRecord,
        build_benchmark,
        select_sentinel,
        validate_benchmark,
        validate_sentinel_review,
    )


def _render_jsonl(cases) -> str:
    return "".join(case.json(separators=(",", ":"), sort_keys=True) + "\n" for case in cases)


def _read_jsonl(path: Path, case_type) -> tuple:
    return tuple(case_type.parse_raw(line) for line in path.read_text(encoding="utf-8").splitlines() if line)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="Task 2 corpus manifest JSON")
    parser.add_argument("--output-dir", required=True, type=Path, help="benchmark artifact directory")
    parser.add_argument("--check", action="store_true", help="check reproducibility and review gate")
    args = parser.parse_args(argv)

    (
        manifest_type,
        case_type,
        review_type,
        build_benchmark,
        select_sentinel,
        validate_benchmark,
        validate_sentinel_review,
    ) = _load_contracts()
    benchmark_path = args.output_dir / BENCHMARK_FILE
    sentinel_path = args.output_dir / SENTINEL_FILE

    try:
        manifest = manifest_type.parse_raw(args.manifest.read_text(encoding="utf-8"))
        benchmark = build_benchmark(manifest, BACKEND_ROOT / "data")
        benchmark_validation = validate_benchmark(benchmark, manifest, BACKEND_ROOT / "data")
        if not benchmark_validation.valid:
            raise ValueError("; ".join(benchmark_validation.errors))
        sentinel = select_sentinel(benchmark)
        benchmark_rendered = _render_jsonl(benchmark)
        sentinel_rendered = _render_jsonl(sentinel)

        if not args.check:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            benchmark_path.write_text(benchmark_rendered, encoding="utf-8")
            sentinel_path.write_text(sentinel_rendered, encoding="utf-8")
            print(f"wrote {len(benchmark)} benchmark cases and {len(sentinel)} draft sentinel cases")
            return 0

        if not benchmark_path.is_file() or not sentinel_path.is_file():
            raise ValueError("benchmark or sentinel output is missing")
        if benchmark_path.read_text(encoding="utf-8") != benchmark_rendered:
            raise ValueError("benchmark output is stale")

        persisted_sentinel = _read_jsonl(sentinel_path, case_type)
        normalized_sentinel = tuple(
            case.copy(update={"review": review_type(status="draft")}) for case in persisted_sentinel
        )
        if _render_jsonl(normalized_sentinel) != sentinel_rendered:
            raise ValueError("sentinel case selection or source content is stale")

        review_validation = validate_sentinel_review(persisted_sentinel)
        if not review_validation.valid:
            preview = "; ".join(review_validation.errors[:3])
            print(
                f"sentinel review gate blocked ({len(review_validation.errors)} issues): {preview}",
                file=sys.stderr,
            )
            return 3
        print("source-backed benchmark and sentinel review gate are valid")
        return 0
    except (OSError, ValidationError, TypeError, ValueError) as error:
        print(f"invalid RAG benchmark: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
