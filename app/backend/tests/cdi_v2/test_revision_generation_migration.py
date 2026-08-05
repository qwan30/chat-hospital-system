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
