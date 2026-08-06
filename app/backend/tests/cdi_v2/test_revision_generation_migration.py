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


def test_cdi_v2_revision_has_one_forward_parent() -> None:
    module = load_revision("cdi_v2_0001_add_revision_generation_schema.py")
    assert module.revision == "cdi_v2_0001"
    assert module.down_revision == "5a950640275c"


def test_cdi_v2_migration_contains_atomic_authority_schema() -> None:
    text = migration_text("cdi_v2_0001_add_revision_generation_schema.py")
    for fragment in (
        "document_uploads",
        "document_page_revisions",
        "document_revision_sets",
        "document_index_generations",
        "approved_revision_set_id",
        "active_index_generation_id",
        "idempotency_records",
    ):
        assert fragment in text
    assert "tenant_id" not in text


def test_cdi_v2_migration_retains_legacy_data(tmp_path: Path) -> None:
    import os
    import sqlite3
    import uuid

    from alembic.config import Config

    from alembic import command

    db_path = tmp_path / "legacy.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    # We must patch the environment before running Alembic
    # since env.py loads settings which reads HOSPITAL_AI_DATABASE_URL
    os.environ["HOSPITAL_AI_DATABASE_URL"] = db_url

    from hospital_ai.core.config import get_settings
    get_settings.cache_clear()

    try:
        cfg = Config("alembic.ini")
        command.upgrade(cfg, "5a950640275c")

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        user_id = str(uuid.uuid4()).replace("-", "")
        patient_id = str(uuid.uuid4()).replace("-", "")
        doc_id = str(uuid.uuid4()).replace("-", "")
        chunk_id = str(uuid.uuid4()).replace("-", "")
        query_id = str(uuid.uuid4()).replace("-", "")
        graph_ent_id = str(uuid.uuid4()).replace("-", "")

        page_id = str(uuid.uuid4()).replace("-", "")

        cur.execute("INSERT INTO users (id, email, full_name, role) VALUES (?, 'a@b.c', 'A B', 'admin')", (user_id,))
        cur.execute("INSERT INTO patients (id, full_name, mrn) VALUES (?, 'A B', 'MRN1')", (patient_id,))
        cur.execute(
            "INSERT INTO documents (id, patient_id, title, status, uploaded_by, document_type, storage_uri, mime_type) VALUES (?, ?, 'Doc 1', 'uploaded', ?, 'note', 'local://a', 'text/plain')",
            (doc_id, patient_id, user_id)
        )
        cur.execute("INSERT INTO document_pages (id, document_id, page_number, ocr_text) VALUES (?, ?, 1, 'text')", (page_id, doc_id))
        cur.execute(
            "INSERT INTO document_chunks (id, document_id, page_id, patient_id, chunk_index, content) VALUES (?, ?, ?, ?, 0, 'some text')",
            (chunk_id, doc_id, page_id, patient_id)
        )
        cur.execute("INSERT INTO ai_queries (id, patient_id, user_id, question, status) VALUES (?, ?, ?, 'q', 'completed')", (query_id, patient_id, user_id))
        cur.execute("INSERT INTO graph_entities (id, name, entity_type, source_chunk_id, source_document_id) VALUES (?, 'E1', 'type', ?, ?)", (graph_ent_id, chunk_id, doc_id))
        
        conn.commit()
        conn.close()

        command.upgrade(cfg, "head")

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("SELECT retention_state FROM documents WHERE id = ?", (doc_id,))
        assert cur.fetchone()[0] == "active"

        cur.execute("SELECT validation_mode FROM ai_queries WHERE id = ?", (query_id,))
        assert cur.fetchone()[0] is None

        cur.execute("SELECT last_emitted_sequence FROM ai_queries WHERE id = ?", (query_id,))
        assert cur.fetchone()[0] == 0

        cur.execute("SELECT id FROM document_chunks WHERE id = ?", (chunk_id,))
        assert cur.fetchone()[0] == chunk_id

        cur.execute("SELECT id FROM legacy_graph_entities WHERE id = ?", (graph_ent_id,))
        assert cur.fetchone()[0] == graph_ent_id

        conn.close()
    finally:
        os.environ.pop("HOSPITAL_AI_DATABASE_URL", None)
        get_settings.cache_clear()


