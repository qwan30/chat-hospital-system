"""Promotion-gate tests for the CDI V2 Alembic chain and model contract."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND_ROOT = Path(__file__).resolve().parents[2]
VERSIONS_DIR = BACKEND_ROOT / "alembic" / "versions"
CDI_MIGRATION_PATTERN = re.compile(r"^cdi_v2_\d{4}_.*\.py$")
CDI_ORDINAL_PATTERN = re.compile(r"^cdi_v2_(\d{4})_.*\.py$")


def _assignment(module: ast.Module, name: str) -> object | None:
    for node in ast.walk(module):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            return ast.literal_eval(node.value) if node.value is not None else None
    return None


def _migration_headers() -> list[tuple[Path, str, str | None, object | None]]:
    headers: list[tuple[Path, str, str | None, object | None]] = []
    for path in sorted(VERSIONS_DIR.glob("*.py")):
        if not CDI_MIGRATION_PATTERN.match(path.name):
            continue
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        revision = _assignment(module, "revision")
        assert isinstance(revision, str), f"missing revision header: {path.name}"
        down_revision = _assignment(module, "down_revision")
        assert down_revision is None or isinstance(down_revision, str), f"invalid down_revision: {path.name}"
        headers.append((path, revision, down_revision, _assignment(module, "branch_labels")))
    return headers


def test_cdi_v2_has_one_head_and_all_declared_parents_are_resolvable() -> None:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    script = ScriptDirectory.from_config(config)

    assert script.get_heads() == ["cdi_v2_0006"]
    for path, revision, down_revision, branch_labels in _migration_headers():
        assert branch_labels is None, f"unexpected branch label in {path.name}"
        if down_revision is not None:
            assert script.get_revision(down_revision) is not None, (
                f"missing Alembic parent {down_revision!r} for {path.name}"
            )
        assert script.get_revision(revision) is not None


def test_cdi_v2_headers_are_unique_and_filename_ordinals_match() -> None:
    headers = _migration_headers()
    revisions = [revision for _, revision, _, _ in headers]

    assert len(revisions) == len(set(revisions)), "duplicate CDI V2 revision headers"
    for path, revision, _, _ in headers:
        filename_match = CDI_ORDINAL_PATTERN.match(path.name)
        revision_match = re.fullmatch(r"cdi_v2_(\d{4})", revision)
        if filename_match and revision_match:
            assert filename_match.group(1) == revision_match.group(1), (
                f"filename/header ordinal mismatch: {path.name} declares {revision}"
            )


def test_build_authorized_revision_state_was_renamed_without_changing_revision_id() -> None:
    renamed = VERSIONS_DIR / "cdi_v2_0005_add_build_authorized_revision_state.py"

    assert renamed.is_file()
    assert not (VERSIONS_DIR / "cdi_v2_0004_add_build_authorized_revision_state.py").exists()
    assert 'revision: str = "cdi_v2_0005"' in renamed.read_text(encoding="utf-8")
    assert 'down_revision: Union[str, None] = "cdi_v2_0004"' in renamed.read_text(encoding="utf-8")


def test_model_metadata_contains_cdi_v2_tables_and_search_shapes() -> None:
    from hospital_ai.db import clinical_documents, clinical_graph  # noqa: F401
    from hospital_ai.db.models import Base

    expected_tables = {
        "document_uploads",
        "document_revision_sets",
        "document_page_revisions",
        "document_index_generations",
        "graph_entities",
        "graph_mentions",
        "graph_relation_assertions",
        "graph_relation_evidence",
    }
    assert expected_tables.issubset(Base.metadata.tables)

    document_chunks = Base.metadata.tables["document_chunks"]
    assert {"embedding", "search_vector"}.issubset(set(document_chunks.c.keys()))
    assert {"document_chunks_embedding_hnsw", "ix_document_chunks_search_vector"}.issubset(
        {index.name for index in document_chunks.indexes}
    )
    assert "legacy_graph_relations" in Base.metadata.tables
