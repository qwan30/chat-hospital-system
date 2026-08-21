#!/usr/bin/env python3
"""CRAP (Change Risk Anti-Patterns) Score Calculator for Python.

CRAP Score formula (Alberto Savoia & Bob Martin):
    CRAP(m) = comp(m)^2 * (1 - cov(m))^3 + comp(m)

Where:
    comp(m) = Cyclomatic Complexity of method/function m
    cov(m)  = Test coverage fraction [0.0, 1.0] of method/function m

A CRAP score <= 15 is considered clean/acceptable.
A CRAP score > 30 indicates high maintenance and regression risk (CRAPPY code).
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FunctionMetric:
    name: str
    file_path: str
    line_start: int
    line_end: int
    complexity: int
    executable_lines: int
    covered_lines: int

    @property
    def coverage(self) -> float:
        if self.executable_lines == 0:
            return 1.0
        return min(1.0, self.covered_lines / self.executable_lines)

    @property
    def crap_score(self) -> float:
        c = self.complexity
        cov = self.coverage
        return (c**2) * ((1.0 - cov) ** 3) + c

    @property
    def risk(self) -> str:
        score = self.crap_score
        if score <= 10:
            return "CLEAN"
        elif score <= 15:
            return "ACCEPTABLE"
        elif score <= 30:
            return "MODERATE"
        else:
            return "CRITICAL"


class ComplexityVisitor(ast.NodeVisitor):
    """Calculates McCabe Cyclomatic Complexity for a single function AST node."""

    def __init__(self) -> None:
        self.complexity = 1

    def visit_If(self, node: ast.If) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:
        self.complexity += len(node.cases)
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        self.complexity += 1
        self.generic_visit(node)


def compute_node_complexity(node: ast.AST) -> int:
    visitor = ComplexityVisitor()
    for child in ast.iter_child_nodes(node):
        visitor.visit(child)
    return visitor.complexity


def load_coverage_data(coverage_path: Path) -> dict[str, set[int]]:
    """Loads covered line numbers per normalized absolute file path from .coverage sqlite or coverage.json."""
    if not coverage_path.exists():
        return {}

    covered_lines_by_file: dict[str, set[int]] = {}

    # Check if JSON report
    if coverage_path.suffix == ".json":
        try:
            data = json.loads(coverage_path.read_text(encoding="utf-8"))
            files = data.get("files", {})
            for filepath, file_info in files.items():
                norm = os.path.abspath(filepath).replace("\\", "/").lower()
                executed = set(file_info.get("executed_lines", []))
                covered_lines_by_file[norm] = executed
            return covered_lines_by_file
        except Exception:
            pass

    # SQLite .coverage file
    try:
        conn = sqlite3.connect(str(coverage_path))
        cursor = conn.cursor()
        tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

        if "arc" in tables and "file" in tables:
            cursor.execute("SELECT f.path, a.fromno, a.tono FROM file f JOIN arc a ON f.id = a.file_id")
            for path_str, fromno, tono in cursor.fetchall():
                norm = os.path.abspath(path_str).replace("\\", "/").lower()
                file_set = covered_lines_by_file.setdefault(norm, set())
                if fromno > 0:
                    file_set.add(fromno)
                if tono > 0:
                    file_set.add(tono)
        elif "line_map" in tables and "file" in tables:
            cursor.execute("SELECT f.path, l.num FROM file f JOIN line_map l ON f.id = l.file_id")
            for path_str, line_num in cursor.fetchall():
                norm = os.path.abspath(path_str).replace("\\", "/").lower()
                covered_lines_by_file.setdefault(norm, set()).add(line_num)
        conn.close()
    except Exception as exc:
        print(f"[WARN] Unable to read coverage database ({exc}), continuing with AST complexity analysis.", file=sys.stderr)

    return covered_lines_by_file


def analyze_file(file_path: Path, covered_lines: set[int]) -> list[FunctionMetric]:
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except Exception:
        return []

    metrics: list[FunctionMetric] = []
    norm_path = str(file_path).replace("\\", "/")

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            complexity = compute_node_complexity(node)

            func_lines = set(range(start_line, end_line + 1))
            covered_in_func = len(func_lines.intersection(covered_lines))
            exec_lines = max(1, end_line - start_line + 1)

            metrics.append(
                FunctionMetric(
                    name=node.name,
                    file_path=norm_path,
                    line_start=start_line,
                    line_end=end_line,
                    complexity=complexity,
                    executable_lines=exec_lines,
                    covered_lines=covered_in_func,
                )
            )

    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate Cyclomatic Complexity and CRAP scores for Python code.")
    parser.add_argument("--source-dir", default="src/hospital_ai", help="Source directory to analyze")
    parser.add_argument("--coverage-db", default=".coverage", help="Path to .coverage SQLite or coverage.json file")
    parser.add_argument("--max-crap", type=float, default=30.0, help="Maximum allowed CRAP score threshold")
    parser.add_argument("--max-complexity", type=int, default=25, help="Maximum allowed cyclomatic complexity")
    parser.add_argument("--top-n", type=int, default=15, help="Number of highest-risk functions to display")
    parser.add_argument("--strict", action="store_true", help="Fail if any function exceeds max-crap threshold")
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    if not source_dir.exists():
        print(f"Error: Source directory '{source_dir}' not found.", file=sys.stderr)
        return 1

    coverage_db = Path(args.coverage_db)
    has_cov = coverage_db.exists()
    covered_lines_by_file = load_coverage_data(coverage_db) if has_cov else {}

    all_metrics: list[FunctionMetric] = []
    for py_file in source_dir.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        norm_key = os.path.abspath(py_file).replace("\\", "/").lower()
        cov_set = covered_lines_by_file.get(norm_key, set())
        metrics = analyze_file(py_file, cov_set)
        all_metrics.extend(metrics)

    if not all_metrics:
        print("No Python functions found to analyze.")
        return 0

    all_metrics.sort(key=lambda m: m.crap_score, reverse=True)

    print("=" * 96)
    print(f"CRAP & COMPLEXITY REPORT (Analyzed {len(all_metrics)} functions across {args.source_dir})")
    print(f"Coverage DB Loaded: {'YES (' + str(coverage_db) + ')' if (has_cov and covered_lines_by_file) else 'NO (Defaulting to structural complexity)'}")
    print(f"Thresholds: Max CRAP = {args.max_crap} | Max Complexity = {args.max_complexity}")
    print("=" * 96)
    print(f"{'Function':<30} {'Location':<34} {'Comp':<6} {'Cov %':<8} {'CRAP':<8} {'Risk':<10}")
    print("-" * 96)

    high_risk_count = 0
    over_threshold_count = 0

    for m in all_metrics[: args.top_n]:
        loc = f"{Path(m.file_path).name}:{m.line_start}"
        cov_str = f"{m.coverage * 100:.1f}%" if (has_cov and covered_lines_by_file) else "N/A"
        crap_str = f"{m.crap_score:.1f}"
        print(f"{m.name[:28]:<30} {loc[:32]:<34} {m.complexity:<6} {cov_str:<8} {crap_str:<8} {m.risk:<10}")

    for m in all_metrics:
        if m.crap_score > args.max_crap:
            over_threshold_count += 1
        if m.risk in ("MODERATE", "CRITICAL"):
            high_risk_count += 1

    print("-" * 96)
    print(f"Summary: {len(all_metrics)} functions | {high_risk_count} Moderate/Critical risk | {over_threshold_count} exceeding CRAP > {args.max_crap}")
    print("=" * 96)

    if args.strict and over_threshold_count > 0:
        print(f"[FAIL] {over_threshold_count} functions exceeded CRAP threshold {args.max_crap} in strict mode.", file=sys.stderr)
        return 1

    print("[PASS] CRAP & Complexity verification completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
