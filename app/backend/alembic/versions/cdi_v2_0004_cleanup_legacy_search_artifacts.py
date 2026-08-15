"""remove legacy search and constraint artifacts left by the CDI v2 model contract

Revision ID: cdi_v2_0004
Revises: 704142b14459
Create Date: 2026-08-08
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "cdi_v2_0004"
down_revision: Union[str, None] = "704142b14459"
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


def _drop_constraint_if_present(table_name: str, constraint_name: str, constraint_type: str) -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table_name):
        return
    if constraint_name not in _names(inspector, table_name, constraint_type):
        return

    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_constraint(constraint_name, type_=constraint_type)
    else:
        op.drop_constraint(constraint_name, table_name=table_name, type_=constraint_type)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    dialect = bind.dialect.name

    if inspector.has_table("document_chunks"):
        indexes = _names(inspector, "document_chunks", "index")
        if "document_chunks_embedding_hnsw" in indexes:
            op.drop_index("document_chunks_embedding_hnsw", table_name="document_chunks")
        if "ix_document_chunks_search_vector" in indexes:
            op.drop_index("ix_document_chunks_search_vector", table_name="document_chunks")

        if dialect == "postgresql":
            op.execute("DROP TRIGGER IF EXISTS trg_document_chunks_search_vector ON document_chunks")
            op.execute("DROP FUNCTION IF EXISTS document_chunks_search_vector_update()")
        elif dialect == "sqlite":
            op.execute("DROP TRIGGER IF EXISTS trg_document_chunks_search_vector")

        columns = {column["name"] for column in inspector.get_columns("document_chunks")}
        if "search_vector" in columns:
            if dialect == "sqlite":
                with op.batch_alter_table("document_chunks") as batch_op:
                    batch_op.drop_column("search_vector")
            else:
                op.drop_column("document_chunks", "search_vector")

    _drop_constraint_if_present("system_settings", "system_settings_key_key", "unique")
    _drop_constraint_if_present("user_feedback", "ck_user_feedback_rating", "check")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    dialect = bind.dialect.name

    if inspector.has_table("document_chunks"):
        columns = {column["name"] for column in inspector.get_columns("document_chunks")}
        if "search_vector" not in columns:
            with op.batch_alter_table("document_chunks") as batch_op:
                batch_op.add_column(sa.Column("search_vector", sa.Text(), nullable=True))
            if dialect == "postgresql":
                op.execute(
                    "ALTER TABLE document_chunks ALTER COLUMN search_vector TYPE tsvector USING search_vector::tsvector"
                )

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
        if dialect == "postgresql" and "document_chunks_embedding_hnsw" not in indexes:
            op.execute(
                "CREATE INDEX document_chunks_embedding_hnsw ON document_chunks "
                "USING hnsw (embedding vector_cosine_ops)"
            )

    if inspector.has_table("system_settings"):
        unique_constraints = _names(inspector, "system_settings", "unique")
        if "system_settings_key_key" not in unique_constraints:
            if dialect == "sqlite":
                with op.batch_alter_table("system_settings") as batch_op:
                    batch_op.create_unique_constraint("system_settings_key_key", ["key"])
            else:
                op.create_unique_constraint("system_settings_key_key", "system_settings", ["key"])

    if inspector.has_table("user_feedback"):
        checks = _names(inspector, "user_feedback", "check")
        if "ck_user_feedback_rating" not in checks:
            if dialect == "sqlite":
                with op.batch_alter_table("user_feedback") as batch_op:
                    batch_op.create_check_constraint("ck_user_feedback_rating", "rating >= -1 AND rating <= 1")
            else:
                op.create_check_constraint(
                    "ck_user_feedback_rating",
                    "user_feedback",
                    "rating >= -1 AND rating <= 1",
                )
