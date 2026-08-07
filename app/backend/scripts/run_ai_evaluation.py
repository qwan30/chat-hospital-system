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
_PRODUCT_COMPONENTS = {"retrieval", "graph", "chat", "timeline", "stream"}


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
    allowed = {"corpus", "ocr", "retrieval", "graph", "chat", "timeline", "stream"}
    if not components or set(components) - allowed:
        raise ValueError(
            "components must be a comma-separated subset of corpus,ocr,retrieval,graph,chat,timeline,stream"
        )  # noqa: E501
    return components


def _deterministic_product_adapters(
    data_root: Path,
    components: tuple[str, ...],
    *,
    retrieval_mode: str = "vector",
):
    """Build the isolated product adapters used by the deterministic lane only."""

    from hospital_ai.evaluation.adapter_foundation import EvaluatorIsolationConfig

    source_root = data_root.resolve()
    requested = {}
    if "retrieval" in components:
        from hospital_ai.evaluation.product_retrieval_adapter import ProductRetrievalAdapter

        requested["retrieval"] = ProductRetrievalAdapter(source_root, retrieval_mode=retrieval_mode)
    if "graph" in components:
        from hospital_ai.evaluation.product_graph_adapter import ProductGraphAdapter

        requested["graph"] = ProductGraphAdapter(source_root)
    if "chat" in components:
        from hospital_ai.evaluation.product_chat_adapter import ProductChatAdapter

        requested["chat"] = ProductChatAdapter(source_root)
    if "timeline" in components:
        from hospital_ai.evaluation.product_timeline_adapter import ProductTimelineAdapter

        requested["timeline"] = ProductTimelineAdapter(source_root)
    if "stream" in components:
        from hospital_ai.evaluation.product_stream_adapter import ProductStreamAdapter

        requested["stream"] = ProductStreamAdapter(source_root)
    isolation = EvaluatorIsolationConfig(
        evaluation_database_url="sqlite+aiosqlite:///:memory:",
        approved_evaluation_database_url="sqlite+aiosqlite:///:memory:",
        product_database_url="sqlite+aiosqlite:///product.db",
        run_namespace="ai-eval/deterministic-cli",
    )
    return requested, isolation


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(description=__doc__, add_help=True)
    parser.add_argument("--suite", default="smoke")
    parser.add_argument("--lane", default="deterministic")
    parser.add_argument("--components", default="corpus,ocr,retrieval,graph,chat,timeline,stream")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--benchmark-dir", type=Path, default=DEFAULT_BENCHMARK_DIR)
    parser.add_argument("--retrieval-mode", choices=("vector", "bm25", "hybrid", "graph"), default="vector")
    parser.add_argument("--llm-judge-provider", choices=("gemini", "local", "stub"), default="stub")
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
        retrieval_mode=args.retrieval_mode,
        llm_judge_provider=args.llm_judge_provider,
        environment=os.environ,
        git_sha=_git_sha(),
    )
    adapters = None
    isolation = None
    if args.lane == "deterministic" and set(components) & _PRODUCT_COMPONENTS:
        adapters, isolation = _deterministic_product_adapters(
            args.data_root,
            components,
            retrieval_mode=args.retrieval_mode,
        )
    run = run_evaluation(config, adapters=adapters, isolation=isolation)
    write_run_artifacts(run, config.output_dir)

    from hospital_ai.evaluation.artifact_generator import load_measured_artifacts, check_measured_thresholds
    
    cases_path = config.output_dir / "cases.jsonl"
    if cases_path.exists():
        artifacts = load_measured_artifacts(cases_path)
        if artifacts and not check_measured_thresholds(artifacts):
            print("AI evaluation failed: measured metrics below thresholds", file=sys.stderr)
            return 1

    print(f"AI evaluation {run.manifest.status}: {config.output_dir}")
    return run.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
