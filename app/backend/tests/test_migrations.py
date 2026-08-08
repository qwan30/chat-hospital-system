from __future__ import annotations

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


def test_document_processing_events_are_only_added_by_forward_migration():
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    previous_head = (versions_dir / "0009_repair_search_vector_gin.py").read_text(encoding="utf-8")
    processing_events_migration = (versions_dir / "0010_add_document_processing_events.py").read_text(encoding="utf-8")

    assert "document_processing_events" not in previous_head
    assert "document_processing_events" in processing_events_migration
    assert 'down_revision = "0009_repair_search_vector_gin"' in processing_events_migration
    assert "uq_document_processing_event_sequence" in processing_events_migration
    assert 'revision = "0010_document_processing_events"' in processing_events_migration
