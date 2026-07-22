"""add durable document processing activity

Revision ID: 0010_document_processing_events
Revises: 0009_repair_search_vector_gin
Create Date: 2026-07-22
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_document_processing_events"
down_revision = "0009_repair_search_vector_gin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_processing_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.Uuid(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("progress_current", sa.Integer(), nullable=True),
        sa.Column("progress_total", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("stage in ('upload','ocr','index','ready')", name="ck_document_processing_event_stage"),
        sa.CheckConstraint("state in ('started','completed','failed')", name="ck_document_processing_event_state"),
        sa.CheckConstraint(
            "error_code is null or error_code in ('OCR_FAILED','INDEX_FAILED')",
            name="ck_document_processing_event_error_code",
        ),
        sa.UniqueConstraint("document_id", "attempt", "sequence", name="uq_document_processing_event_sequence"),
    )
    op.create_index("ix_document_processing_events_document_id", "document_processing_events", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_document_processing_events_document_id", table_name="document_processing_events")
    op.drop_table("document_processing_events")
