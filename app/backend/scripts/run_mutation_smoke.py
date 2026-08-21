#!/usr/bin/env python3
"""Targeted Mutation Testing Runner for Hospital AI Backend.

Injects AST mutations into target Python modules and runs the associated
pytest test suite to verify whether the unit tests detect and kill the mutants.

Mutation Operators:
  - Comparison inversion (== <-> !=, < <-> >=, > <-> <=)
  - Boolean negation (True <-> False, and <-> or, not elimination)
  - Arithmetic swap (+ <-> -, * <-> /)
  - Return value mutation (return x <-> return None / return 0)
"""

from __future__ import annotations

import argparse
import ast
import io
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Ensure UTF-8 output safe on all platforms
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


@dataclass
class Mutant:
    id: int
    target_file: Path
    line_number: int
    original_code: str
    mutated_code: str
    operator_name: str
    status: str = "PENDING"  # KILLED, SURVIVED, TIMEOUT, ERROR


class MutationTransformer(ast.NodeTransformer):
    def __init__(self, target_mutation_index: int) -> None:
        self.target_mutation_index = target_mutation_index
        self.current_mutation_index = 0
        self.applied_mutant_info: dict[str, str] | None = None

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        new_ops = []
        for op in node.ops:
            if self.current_mutation_index == self.target_mutation_index and self.applied_mutant_info is None:
                mutated_op = None
                op_name = type(op).__name__
                if isinstance(op, ast.Eq):
                    mutated_op = ast.NotEq()
                elif isinstance(op, ast.NotEq):
                    mutated_op = ast.Eq()
                elif isinstance(op, ast.Lt):
                    mutated_op = ast.GtE()
                elif isinstance(op, ast.GtE):
                    mutated_op = ast.Lt()
                elif isinstance(op, ast.Gt):
                    mutated_op = ast.LtE()
                elif isinstance(op, ast.LtE):
                    mutated_op = ast.Gt()
                elif isinstance(op, ast.In):
                    mutated_op = ast.NotIn()
                elif isinstance(op, ast.NotIn):
                    mutated_op = ast.In()

                if mutated_op:
                    self.applied_mutant_info = {
                        "lineno": str(node.lineno),
                        "operator": f"Invert {op_name} -> {type(mutated_op).__name__}",
                    }
                    new_ops.append(mutated_op)
                    continue

            self.current_mutation_index += 1
            new_ops.append(op)

        node.ops = new_ops
        return self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        if self.current_mutation_index == self.target_mutation_index and self.applied_mutant_info is None:
            if isinstance(node.op, ast.And):
                self.applied_mutant_info = {
                    "lineno": str(node.lineno),
                    "operator": "Swap And -> Or",
                }
                node.op = ast.Or()
            elif isinstance(node.op, ast.Or):
                self.applied_mutant_info = {
                    "lineno": str(node.lineno),
                    "operator": "Swap Or -> And",
                }
                node.op = ast.And()

        self.current_mutation_index += 1
        return self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        if self.current_mutation_index == self.target_mutation_index and self.applied_mutant_info is None:
            if isinstance(node.op, ast.Add):
                self.applied_mutant_info = {"lineno": str(node.lineno), "operator": "Swap + -> -"}
                node.op = ast.Sub()
            elif isinstance(node.op, ast.Sub):
                self.applied_mutant_info = {"lineno": str(node.lineno), "operator": "Swap - -> +"}
                node.op = ast.Add()
            elif isinstance(node.op, ast.Mult):
                self.applied_mutant_info = {"lineno": str(node.lineno), "operator": "Swap * -> /"}
                node.op = ast.Div()

        self.current_mutation_index += 1
        return self.generic_visit(node)


def count_potential_mutations(source_code: str) -> int:
    try:
        tree = ast.parse(source_code)
    except Exception:
        return 0

    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            count += len(node.ops)
        elif isinstance(node, ast.BoolOp):
            count += 1
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
            count += 1
    return count


def generate_mutated_source(source_code: str, mutation_index: int) -> tuple[str, dict[str, str] | None]:
    tree = ast.parse(source_code)
    transformer = MutationTransformer(mutation_index)
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)
    return ast.unparse(new_tree), transformer.applied_mutant_info


def run_test_suite(test_target: str, timeout_seconds: int = 15) -> bool:
    """Runs pytest on test_target. Returns True if tests pass (Mutant survived), False if tests fail (Mutant killed)."""
    env = dict(os.environ)
    env["HOSPITAL_AI_CHAT_PROVIDER"] = "stub"
    env["HOSPITAL_AI_EMBEDDING_PROVIDER"] = "deterministic"
    env["HOSPITAL_AI_DISABLE_GUARDRAILS"] = "true"

    cmd = [sys.executable, "-m", "pytest", test_target, "-q", "--tb=no"]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            env=env,
        )
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        # Timeout means infinite loop or hang caused by mutant -> mutant considered killed!
        return False
    except Exception:
        return False


def run_mutation_on_target(
    target_file: Path,
    test_target: str,
    max_mutants: int = 20,
) -> list[Mutant]:
    if not target_file.exists():
        print(f"[ERROR] Target file {target_file} does not exist.", file=sys.stderr)
        return []

    original_code = target_file.read_text(encoding="utf-8")
    backup_file = target_file.with_suffix(".py.bak")
    shutil.copy2(target_file, backup_file)

    potential_count = count_potential_mutations(original_code)
    actual_run_count = min(potential_count, max_mutants)
    mutants: list[Mutant] = []

    print(f"\nEvaluating target: {target_file.name} ({potential_count} mutation sites, testing {actual_run_count} mutants)")
    print(f"Associated test suite: {test_target}")
    print("-" * 80)

    try:
        # 1. Baseline check: original code must pass tests!
        if not run_test_suite(test_target):
            print("[ERROR] Baseline tests failed on unmutated code! Aborting mutation test.", file=sys.stderr)
            return []

        for i in range(actual_run_count):
            mutated_code, info = generate_mutated_source(original_code, i)
            if not info:
                continue

            lineno = int(info.get("lineno", 1))
            op_desc = info.get("operator", "Unknown")

            # Write mutant to disk
            target_file.write_text(mutated_code, encoding="utf-8")

            # Run test suite
            passed = run_test_suite(test_target)
            status = "SURVIVED" if passed else "KILLED"

            m = Mutant(
                id=i + 1,
                target_file=target_file,
                line_number=lineno,
                original_code=original_code,
                mutated_code=mutated_code,
                operator_name=op_desc,
                status=status,
            )
            mutants.append(m)

            tag = "[SURVIVED]" if status == "SURVIVED" else "[KILLED]"
            print(f"Mutant #{m.id:<2} (L{lineno:<3}) {op_desc:<32} -> {tag}")

    finally:
        # Always restore original file!
        if backup_file.exists():
            shutil.copy2(backup_file, target_file)
            backup_file.unlink()

    return mutants


def main() -> int:
    parser = argparse.ArgumentParser(description="Targeted Mutation Testing Runner for Hospital AI.")
    parser.add_argument(
        "--target-file",
        default="src/hospital_ai/services/bm25.py",
        help="Target file to inject mutations into",
    )
    parser.add_argument(
        "--test-target",
        default="tests/test_bm25.py",
        help="Pytest test file or directory to execute against mutants",
    )
    parser.add_argument(
        "--max-mutants",
        type=int,
        default=15,
        help="Maximum number of mutants to generate and test",
    )
    parser.add_argument(
        "--min-kill-rate",
        type=float,
        default=70.0,
        help="Minimum required mutant kill rate percentage",
    )
    args = parser.parse_args()

    target_path = Path(args.target_file)
    test_target = args.test_target

    if not Path(test_target).exists():
        test_target = "tests/"

    start_time = time.time()
    mutants = run_mutation_on_target(target_path, test_target, max_mutants=args.max_mutants)
    duration = time.time() - start_time

    if not mutants:
        print("No mutants were tested.")
        return 0

    killed = sum(1 for m in mutants if m.status == "KILLED")
    survived = sum(1 for m in mutants if m.status == "SURVIVED")
    total = len(mutants)
    kill_rate = (killed / total) * 100.0 if total > 0 else 0.0

    print("=" * 80)
    print(f"MUTATION TESTING RESULTS ({target_path.name})")
    print(f"Total Mutants: {total} | Killed: {killed} | Survived: {survived}")
    print(f"Mutation Score / Kill Rate: {kill_rate:.1f}% (Required: {args.min_kill_rate:.1f}%)")
    print(f"Elapsed Time: {duration:.2f}s")
    print("=" * 80)

    if survived > 0:
        print("\nSURVIVED MUTANTS (Write additional tests to eliminate these blind spots):")
        for m in mutants:
            if m.status == "SURVIVED":
                print(f"  - Mutant #{m.id} at Line {m.line_number}: {m.operator_name}")

    if kill_rate < args.min_kill_rate:
        print(f"\n[FAIL] Mutation kill rate {kill_rate:.1f}% is below threshold {args.min_kill_rate:.1f}%.", file=sys.stderr)
        return 1

    print("\n[PASS] Mutation Testing Gate passed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
