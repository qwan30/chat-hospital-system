"""add shared chat thread contract

Revision ID: 0003_add_chat_threads
Revises: 0002_add_doc_idx_gen
Create Date: 2026-04-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_add_chat_threads"
down_revision = "0002_add_doc_idx_gen"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_threads",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("visibility", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=True),
        sa.Column("created_trace_id", sa.String(length=64), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("scope in ('general','patient-linked')", name="ck_chat_threads_scope"),
        sa.CheckConstraint("visibility in ('private','shared')", name="ck_chat_threads_visibility"),
        sa.CheckConstraint("status in ('active','archived')", name="ck_chat_threads_status"),
        sa.CheckConstraint(
            "(scope = 'general' and patient_id is null) or "
            "(scope = 'patient-linked' and patient_id is not null)",
            name="ck_chat_threads_patient_scope",
        ),
    )
    op.create_index("ix_chat_threads_owner_user_id", "chat_threads", ["owner_user_id"])
    op.create_index("ix_chat_threads_patient_id", "chat_threads", ["patient_id"])

    op.create_table(
        "chat_thread_participants",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("thread_id", sa.Uuid(), sa.ForeignKey("chat_threads.id"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("access_level", sa.String(length=32), nullable=False),
        sa.Column("can_share", sa.Boolean(), nullable=False),
        sa.Column("added_by_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_trace_id", sa.String(length=64), nullable=False),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "access_level in ('owner','write','read')",
            name="ck_chat_thread_participants_access_level",
        ),
        sa.UniqueConstraint("thread_id", "user_id", name="uq_chat_thread_participant"),
    )
    op.create_index("ix_chat_thread_participants_thread_id", "chat_thread_participants", ["thread_id"])
    op.create_index("ix_chat_thread_participants_user_id", "chat_thread_participants", ["user_id"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("thread_id", sa.Uuid(), sa.ForeignKey("chat_threads.id"), nullable=False),
        sa.Column("sender_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("ai_query_id", sa.Uuid(), sa.ForeignKey("ai_queries.id"), nullable=True),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("patient_permission_state", sa.String(length=32), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("role in ('user','assistant','system')", name="ck_chat_messages_role"),
        sa.CheckConstraint("scope in ('general','patient-linked')", name="ck_chat_messages_scope"),
        sa.CheckConstraint(
            "patient_permission_state in ('not-required','pending','allowed','denied')",
            name="ck_chat_messages_patient_permission_state",
        ),
        sa.CheckConstraint(
            "(scope = 'general' and patient_id is null) or "
            "(scope = 'patient-linked' and patient_id is not null)",
            name="ck_chat_messages_patient_scope",
        ),
    )
    op.create_index("ix_chat_messages_thread_id", "chat_messages", ["thread_id"])
    op.create_index("ix_chat_messages_sender_user_id", "chat_messages", ["sender_user_id"])
    op.create_index("ix_chat_messages_ai_query_id", "chat_messages", ["ai_query_id"])
    op.create_index("ix_chat_messages_patient_id", "chat_messages", ["patient_id"])


def downgrade() -> None:
    op.drop_index("ix_chat_messages_patient_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_ai_query_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_sender_user_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_thread_id", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("ix_chat_thread_participants_user_id", table_name="chat_thread_participants")
    op.drop_index("ix_chat_thread_participants_thread_id", table_name="chat_thread_participants")
    op.drop_table("chat_thread_participants")
    op.drop_index("ix_chat_threads_patient_id", table_name="chat_threads")
    op.drop_index("ix_chat_threads_owner_user_id", table_name="chat_threads")
    op.drop_table("chat_threads")
