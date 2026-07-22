"""Run source-backed deterministic or live-adapter AI evaluation suites."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = BACKEND_ROOT / "data"
DEFAULT_BENCHMARK_DIR = DEFAULT_DATA_ROOT / "evaluation"


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def _git_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=BACKEND_ROOT,
            capture_output=True,
            check=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _parse_components(raw: str) -> tuple[str, ...]:
    components = tuple(item.strip() for item in raw.split(",") if item.strip())
    allowed = {"corpus", "ocr", "retrieval", "graph", "chat"}
    if not components or set(components) - allowed:
        raise ValueError("components must be a comma-separated subset of corpus,ocr,retrieval,graph,chat")
    return components


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(description=__doc__, add_help=True)
    parser.add_argument("--suite", default="smoke")
    parser.add_argument("--lane", default="deterministic")
    parser.add_argument("--components", default="corpus,ocr,retrieval,graph,chat")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--benchmark-dir", type=Path, default=DEFAULT_BENCHMARK_DIR)
    try:
        args = parser.parse_args(argv)
        components = _parse_components(args.components)
        if args.suite not in {"smoke", "release"} or args.lane not in {"deterministic", "live"}:
            raise ValueError("suite must be smoke|release and lane must be deterministic|live")
    except (ValueError, SystemExit) as error:
        print(f"invalid evaluation configuration: {error}", file=sys.stderr)
        return 2

    sys.path.insert(0, str(BACKEND_ROOT / "src"))
    from hospital_ai.evaluation.runner import EvaluationConfig, run_evaluation, write_run_artifacts

    config = EvaluationConfig(
        suite=args.suite,
        lane=args.lane,
        components=components,
        output_dir=args.output_dir,
        data_root=args.data_root,
        benchmark_dir=args.benchmark_dir,
        environment=os.environ,
        git_sha=_git_sha(),
    )
    run = run_evaluation(config)
    write_run_artifacts(run, config.output_dir)
    print(f"AI evaluation {run.manifest.status}: {config.output_dir}")
    return run.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
