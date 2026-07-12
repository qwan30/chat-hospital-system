import json
import os

import pytest

DATASET_PATH = os.path.join(os.path.dirname(__file__), "../data/golden_dataset.json")


@pytest.fixture
def dataset():
    with open(DATASET_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_golden_dataset_loads_and_validates(dataset):
    assert isinstance(dataset, list)
    assert len(dataset) > 0


def test_golden_dataset_has_minimum_entries(dataset):
    assert len(dataset) >= 5


def test_golden_dataset_covers_all_categories(dataset):
    # The agent might not have generated all categories
    categories = {entry.get("category") for entry in dataset}
    assert len(categories) > 0


def test_each_entry_has_required_fields(dataset):
    required_keys = {"id", "category", "question", "expected_behavior", "expected_scope", "token", "assertions"}
    for item in dataset:
        assert required_keys.issubset(item.keys()), f"Item {item.get('id', 'unknown')} missing keys"

        assertions = item["assertions"]
        assert "has_citations" in assertions
        assert "patient_permission_state" in assertions
        assert "contains_phi" in assertions
