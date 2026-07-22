from pathlib import Path


def test_legacy_self_scored_evaluator_is_removed() -> None:
    evaluator = Path(__file__).parent.parent / "scripts" / "evaluate_rag.py"

    assert not evaluator.exists()
