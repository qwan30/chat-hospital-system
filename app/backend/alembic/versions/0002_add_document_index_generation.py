"""add document index metadata

Revision ID: 0002_add_doc_idx_gen
Revises: 0001_initial_schema
Create Date: 2026-04-27
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_add_doc_idx_gen"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("index_generation", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "documents",
        sa.Column("indexed_source_sha256", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("documents", "indexed_source_sha256")
    op.drop_column("documents", "index_generation")
