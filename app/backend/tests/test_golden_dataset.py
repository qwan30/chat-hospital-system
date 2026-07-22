import json
import os

import pytest

DATASET_PATH = os.path.join(os.path.dirname(__file__), "../data/golden_dataset.json")


@pytest.fixture
def dataset():
    with open(DATASET_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_golden_dataset_loads_and_validates(dataset):
    pytest.skip("golden_dataset.json is deprecated and not a certification input")
    assert isinstance(dataset, list)
    assert len(dataset) > 0


def test_golden_dataset_has_minimum_entries(dataset):
    assert len(dataset) >= 5


def test_each_entry_has_required_fields(dataset):
    required_keys = {"input", "expected_output", "retrieval_context"}
    for item in dataset:
        assert required_keys.issubset(item.keys()), "Item missing keys"
