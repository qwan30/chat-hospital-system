"""add graph entities, metric events, user feedback, and phase 3 trace columns

Revision ID: 0006_add_phase4_tables
Revises: 0005_add_system_settings
Create Date: 2026-04-29
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_add_phase4_tables"
down_revision = "0005_add_system_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Graph RAG tables ─────────────────────────────────────────────
    op.create_table(
        "graph_entities",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("entity_type", sa.String(64), nullable=False, index=True),
        sa.Column("source_chunk_id", sa.Uuid(), sa.ForeignKey("document_chunks.id"), nullable=False, index=True),
        sa.Column("source_document_id", sa.Uuid(), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "graph_relations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("source_entity_id", sa.Uuid(), sa.ForeignKey("graph_entities.id"), nullable=False, index=True),
        sa.Column("target_entity_id", sa.Uuid(), sa.ForeignKey("graph_entities.id"), nullable=False, index=True),
        sa.Column("relation_type", sa.String(64), nullable=False, index=True),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("source_chunk_id", sa.Uuid(), sa.ForeignKey("document_chunks.id"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # ── Phase 3 trace columns on retrieved_evidence ──────────────────
    # These may already exist from Phase 3 model changes; add if missing.
    with op.batch_alter_table("retrieved_evidence") as batch_op:
        batch_op.add_column(sa.Column("rerank_score", sa.Numeric(), nullable=True))
        batch_op.add_column(sa.Column("retrieval_method", sa.String(32), nullable=True))
        batch_op.add_column(sa.Column("rerank_method", sa.String(32), nullable=True))

    # ── BM25 search_vector column on document_chunks ─────────────────
    # TSVECTOR column for PostgreSQL full-text search.
    # SQLite tests skip this (no tsvector type).
    try:
        op.add_column(
            "document_chunks",
            sa.Column("search_vector", sa.Text(), nullable=True),
        )
        # On PostgreSQL, create a GIN index for fast BM25 queries.
        # The column type is 'tsvector' natively; Alembic uses Text as placeholder.
        op.execute(
            "ALTER TABLE document_chunks "
            "ALTER COLUMN search_vector TYPE tsvector USING search_vector::tsvector"
        )
        op.create_index(
            "ix_document_chunks_search_vector",
            "document_chunks",
            ["search_vector"],
            postgresql_using="gin",
        )
    except Exception:
        pass  # Non-PostgreSQL or column already exists

    # ── Metric events table ──────────────────────────────────────────
    op.create_table(
        "metric_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("query_id", sa.Uuid(), sa.ForeignKey("ai_queries.id"), nullable=True, index=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("task_type", sa.String(64), nullable=False),
        sa.Column("baseline_manual_time_sec", sa.Integer(), nullable=True),
        sa.Column("actual_ai_time_sec", sa.Integer(), nullable=True),
        sa.Column("estimated_time_saved_sec", sa.Integer(), nullable=True),
        sa.Column("estimated_cost_saved", sa.Numeric(12, 2), nullable=True),
        sa.Column("documents_retrieved", sa.Integer(), nullable=True),
        sa.Column("citations_count", sa.Integer(), nullable=True),
        sa.Column("query_latency_ms", sa.Integer(), nullable=True),
        sa.Column("retrieval_latency_ms", sa.Integer(), nullable=True),
        sa.Column("generation_latency_ms", sa.Integer(), nullable=True),
        sa.Column("shared_thread_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # ── User feedback table ──────────────────────────────────────────
    op.create_table(
        "user_feedback",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("query_id", sa.Uuid(), sa.ForeignKey("ai_queries.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("rating >= -1 AND rating <= 1", name="ck_user_feedback_rating"),
    )


def downgrade() -> None:
    op.drop_table("user_feedback")
    op.drop_table("metric_events")
    try:
        op.drop_index("ix_document_chunks_search_vector", table_name="document_chunks")
        op.drop_column("document_chunks", "search_vector")
    except Exception:
        pass
    with op.batch_alter_table("retrieved_evidence") as batch_op:
        batch_op.drop_column("rerank_method")
        batch_op.drop_column("retrieval_method")
        batch_op.drop_column("rerank_score")
    op.drop_table("graph_relations")
    op.drop_table("graph_entities")
