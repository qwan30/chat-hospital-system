"""Migration tests for cdi_v2_0003_add_validated_stream_state."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def get_migration_path(filename: str) -> Path:
    return Path(__file__).resolve().parents[2] / "alembic" / "versions" / filename


def load_revision(filename: str):
    path = get_migration_path(filename)
    spec = importlib.util.spec_from_file_location("migration_module", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def migration_text(filename: str) -> str:
    return get_migration_path(filename).read_text(encoding="utf-8")


def test_validated_stream_migration_follows_graph_schema() -> None:
    module = load_revision("cdi_v2_0003_add_validated_stream_state.py")
    assert module.revision == "cdi_v2_0003"
    assert module.down_revision == "cdi_v2_0002"


def test_validated_stream_migration_adds_required_columns() -> None:
    text = migration_text("cdi_v2_0003_add_validated_stream_state.py")
    for fragment in ("validation_mode", "last_emitted_sequence"):
        assert fragment in text, f"Missing column reference: {fragment}"


def test_validated_stream_migration_allows_interrupted_status() -> None:
    text = migration_text("cdi_v2_0003_add_validated_stream_state.py")
    assert "interrupted" in text
