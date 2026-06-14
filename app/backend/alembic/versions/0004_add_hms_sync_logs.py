"""add hms_sync_logs table

Revision ID: 0004_add_hms_sync_logs
Revises: 0003_add_chat_threads
Create Date: 2026-04-29
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_add_hms_sync_logs"
down_revision = "0003_add_chat_threads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hms_sync_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("initiated_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("sync_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("records_synced", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint(
            "status in ('pending','running','completed','failed','partial')",
            name="ck_hms_sync_logs_status",
        ),
        sa.CheckConstraint(
            "sync_type in ('appointments','lab_results','medical_records','full')",
            name="ck_hms_sync_logs_sync_type",
        ),
    )
    op.create_index("ix_hms_sync_logs_patient_id", "hms_sync_logs", ["patient_id"])
    op.create_index("ix_hms_sync_logs_initiated_by", "hms_sync_logs", ["initiated_by"])


def downgrade() -> None:
    op.drop_index("ix_hms_sync_logs_initiated_by", table_name="hms_sync_logs")
    op.drop_index("ix_hms_sync_logs_patient_id", table_name="hms_sync_logs")
    op.drop_table("hms_sync_logs")
