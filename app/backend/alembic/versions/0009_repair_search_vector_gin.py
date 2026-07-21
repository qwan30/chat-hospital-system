"""repair PostgreSQL full-text search vector

Revision ID: 0009_repair_search_vector_gin
Revises: cfb28845ca63
Create Date: 2026-07-21
"""

from alembic import op


revision = "0009_repair_search_vector_gin"
down_revision = "cfb28845ca63"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create a real, maintained tsvector column only on PostgreSQL."""
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'document_chunks' AND column_name = 'search_vector'
          ) THEN
            ALTER TABLE document_chunks ADD COLUMN search_vector tsvector;
          ELSIF (SELECT udt_name FROM information_schema.columns
                 WHERE table_name = 'document_chunks' AND column_name = 'search_vector') <> 'tsvector' THEN
            ALTER TABLE document_chunks ALTER COLUMN search_vector TYPE tsvector
              USING to_tsvector('english', coalesce(content, ''));
          END IF;
        END $$;
        """
    )
    op.execute(
        "UPDATE document_chunks "
        "SET search_vector = to_tsvector('english', coalesce(content, '')) "
        "WHERE search_vector IS NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_search_vector ON document_chunks USING gin (search_vector)"
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION document_chunks_search_vector_update()
        RETURNS trigger AS $$
        BEGIN
          NEW.search_vector := to_tsvector('english', coalesce(NEW.content, ''));
          RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute("DROP TRIGGER IF EXISTS trg_document_chunks_search_vector ON document_chunks")
    op.execute(
        "CREATE TRIGGER trg_document_chunks_search_vector BEFORE INSERT OR UPDATE OF content "
        "ON document_chunks FOR EACH ROW EXECUTE FUNCTION document_chunks_search_vector_update()"
    )


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute("DROP TRIGGER IF EXISTS trg_document_chunks_search_vector ON document_chunks")
    op.execute("DROP FUNCTION IF EXISTS document_chunks_search_vector_update()")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_search_vector")
    # Restore the parent migration's portable placeholder type.
    op.execute("ALTER TABLE document_chunks ALTER COLUMN search_vector TYPE text USING search_vector::text")
