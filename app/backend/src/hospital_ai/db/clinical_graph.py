from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, ForeignKeyConstraint, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from hospital_ai.db.models import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), nullable=False)


class GraphEntity(TimestampMixin, Base):
    __tablename__ = "graph_entities"
    __table_args__ = (
        UniqueConstraint("patient_id", "entity_type", "normalized_label", name="uq_graph_entity_identity"),
        UniqueConstraint("patient_id", "id", name="uq_graph_entity_patient_id"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_label: Mapped[str] = mapped_column(String(255), nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class GraphMention(Base):
    __tablename__ = "graph_mentions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["patient_id", "entity_id"],
            ["graph_entities.patient_id", "graph_entities.id"],
            name="fk_graph_mention_entity_patient",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    generation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_index_generations.id"), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    revision_set_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_revision_sets.id"), nullable=False)
    page_revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_page_revisions.id"), nullable=False)
    chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_chunks.id"), nullable=False)
    independent_source_identity: Mapped[str] = mapped_column(String(128), nullable=False)


class GraphRelationAssertion(TimestampMixin, Base):
    __tablename__ = "graph_relation_assertions"
    __table_args__ = (
        UniqueConstraint(
            "patient_id",
            "subject_entity_id",
            "object_entity_id",
            "relation_type",
            "normalized_value",
            name="uq_graph_relation_assertion",
        ),
        UniqueConstraint("patient_id", "id", name="uq_graph_assertion_patient_id"),
        ForeignKeyConstraint(
            ["patient_id", "subject_entity_id"],
            ["graph_entities.patient_id", "graph_entities.id"],
            name="fk_graph_assertion_subject_patient",
        ),
        ForeignKeyConstraint(
            ["patient_id", "object_entity_id"],
            ["graph_entities.patient_id", "graph_entities.id"],
            name="fk_graph_assertion_object_patient",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    subject_entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    object_entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    relation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(255), nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class GraphRelationEvidence(Base):
    __tablename__ = "graph_relation_evidence"
    __table_args__ = (
        ForeignKeyConstraint(
            ["patient_id", "assertion_id"],
            ["graph_relation_assertions.patient_id", "graph_relation_assertions.id"],
            name="fk_graph_evidence_assertion_patient",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    assertion_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    generation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_index_generations.id"), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    revision_set_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_revision_sets.id"), nullable=False)
    page_revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_page_revisions.id"), nullable=False)
    chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_chunks.id"), nullable=False)
    independent_source_identity: Mapped[str] = mapped_column(String(128), nullable=False)


class LegacyGraphEntity(TimestampMixin, Base):
    __tablename__ = "legacy_graph_entities"
    __table_args__ = (
        Index("ix_graph_entities_name", "name"),
        Index("ix_graph_entities_entity_type", "entity_type"),
        Index("ix_graph_entities_source_chunk_id", "source_chunk_id"),
        Index("ix_graph_entities_source_document_id", "source_document_id"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    source_chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_chunks.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False, default=1.0)


class LegacyGraphRelation(TimestampMixin, Base):
    __tablename__ = "legacy_graph_relations"
    __table_args__ = (
        Index("ix_graph_relations_source_entity_id", "source_entity_id"),
        Index("ix_graph_relations_target_entity_id", "target_entity_id"),
        Index("ix_graph_relations_relation_type", "relation_type"),
        Index("ix_graph_relations_source_chunk_id", "source_chunk_id"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("legacy_graph_entities.id"), nullable=False)
    target_entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("legacy_graph_entities.id"), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    source_chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_chunks.id"), nullable=False)
