"""restore CDI v2 model-owned schema objects

Revision ID: cdi_v2_0006
Revises: cdi_v2_0005
Create Date: 2026-08-09

The cleanup migration removed search and constraint objects that are still
declared by the current SQLAlchemy models.  Restore them in a forward
migration so both fresh databases and upgraded databases converge on the
same schema without rewriting historical migrations.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "cdi_v2_0006"
down_revision: Union[str, None] = "cdi_v2_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _names(inspector: sa.Inspector, table_name: str, kind: str) -> set[str]:
    if kind == "index":
        return {item["name"] for item in inspector.get_indexes(table_name) if item.get("name")}
    if kind == "unique":
        return {item["name"] for item in inspector.get_unique_constraints(table_name) if item.get("name")}
    if kind == "check":
        return {item["name"] for item in inspector.get_check_constraints(table_name) if item.get("name")}
    raise ValueError(f"unsupported inspector kind: {kind}")


def _restore_search_schema(bind: sa.Connection, inspector: sa.Inspector) -> None:
    if not inspector.has_table("document_chunks"):
        return

    dialect = bind.dialect.name
    columns = {column["name"]: column for column in inspector.get_columns("document_chunks")}
    if "search_vector" not in columns:
        search_type = postgresql.TSVECTOR() if dialect == "postgresql" else sa.Text()
        op.add_column("document_chunks", sa.Column("search_vector", search_type, nullable=True))
    elif dialect == "postgresql" and "tsvector" not in str(columns["search_vector"]["type"]).lower():
        op.execute("ALTER TABLE document_chunks ALTER COLUMN search_vector TYPE tsvector USING search_vector::tsvector")

    indexes = _names(inspector, "document_chunks", "index")
    if "ix_document_chunks_search_vector" not in indexes:
        if dialect == "postgresql":
            op.create_index(
                "ix_document_chunks_search_vector",
                "document_chunks",
                ["search_vector"],
                postgresql_using="gin",
            )
        else:
            op.create_index("ix_document_chunks_search_vector", "document_chunks", ["search_vector"])

    if "document_chunks_embedding_hnsw" not in indexes:
        if dialect == "postgresql":
            op.create_index(
                "document_chunks_embedding_hnsw",
                "document_chunks",
                ["embedding"],
                postgresql_using="hnsw",
                postgresql_ops={"embedding": "vector_cosine_ops"},
            )
        else:
            op.create_index("document_chunks_embedding_hnsw", "document_chunks", ["embedding"])


def _restore_entity_timestamps(bind: sa.Connection, inspector: sa.Inspector) -> None:
    if not inspector.has_table("legacy_graph_entities"):
        return

    columns = {column["name"] for column in inspector.get_columns("legacy_graph_entities")}
    for name in ("created_at", "updated_at"):
        if name not in columns:
            op.add_column(
                "legacy_graph_entities",
                sa.Column(name, sa.DateTime(timezone=True), nullable=True),
            )

    op.execute(
        "UPDATE legacy_graph_entities "
        "SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP), "
        "updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)"
    )
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("legacy_graph_entities") as batch_op:
            batch_op.alter_column("created_at", existing_type=sa.DateTime(timezone=True), nullable=False)
            batch_op.alter_column("updated_at", existing_type=sa.DateTime(timezone=True), nullable=False)
    else:
        op.alter_column(
            "legacy_graph_entities",
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
        )
        op.alter_column(
            "legacy_graph_entities",
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
        )


def _restore_relation_timestamp_types(bind: sa.Connection, inspector: sa.Inspector) -> None:
    if bind.dialect.name != "postgresql" or not inspector.has_table("legacy_graph_relations"):
        return

    columns = {column["name"] for column in inspector.get_columns("legacy_graph_relations")}
    for name in ("created_at", "updated_at"):
        if name in columns:
            op.alter_column(
                "legacy_graph_relations",
                name,
                existing_type=sa.DateTime(timezone=False),
                type_=sa.DateTime(timezone=True),
                existing_nullable=False,
            )


def _restore_constraints(bind: sa.Connection, inspector: sa.Inspector) -> None:
    dialect = bind.dialect.name
    if inspector.has_table("system_settings") and "system_settings_key_key" not in _names(
        inspector, "system_settings", "unique"
    ):
        if dialect == "sqlite":
            with op.batch_alter_table("system_settings") as batch_op:
                batch_op.create_unique_constraint("system_settings_key_key", ["key"])
        else:
            op.create_unique_constraint("system_settings_key_key", "system_settings", ["key"])

    if inspector.has_table("user_feedback") and "ck_user_feedback_rating" not in _names(
        inspector, "user_feedback", "check"
    ):
        expression = "rating >= -1 AND rating <= 1"
        if dialect == "sqlite":
            with op.batch_alter_table("user_feedback") as batch_op:
                batch_op.create_check_constraint("ck_user_feedback_rating", expression)
        else:
            op.create_check_constraint("ck_user_feedback_rating", "user_feedback", expression)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    _restore_search_schema(bind, inspector)
    _restore_entity_timestamps(bind, inspector)
    _restore_relation_timestamp_types(bind, inspector)
    _restore_constraints(bind, inspector)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    dialect = bind.dialect.name

    if inspector.has_table("document_chunks"):
        indexes = _names(inspector, "document_chunks", "index")
        for name in ("document_chunks_embedding_hnsw", "ix_document_chunks_search_vector"):
            if name in indexes:
                op.drop_index(name, table_name="document_chunks")
        if "search_vector" in {column["name"] for column in inspector.get_columns("document_chunks")}:
            if dialect == "sqlite":
                with op.batch_alter_table("document_chunks") as batch_op:
                    batch_op.drop_column("search_vector")
            else:
                op.drop_column("document_chunks", "search_vector")

    if inspector.has_table("legacy_graph_entities"):
        columns = {column["name"] for column in inspector.get_columns("legacy_graph_entities")}
        names = [name for name in ("created_at", "updated_at") if name in columns]
        if names:
            if dialect == "sqlite":
                with op.batch_alter_table("legacy_graph_entities") as batch_op:
                    for name in names:
                        batch_op.drop_column(name)
            else:
                for name in names:
                    op.drop_column("legacy_graph_entities", name)

    if dialect == "postgresql" and inspector.has_table("legacy_graph_relations"):
        columns = {column["name"] for column in inspector.get_columns("legacy_graph_relations")}
        for name in ("created_at", "updated_at"):
            if name in columns:
                op.alter_column(
                    "legacy_graph_relations",
                    name,
                    existing_type=sa.DateTime(timezone=True),
                    type_=sa.DateTime(timezone=False),
                    existing_nullable=False,
                )

    if inspector.has_table("system_settings") and "system_settings_key_key" in _names(
        inspector, "system_settings", "unique"
    ):
        if dialect == "sqlite":
            with op.batch_alter_table("system_settings") as batch_op:
                batch_op.drop_constraint("system_settings_key_key", type_="unique")
        else:
            op.drop_constraint("system_settings_key_key", "system_settings", type_="unique")

    if inspector.has_table("user_feedback") and "ck_user_feedback_rating" in _names(
        inspector, "user_feedback", "check"
    ):
        if dialect == "sqlite":
            with op.batch_alter_table("user_feedback") as batch_op:
                batch_op.drop_constraint("ck_user_feedback_rating", type_="check")
        else:
            op.drop_constraint("ck_user_feedback_rating", "user_feedback", type_="check")
