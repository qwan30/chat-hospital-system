import importlib.util
from pathlib import Path

import pytest


def test_initial_schema_requires_pgvector_python_package(monkeypatch):
    migration_path = (
        Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0001_initial_schema.py"
    )
    spec = importlib.util.spec_from_file_location("initial_schema_migration", migration_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    monkeypatch.setattr(module, "Vector", None)

    with pytest.raises(RuntimeError, match="pgvector"):
        module._embedding_type()
