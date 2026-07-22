import pytest

from scripts.evaluate_rag import load_certification_dataset


def test_legacy_golden_dataset_is_rejected_for_certification() -> None:
    with pytest.raises(ValueError, match="legacy golden_dataset.json"):
        load_certification_dataset("data/golden_dataset.json")
