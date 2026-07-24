"""Executive CLI entrypoint for AI Baseline Regression & Drift Detector."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT / "src"))

from hospital_ai.evaluation.drift_detector import evaluate_metric_drift  # noqa: E402


def _format_markdown_summary(result_dict: dict) -> str:
    verdict = result_dict["verdict"]
    badge = "🟢 **GO / PASSED**" if verdict == "GO" else "🔴 **NO-GO / BLOCKED**"
    sha_cand = result_dict.get("git_sha_candidate", "unknown")
    sha_base = result_dict.get("git_sha_baseline", "unknown")
    lines = [
        "# 🛡️ AI Baseline Regression & Drift Detector Report",
        "",
        f"**Verdict:** {badge}",
        f"**Candidate Commit:** `{sha_cand}` | **Baseline Commit:** `{sha_base}`",
        (
            f"**Evaluated Metrics:** {result_dict['total_metrics_evaluated']} | "
            f"**Violations:** {result_dict['violation_count']}"
        ),
        "",
    ]

    if result_dict["violations"]:
        lines.append("### 🔴 Violations")
        for v in result_dict["violations"]:
            lines.append(f"- ❌ **`{v['metric_name']}`**: {v['message']}")
        lines.append("")

    lines.extend(
        [
            "### 📊 Full Metric Drift Comparison",
            "",
            "| Metric Name | Baseline | Candidate | Delta | Status |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ]
    )
    for c in result_dict["comparisons"]:
        st = "🟢 PASSED" if c["status"] == "passed" else f"🔴 FAILED ({c['status']})"
        lines.append(
            f"| `{c['metric_name']}` | {c['baseline_value']:.4f} | {c['candidate_value']:.4f} | "
            f"{c['delta']:+.4f} | {st} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    default_baseline = BACKEND_ROOT / "data" / "evaluation" / "baselines" / "baseline-release.json"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--baseline", type=Path, default=default_baseline)

    parser.add_argument("--output-report", type=Path)
    parser.add_argument("--github-summary", action="store_true")
    parser.add_argument("--no-strict", dest="strict", action="store_false", default=True)

    args = parser.parse_args(argv)

    if not args.candidate.exists():
        print(f"Error: Candidate summary file not found at {args.candidate}", file=sys.stderr)
        return 2

    if not args.baseline.exists():
        print(f"Error: Baseline summary file not found at {args.baseline}", file=sys.stderr)
        return 2

    candidate_data = json.loads(args.candidate.read_text(encoding="utf-8"))
    baseline_data = json.loads(args.baseline.read_text(encoding="utf-8"))

    result = evaluate_metric_drift(
        candidate_summary=candidate_data,
        baseline_summary=baseline_data,
        git_sha_candidate=candidate_data.get("git_sha", "unknown"),
        git_sha_baseline=baseline_data.get("git_sha", "unknown"),
    )

    res_dict = result.model_dump() if hasattr(result, "model_dump") else result.dict()

    if args.output_report:
        args.output_report.parent.mkdir(parents=True, exist_ok=True)
        args.output_report.write_text(json.dumps(res_dict, indent=2), encoding="utf-8")

    md_summary = _format_markdown_summary(res_dict)
    print(md_summary)

    if args.github_summary and "GITHUB_STEP_SUMMARY" in os.environ:
        summary_path = Path(os.environ["GITHUB_STEP_SUMMARY"])
        with summary_path.open("a", encoding="utf-8") as f:
            f.write(md_summary)

    return 0 if (result.passed or not args.strict) else 1


if __name__ == "__main__":
    sys.exit(main())
