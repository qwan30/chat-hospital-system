"""add_graph_provenance_schema

Revision ID: cdi_v2_0002
Revises: cdi_v2_0001
Create Date: 2026-08-05 10:00:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cdi_v2_0002"
down_revision: Union[str, None] = "cdi_v2_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename legacy tables
    op.rename_table("graph_entities", "legacy_graph_entities")
    op.rename_table("graph_relations", "legacy_graph_relations")

    # Create graph_entities
    op.create_table(
        "graph_entities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("normalized_label", sa.String(length=255), nullable=False),
        sa.Column("lifecycle_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("patient_id", "entity_type", "normalized_label", name="uq_graph_entity_identity"),
        sa.UniqueConstraint("patient_id", "id", name="uq_graph_entity_patient_id"),
    )
    op.create_index(op.f("ix_graph_entities_patient_id"), "graph_entities", ["patient_id"], unique=False)

    # Create graph_mentions
    op.create_table(
        "graph_mentions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("generation_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("revision_set_id", sa.Uuid(), nullable=False),
        sa.Column("page_revision_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_id", sa.Uuid(), nullable=False),
        sa.Column("independent_source_identity", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(
            ["chunk_id"],
            ["document_chunks.id"],
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.ForeignKeyConstraint(
            ["patient_id", "entity_id"],
            ["graph_entities.patient_id", "graph_entities.id"],
            name="fk_graph_mention_entity_patient",
        ),
        sa.ForeignKeyConstraint(
            ["generation_id"],
            ["document_index_generations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["page_revision_id"],
            ["document_page_revisions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
        ),
        sa.ForeignKeyConstraint(
            ["revision_set_id"],
            ["document_revision_sets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_graph_mentions_patient_id"), "graph_mentions", ["patient_id"], unique=False)

    # Create graph_relation_assertions
    op.create_table(
        "graph_relation_assertions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("subject_entity_id", sa.Uuid(), nullable=False),
        sa.Column("object_entity_id", sa.Uuid(), nullable=False),
        sa.Column("relation_type", sa.String(length=64), nullable=False),
        sa.Column("normalized_value", sa.String(length=255), nullable=False),
        sa.Column("lifecycle_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "patient_id",
            "subject_entity_id",
            "object_entity_id",
            "relation_type",
            "normalized_value",
            name="uq_graph_relation_assertion",
        ),  # noqa: E501
        sa.UniqueConstraint("patient_id", "id", name="uq_graph_assertion_patient_id"),
        sa.ForeignKeyConstraint(
            ["patient_id", "subject_entity_id"],
            ["graph_entities.patient_id", "graph_entities.id"],
            name="fk_graph_assertion_subject_patient",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id", "object_entity_id"],
            ["graph_entities.patient_id", "graph_entities.id"],
            name="fk_graph_assertion_object_patient",
        ),
    )
    op.create_index(
        op.f("ix_graph_relation_assertions_patient_id"), "graph_relation_assertions", ["patient_id"], unique=False
    )  # noqa: E501

    # Create graph_relation_evidence
    op.create_table(
        "graph_relation_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("assertion_id", sa.Uuid(), nullable=False),
        sa.Column("generation_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("revision_set_id", sa.Uuid(), nullable=False),
        sa.Column("page_revision_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_id", sa.Uuid(), nullable=False),
        sa.Column("independent_source_identity", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(
            ["patient_id", "assertion_id"],
            ["graph_relation_assertions.patient_id", "graph_relation_assertions.id"],
            name="fk_graph_evidence_assertion_patient",
        ),
        sa.ForeignKeyConstraint(
            ["chunk_id"],
            ["document_chunks.id"],
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.ForeignKeyConstraint(
            ["generation_id"],
            ["document_index_generations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["page_revision_id"],
            ["document_page_revisions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
        ),
        sa.ForeignKeyConstraint(
            ["revision_set_id"],
            ["document_revision_sets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_graph_relation_evidence_patient_id"), "graph_relation_evidence", ["patient_id"], unique=False
    )  # noqa: E501


def downgrade() -> None:
    op.drop_index(op.f("ix_graph_relation_evidence_patient_id"), table_name="graph_relation_evidence")
    op.drop_table("graph_relation_evidence")
    op.drop_index(op.f("ix_graph_relation_assertions_patient_id"), table_name="graph_relation_assertions")
    op.drop_table("graph_relation_assertions")
    op.drop_index(op.f("ix_graph_mentions_patient_id"), table_name="graph_mentions")
    op.drop_table("graph_mentions")
    op.drop_index(op.f("ix_graph_entities_patient_id"), table_name="graph_entities")
    op.drop_table("graph_entities")

    op.rename_table("legacy_graph_relations", "graph_relations")
    op.rename_table("legacy_graph_entities", "graph_entities")
