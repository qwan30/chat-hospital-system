import importlib.util
from pathlib import Path

import pytest


def test_initial_schema_requires_pgvector_python_package(monkeypatch):
    migration_path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0001_initial_schema.py"
    spec = importlib.util.spec_from_file_location("initial_schema_migration", migration_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    monkeypatch.setattr(module, "Vector", None)

    with pytest.raises(RuntimeError, match="pgvector"):
        module._require_pgvector()


def test_document_index_metadata_is_only_added_by_forward_migration():
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    initial_schema = (versions_dir / "0001_initial_schema.py").read_text(encoding="utf-8")
    index_metadata_migration = (versions_dir / "0002_add_document_index_generation.py").read_text(encoding="utf-8")

    assert '"index_generation"' not in initial_schema
    assert '"indexed_source_sha256"' not in initial_schema
    assert '"index_generation"' in index_metadata_migration
    assert '"indexed_source_sha256"' in index_metadata_migration


def test_chat_thread_contract_is_only_added_by_forward_migration():
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    initial_schema = (versions_dir / "0001_initial_schema.py").read_text(encoding="utf-8")
    chat_threads_migration = (versions_dir / "0003_add_chat_threads.py").read_text(encoding="utf-8")

    assert '"chat_threads"' not in initial_schema
    assert '"chat_thread_participants"' not in initial_schema
    assert '"chat_messages"' not in initial_schema
    assert '"chat_threads"' in chat_threads_migration
    assert '"chat_thread_participants"' in chat_threads_migration
    assert '"chat_messages"' in chat_threads_migration
    assert "ck_chat_threads_patient_scope" in chat_threads_migration
    assert "ck_chat_messages_patient_permission_state" in chat_threads_migration
