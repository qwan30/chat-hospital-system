"""Machine-readable and human-readable AI evaluation artifact writers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from xml.etree import ElementTree

if TYPE_CHECKING:
    from hospital_ai.evaluation.runner import EvaluationRun


def _junit(run: EvaluationRun) -> str:
    total = len(run.cases) or 1
    failures = sum(result.status == "failed" for result in run.cases)
    skipped = sum(result.status == "skipped" for result in run.cases)
    if not run.cases and run.exit_code:
        failures = 1
    suite = ElementTree.Element(
        "testsuite",
        name="ai-evaluation",
        tests=str(total),
        failures=str(failures),
        skipped=str(skipped),
        time=f"{run.manifest.latency_ms / 1000:.3f}",
    )
    if not run.cases:
        case = ElementTree.SubElement(suite, "testcase", name="configuration", classname="evaluation")
        if run.exit_code:
            failure = ElementTree.SubElement(case, "failure", message=run.manifest.failure_reason or "invalid run")
            failure.text = run.manifest.failure_reason
    for result in run.cases:
        case = ElementTree.SubElement(
            suite,
            "testcase",
            name=result.case_id,
            classname=f"evaluation.{result.component}",
            time=f"{result.latency_ms / 1000:.3f}",
        )
        if result.status == "failed":
            failed_names = ", ".join(gate.name for gate in result.gates if not gate.passed)
            failure = ElementTree.SubElement(case, "failure", message=failed_names or result.reason or "gate failure")
            failure.text = result.reason
        elif result.status == "skipped":
            ElementTree.SubElement(case, "skipped", message=result.reason)
    return ElementTree.tostring(suite, encoding="unicode", xml_declaration=True)


def _summary(run: EvaluationRun) -> str:
    failed_gates = [gate for gate in run.gates if gate.hard and not gate.passed]
    lines = [
        "# AI evaluation summary",
        "",
        f"- Verdict: `{run.manifest.status.upper()}`",
        f"- Suite/lane: `{run.manifest.suite}` / `{run.manifest.lane}`",
        f"- Dataset: `{run.manifest.dataset_version}`",
        f"- Git SHA: `{run.manifest.git_sha}`",
        f"- Cases selected: {run.manifest.selected_case_count}",
        (
            "- Results: "
            f"{run.manifest.passed_cases} passed, {run.manifest.failed_cases} failed, "
            f"{run.manifest.skipped_cases} skipped"
        ),
        "",
        "> Deterministic harness fixtures and skipped adapters are not product quality evidence.",
        "",
        "## Blocking gates",
        "",
    ]
    if failed_gates:
        lines.extend(
            f"- `{gate.component}.{gate.name}`: observed `{gate.observed}`; required `{gate.threshold}`"
            + (f" — {gate.details}" if gate.details else "")
            for gate in failed_gates
        )
    else:
        lines.append("- None")
    if run.manifest.failure_reason and not failed_gates:
        lines.extend(("", "## Diagnostic", "", run.manifest.failure_reason))
    return "\n".join(lines) + "\n"


def write_run_artifacts(run: EvaluationRun, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "run.json").write_text(run.manifest.json(indent=2, sort_keys=True) + "\n", encoding="utf-8")
    cases = "".join(result.json(separators=(",", ":"), sort_keys=True) + "\n" for result in run.cases)
    (output_dir / "cases.jsonl").write_text(cases, encoding="utf-8")
    (output_dir / "junit.xml").write_text(_junit(run), encoding="utf-8")
    (output_dir / "summary.md").write_text(_summary(run), encoding="utf-8")
