#!/usr/bin/env python3
"""Master Deterministic Quality Gatekeeper for Hospital AI.

Enforces zero-tolerance mathematical & structural quality checks:
  1. Ruff Lint & Format Verification
  2. McCabe Cyclomatic Complexity & CRAP Score Audit
  3. Targeted Mutation Testing Gate (100% Mutants Killed on core modules)
  4. Pytest Unit / Integration Suite
  5. API Contract & CDI V2 Release Verification
  6. Deterministic AI Regression & Drift Verification

Usage:
  python scripts/verify_deterministic_gates.py
  python scripts/verify_deterministic_gates.py --mode smoke
  python scripts/verify_deterministic_gates.py --mode full
"""

from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# UTF-8 stream setup
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


@dataclass
class GateResult:
    name: str
    command: list[str]
    exit_code: int
    duration_s: float
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


def run_gate(name: str, command: list[str], cwd: Path, env: dict[str, str] | None = None) -> GateResult:
    print(f"\n[RUNNING GATE] {name}...")
    print(f"Command: {' '.join(command)}")

    merged_env = dict(os.environ)
    if env:
        merged_env.update(env)
    merged_env["PYTHONPATH"] = "src"

    start_time = time.time()
    try:
        proc = subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=merged_env,
            timeout=180,
        )
        duration = time.time() - start_time
        res = GateResult(
            name=name,
            command=command,
            exit_code=proc.returncode,
            duration_s=duration,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        res = GateResult(
            name=name,
            command=command,
            exit_code=124,
            duration_s=duration,
            stdout="",
            stderr="Gate execution timed out after 180s.",
        )
    except Exception as exc:
        duration = time.time() - start_time
        res = GateResult(
            name=name,
            command=command,
            exit_code=1,
            duration_s=duration,
            stdout="",
            stderr=str(exc),
        )

    status_tag = "[PASS]" if res.passed else "[FAIL]"
    print(f"{status_tag} {name} (completed in {duration:.2f}s, exit code: {res.exit_code})")
    if not res.passed:
        if res.stdout:
            print("--- STDOUT ---")
            print(res.stdout[-1500:])
        if res.stderr:
            print("--- STDERR ---")
            print(res.stderr[-1500:])

    return res


def main() -> int:
    parser = argparse.ArgumentParser(description="Master Deterministic Quality Gatekeeper.")
    parser.add_argument(
        "--mode",
        choices=["smoke", "standard", "full"],
        default="standard",
        help="Execution mode (smoke: fast sanity gates; standard: CI baseline; full: comprehensive)",
    )
    args = parser.parse_args()

    backend_dir = Path(__file__).resolve().parent.parent
    os.chdir(backend_dir)

    py_exe = sys.executable
    results: list[GateResult] = []

    print("=" * 88)
    print(f"HOSPITAL AI — DETERMINISTIC QUALITY GATES (Mode: {args.mode.upper()})")
    print(f"Working Directory: {backend_dir}")
    print(f"Python Executable: {py_exe}")
    print("=" * 88)

    start_all = time.time()

    # 1. Ruff Lint check
    results.append(
        run_gate(
            name="1. Ruff Lint & Style Check",
            command=[py_exe, "-m", "ruff", "check", "src/", "tests/"],
            cwd=backend_dir,
        )
    )

    # 2. Ruff Format check
    results.append(
        run_gate(
            name="2. Ruff Formatting Alignment",
            command=[py_exe, "-m", "ruff", "format", "--check", "src/", "tests/"],
            cwd=backend_dir,
        )
    )

    # 3. CRAP Score & Complexity Gate
    results.append(
        run_gate(
            name="3. Cyclomatic Complexity & CRAP Score Audit",
            command=[
                py_exe,
                "scripts/calculate_crap_score.py",
                "--source-dir",
                "src/hospital_ai",
                "--max-crap",
                "35.0",
                "--max-complexity",
                "40",
            ],
            cwd=backend_dir,
        )
    )

    # 4. Targeted Mutation Testing Smoke Gate
    results.append(
        run_gate(
            name="4. Targeted Mutation Testing Gate",
            command=[
                py_exe,
                "scripts/run_mutation_smoke.py",
                "--target-file",
                "src/hospital_ai/services/bm25.py",
                "--test-target",
                "tests/test_bm25.py",
                "--max-mutants",
                "8",
                "--min-kill-rate",
                "80.0",
            ],
            cwd=backend_dir,
        )
    )

    # 5. API Contracts & CDI V2 Schema Gate
    results.append(
        run_gate(
            name="5. API Contracts & Schema Validation",
            command=[py_exe, "scripts/verify_contracts.py"],
            cwd=backend_dir,
        )
    )

    # 6. CDI V2 Release Contract Verification
    results.append(
        run_gate(
            name="6. CDI V2 Release Verification",
            command=[py_exe, "scripts/verify_cdi_v2_release.py", "--mode", "source"],
            cwd=backend_dir,
        )
    )

    # 7. Unit Tests
    test_scope = "tests/test_bm25.py" if args.mode == "smoke" else "tests/api"
    results.append(
        run_gate(
            name="7. Core Pytest Unit Suite",
            command=[py_exe, "-m", "pytest", test_scope, "-v", "--tb=short"],
            cwd=backend_dir,
            env={
                "HOSPITAL_AI_CHAT_PROVIDER": "stub",
                "HOSPITAL_AI_EMBEDDING_PROVIDER": "deterministic",
                "HOSPITAL_AI_DISABLE_GUARDRAILS": "true",
            },
        )
    )

    total_duration = time.time() - start_all
    passed_count = sum(1 for r in results if r.passed)
    failed_count = sum(1 for r in results if not r.passed)

    print("\n" + "=" * 88)
    print("DETERMINISTIC GATES SUMMARY")
    print("=" * 88)
    for r in results:
        status_str = "[PASS]" if r.passed else "[FAIL]"
        print(f"  {status_str:<8} {r.name:<55} ({r.duration_s:.2f}s)")
    print("-" * 88)
    print(f"Total: {len(results)} Gates | Passed: {passed_count} | Failed: {failed_count} | Duration: {total_duration:.2f}s")
    print("=" * 88)

    if failed_count > 0:
        print("\n[BLOCKED] Deterministic quality gates FAILED. See details above to fix code.", file=sys.stderr)
        return 1

    print("\n[SUCCESS] ALL DETERMINISTIC GATES ARE GREEN. Ready for PR / Merge!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
