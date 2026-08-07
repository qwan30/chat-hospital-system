import json
from pathlib import Path
from typing import Any


def load_measured_artifacts(jsonl_path: Path) -> list[dict[str, Any]]:
    """Read concrete JSON lines outputs."""
    results = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results


def check_measured_thresholds(artifacts: list[dict[str, Any]]) -> bool:
    """Checks thresholds (precision/recall > 0.85)."""
    answer_cases = [
        a for a in artifacts if "precision_at_5" in a.get("metrics", {}) and "recall_at_5" in a.get("metrics", {})
    ]
    if not answer_cases:
        return False

    avg_precision = sum(a["metrics"]["precision_at_5"] for a in answer_cases) / len(answer_cases)
    avg_recall = sum(a["metrics"]["recall_at_5"] for a in answer_cases) / len(answer_cases)

    return avg_precision > 0.85 and avg_recall > 0.85
