from pathlib import Path

import pytest

from scripts.evaluate_rag import load_certification_dataset


def test_legacy_self_scored_fixture_is_not_an_evaluation() -> None:
    path = Path(__file__).parent.parent / "data" / "golden_dataset.json"

    with pytest.raises(ValueError, match="not a certification input"):
        load_certification_dataset(path)
