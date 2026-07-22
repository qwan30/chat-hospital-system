from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from xml.etree import ElementTree

import pytest

from hospital_ai.evaluation.contracts import CaseResult, GateResult, OcrEngineStatus
from hospital_ai.evaluation.runner import (
    CaseObservation,
    EvaluationConfig,
    run_evaluation,
    write_run_artifacts,
)

BACKEND_ROOT = Path(__file__).parents[2]
DATA_ROOT = BACKEND_ROOT / "data"
BENCHMARK_DIR = DATA_ROOT / "evaluation"
CLI_PATH = BACKEND_ROOT / "scripts" / "run_ai_evaluation.py"


def _load_cli():
    spec = importlib.util.spec_from_file_location("run_ai_evaluation", CLI_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _approved_benchmark_dir(tmp_path: Path) -> Path:
    output = tmp_path / "benchmarks"
    output.mkdir()
    (output / "rag_benchmark_v2.jsonl").write_bytes((BENCHMARK_DIR / "rag_benchmark_v2.jsonl").read_bytes())
    reviewed = []
    for line in (BENCHMARK_DIR / "rag_sentinel_v2.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        row["review"] = {
            "status": "approved",
            "reviewer_ids": ["independent-reviewer-alpha", "independent-reviewer-beta"],
            "unresolved_issues": [],
        }
        reviewed.append(json.dumps(row, separators=(",", ":"), sort_keys=True))
    (output / "rag_sentinel_v2.jsonl").write_text("\n".join(reviewed) + "\n", encoding="utf-8")
    return output


def _config(
    tmp_path: Path,
    benchmark_dir: Path,
    *,
    suite: str = "smoke",
    lane: str = "deterministic",
    components: tuple[str, ...] = ("corpus", "retrieval", "graph", "chat"),
    environment: dict[str, str] | None = None,
) -> EvaluationConfig:
    return EvaluationConfig(
        suite=suite,
        lane=lane,
        components=components,
        output_dir=tmp_path / "artifacts",
        data_root=DATA_ROOT,
        benchmark_dir=benchmark_dir,
        environment=environment or {},
        git_sha="fixture-git-sha",
        clock=lambda: "2026-07-22T12:00:00Z",
    )


def test_result_contracts_preserve_machine_readable_scalar_types() -> None:
    result = CaseResult(
        case_id="contract-fixture",
        component="harness",
        status="passed",
        metrics={"score": 0.5, "count": 2, "ok": True},
    )
    gate = GateResult(
        name="typed-observation",
        component="harness",
        passed=True,
        hard=True,
        observed=2,
        threshold="= 2",
    )

    assert result.metrics == {"score": 0.5, "count": 2, "ok": True}
    assert isinstance(result.metrics["score"], float)
    assert isinstance(result.metrics["count"], int)
    assert isinstance(result.metrics["ok"], bool)
    assert gate.observed == 2
    assert isinstance(gate.observed, int)


def test_deterministic_smoke_validates_reviewed_sentinel_and_writes_all_artifacts(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("corpus",))

    run = run_evaluation(config)
    write_run_artifacts(run, config.output_dir)

    assert run.exit_code == 0
    assert run.manifest.status == "passed"
    assert run.manifest.selected_case_count == 50
    for filename in ("run.json", "cases.jsonl", "junit.xml", "summary.md"):
        assert (config.output_dir / filename).is_file()
    run_json = json.loads((config.output_dir / "run.json").read_text(encoding="utf-8"))
    assert run_json["dataset_version"] == "synthetic-100-v2"
    assert run_json["git_sha"] == "fixture-git-sha"
    assert run_json["prompt_version"] == "not-applicable-deterministic"
    assert "token_usage" in run_json
    ElementTree.parse(config.output_dir / "junit.xml")
    assert "not product quality evidence" in (config.output_dir / "summary.md").read_text(encoding="utf-8")


def test_requested_product_component_without_adapter_fails_required_component_gate(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("retrieval",))

    run = run_evaluation(config)

    assert run.exit_code == 1
    assert run.manifest.status == "failed"
    assert any(
        gate.name == "evaluation_adapter_configured" and gate.component == "retrieval" and gate.hard and not gate.passed
        for gate in run.gates
    )
    retrieval_results = [result for result in run.cases if result.component == "retrieval"]
    assert retrieval_results
    assert all(result.status == "skipped" for result in retrieval_results)


def test_unreviewed_real_sentinel_is_a_gate_failure_not_invalid_data(tmp_path: Path) -> None:
    run = run_evaluation(_config(tmp_path, BENCHMARK_DIR, components=("corpus",)))

    assert run.exit_code == 1
    assert run.manifest.status == "failed"
    review_gate = next(gate for gate in run.gates if gate.name == "sentinel_independent_review")
    assert review_gate.hard
    assert not review_gate.passed
    assert review_gate.observed == 0


def test_requested_image_ocr_fails_explicitly_when_engine_is_unavailable(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("ocr",))

    run = run_evaluation(
        config,
        ocr_probe=lambda: OcrEngineStatus(
            status="engine_unavailable",
            available=False,
            reason="missing paddleocr and paddlepaddle",
        ),
    )

    assert run.exit_code == 1
    result = next(result for result in run.cases if result.case_id == "ocr-image-engine")
    assert result.status == "failed"
    assert result.reason == "missing paddleocr and paddlepaddle"
    assert not any(result.metrics.get("cer") == 0 for result in run.cases if result.case_id == "ocr-image-engine")


def test_live_lane_without_credentials_is_explicitly_skipped_without_scores(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(
        tmp_path,
        benchmark_dir,
        lane="live",
        components=("retrieval", "graph", "chat"),
        environment={},
    )

    run = run_evaluation(config)

    assert run.exit_code == 0
    assert run.manifest.status == "skipped"
    product_results = [result for result in run.cases if result.component in {"retrieval", "graph", "chat"}]
    assert product_results
    assert all(result.status == "skipped" for result in product_results)
    assert all("credentials" in result.reason for result in product_results)
    assert all(1.0 not in result.metrics.values() for result in product_results)


class _LeakingAdapter:
    def evaluate(self, _case) -> CaseObservation:
        return CaseObservation(
            retrieved_ids=("fabricated-source",),
            cited_ids=("fabricated-source",),
            provenance_ids=(),
            covered_fact_ids=(),
            refused=False,
            sync_safety_outcome="answered",
            stream_safety_outcome="answered",
        )


def test_adapter_observation_that_leaks_evidence_fails_hard_gates(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, components=("chat",))

    run = run_evaluation(config, adapters={"chat": _LeakingAdapter()})

    assert run.exit_code == 1
    assert any(gate.hard and not gate.passed and gate.name == "zero_unauthorized_evidence" for gate in run.gates)
    assert any(gate.hard and not gate.passed and gate.name == "zero_fabricated_citations" for gate in run.gates)


def test_release_selects_all_300_cases(tmp_path: Path) -> None:
    benchmark_dir = _approved_benchmark_dir(tmp_path)
    config = _config(tmp_path, benchmark_dir, suite="release", components=("corpus",))

    run = run_evaluation(config)

    assert run.exit_code == 0
    assert run.manifest.selected_case_count == 300


def test_invalid_dataset_returns_two_and_still_writes_diagnostic_artifacts(tmp_path: Path) -> None:
    config = EvaluationConfig(
        suite="smoke",
        lane="deterministic",
        components=("corpus",),
        output_dir=tmp_path / "artifacts",
        data_root=tmp_path / "missing-data",
        benchmark_dir=tmp_path / "missing-benchmarks",
        environment={},
        git_sha="fixture",
        clock=lambda: "2026-07-22T12:00:00Z",
    )

    run = run_evaluation(config)
    write_run_artifacts(run, config.output_dir)

    assert run.exit_code == 2
    assert run.manifest.status == "invalid"
    assert (config.output_dir / "run.json").is_file()
    assert "data root" in (config.output_dir / "summary.md").read_text(encoding="utf-8").lower()


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["--suite", "unknown"], 2),
        (["--lane", "invalid"], 2),
        (["--components", "corpus,unknown"], 2),
    ],
)
def test_cli_invalid_configuration_returns_two_without_argparse_escape(
    tmp_path: Path, argv: list[str], expected: int
) -> None:
    cli = _load_cli()
    base = ["--output-dir", str(tmp_path / "out")]

    assert cli.main(base + argv) == expected


def test_cli_main_returns_gate_exit_and_writes_artifacts(tmp_path: Path) -> None:
    cli = _load_cli()
    output = tmp_path / "out"

    exit_code = cli.main(
        [
            "--suite",
            "smoke",
            "--lane",
            "deterministic",
            "--components",
            "corpus",
            "--output-dir",
            str(output),
            "--data-root",
            str(DATA_ROOT),
            "--benchmark-dir",
            str(BENCHMARK_DIR),
        ]
    )

    assert exit_code == 1
    assert (output / "run.json").is_file()
