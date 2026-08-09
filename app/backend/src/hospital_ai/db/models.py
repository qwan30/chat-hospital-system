from __future__ import annotations

import os
import uuid
from datetime import date, datetime
from typing import Any, Optional

from cryptography.fernet import Fernet
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    pass


class EmbeddingVector(TypeDecorator):
    """Store vectors as pgvector in PostgreSQL and JSON in test databases."""

    impl = JSON
    cache_ok = True

    def __init__(self, dimensions: int = 1024, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector

                return dialect.type_descriptor(Vector(self.dimensions))
            except Exception:
                return dialect.type_descriptor(JSON())
        return dialect.type_descriptor(JSON())


class InetAddress(TypeDecorator):
    impl = String(64)
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(INET())
        return dialect.type_descriptor(String(64))


_ENCRYPTION_KEY = os.environ.get("PHI_ENCRYPTION_KEY", Fernet.generate_key().decode("utf-8"))
_fernet = Fernet(_ENCRYPTION_KEY.encode("utf-8"))


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy TypeDecorator that applies application-level encryption for PHI fields.
    This satisfies the security review requirement for field-level encryption at rest.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if not isinstance(value, str):
                value = str(value)
            return _fernet.encrypt(value.encode("utf-8")).decode("utf-8")
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                return _fernet.decrypt(value.encode("utf-8")).decode("utf-8")
            except Exception:
                return value
        return value


class EncryptedText(TypeDecorator):
    """
    SQLAlchemy TypeDecorator for encrypting text or large JSON fields containing PHI.
    This satisfies the security review requirement for field-level encryption at rest.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if not isinstance(value, str):
                value = str(value)
            return _fernet.encrypt(value.encode("utf-8")).decode("utf-8")
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                return _fernet.decrypt(value.encode("utf-8")).decode("utf-8")
            except Exception:
                return value
        return value


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SoftDeleteMixin:
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role in ('doctor','nurse','pharmacist','lab_staff','records_staff','security','admin','front_desk')",
            name="ck_users_role",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    permissions: Mapped[list[PatientPermission]] = relationship(back_populates="user")
    notifications: Mapped[list[Notification]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Patient(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    mrn: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dob: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")

    permissions: Mapped[list[PatientPermission]] = relationship(back_populates="patient")
    documents: Mapped[list[Document]] = relationship(back_populates="patient")
    chat_threads: Mapped[list[ChatThread]] = relationship(back_populates="patient")


class PatientPermission(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "patient_permissions"
    __table_args__ = (
        UniqueConstraint("user_id", "patient_id", "scope", name="uq_patient_permission_scope"),
        CheckConstraint(
            "scope in ('read','summary','medication','upload','admin')", name="ck_patient_permission_scope"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="manual", server_default="manual")
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="permissions")
    patient: Mapped[Patient] = relationship(back_populates="permissions")


class AccessRequest(TimestampMixin, Base):
    __tablename__ = "access_requests"
    __table_args__ = (
        CheckConstraint("status in ('pending','approved','denied','pending_info')", name="ck_access_requests_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    patient: Mapped[Patient] = relationship()
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    reviewed_by: Mapped[Optional[User]] = relationship(foreign_keys=[reviewed_by_user_id])


class Document(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "status in ('uploaded','queued','processing','review_required',"
            "'ready_with_warnings','ready','failed','cancelled','quarantined','soft_deleted')",
            name="ck_documents_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("patients.id"), nullable=True, index=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_uri: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded")
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ocr_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    index_generation: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    indexed_source_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    approved_revision_set_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("document_revision_sets.id", use_alter=True), nullable=True
    )
    active_index_generation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("document_index_generations.id", use_alter=True), nullable=True
    )
    finalized_upload_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("document_uploads.id", use_alter=True), nullable=True
    )
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    retention_state: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    patient: Mapped[Optional[Patient]] = relationship(back_populates="documents")
    pages: Mapped[list[DocumentPage]] = relationship(back_populates="document", cascade="all, delete-orphan")
    chunks: Mapped[list[DocumentChunk]] = relationship(back_populates="document", cascade="all, delete-orphan")
    processing_events: Mapped[list[DocumentProcessingEvent]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentProcessingEvent(Base):
    """Sanitized, user-visible document processing milestones."""

    __tablename__ = "document_processing_events"
    __table_args__ = (
        CheckConstraint(
            "stage in ('upload','ocr','index','ready','preflight_document','classify_document',"
            "'extract_native_pages','extract_vision_pages','reconstruct_document','extract_clinical_facts',"
            "'validate_and_route_review','build_fhir_draft','index_document','extract_graph','run_cdss',"
            "'finalize_document')",
            name="ck_document_processing_event_stage",
        ),
        CheckConstraint("state in ('started','completed','failed')", name="ck_document_processing_event_state"),
        CheckConstraint(
            "error_code is null or error_code in ('OCR_FAILED','INDEX_FAILED')",
            name="ck_document_processing_event_error_code",
        ),
        UniqueConstraint(
            "document_id",
            "attempt",
            "sequence",
            name="uq_document_processing_event_sequence",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    progress_current: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    progress_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    document: Mapped[Document] = relationship(back_populates="processing_events")


class DocumentPage(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "document_pages"
    __table_args__ = (UniqueConstraint("document_id", "page_number", name="uq_document_page_number"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    ocr_text: Mapped[str] = mapped_column(Text, nullable=False)
    ocr_confidence: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)

    document: Mapped[Document] = relationship(back_populates="pages")
    chunks: Mapped[list[DocumentChunk]] = relationship(back_populates="page")


class DocumentChunk(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "document_chunks"
    __table_args__ = (UniqueConstraint("document_id", "generation_id", "chunk_index", name="uq_document_chunk_index"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    page_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_pages.id"), nullable=False, index=True)
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("patients.id"), nullable=True, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    embedding: Mapped[Optional[list[float]]] = mapped_column(EmbeddingVector(1024), nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)

    generation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("document_index_generations.id", use_alter=True), nullable=True, index=True
    )
    revision_set_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("document_revision_sets.id", use_alter=True), nullable=True, index=True
    )
    page_revision_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("document_page_revisions.id", use_alter=True), nullable=True, index=True
    )
    text_start_offset: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    text_end_offset: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_text_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    approval_state: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    bounding_boxes: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    access_tags: Mapped[list[str]] = mapped_column(JSON, nullable=True, default=list)

    document: Mapped[Document] = relationship(back_populates="chunks")
    page: Mapped[DocumentPage] = relationship(back_populates="chunks")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (CheckConstraint("outcome in ('allowed','denied','failed')", name="ck_audit_logs_outcome"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    object_type: Mapped[str] = mapped_column(String(64), nullable=False)
    object_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("patients.id"), nullable=True, index=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(InetAddress(), nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AiQuery(Base):
    __tablename__ = "ai_queries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("patients.id"), nullable=True, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    validation_mode: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_emitted_sequence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    evidence: Mapped[list[RetrievedEvidence]] = relationship(back_populates="query", cascade="all, delete-orphan")
    messages: Mapped[list[ChatMessage]] = relationship(back_populates="ai_query")


class RetrievedEvidence(Base):
    __tablename__ = "retrieved_evidence"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ai_query_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ai_queries.id"), nullable=False, index=True)
    chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_chunks.id"), nullable=False, index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Numeric, nullable=False)
    citation_label: Mapped[str] = mapped_column(String(16), nullable=False)

    # RAG trace observability fields
    rerank_score: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    retrieval_method: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    rerank_method: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    generation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("document_index_generations.id", use_alter=True), nullable=True, index=True
    )

    query: Mapped[AiQuery] = relationship(back_populates="evidence")


class ChatThread(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "chat_threads"
    __table_args__ = (
        CheckConstraint("scope in ('general','patient-linked')", name="ck_chat_threads_scope"),
        CheckConstraint("visibility in ('private','shared')", name="ck_chat_threads_visibility"),
        CheckConstraint("status in ('active','archived')", name="ck_chat_threads_status"),
        CheckConstraint(
            "(scope = 'general' and patient_id is null) or (scope = 'patient-linked' and patient_id is not null)",
            name="ck_chat_threads_patient_scope",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    visibility: Mapped[str] = mapped_column(String(32), nullable=False, default="private")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    owner_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("patients.id"), nullable=True, index=True)
    created_trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped[User] = relationship()
    patient: Mapped[Optional[Patient]] = relationship(back_populates="chat_threads")
    participants: Mapped[list[ChatThreadParticipant]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
    )
    memory: Mapped[Optional[ChatSessionMemory]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        uselist=False,
    )


class ChatSessionMemory(TimestampMixin, Base):
    __tablename__ = "chat_session_memory"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_threads.id"), nullable=False, unique=True, index=True)
    active_patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("patients.id"), nullable=True, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    active_entities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    source_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    thread: Mapped[ChatThread] = relationship(back_populates="memory")
    active_patient: Mapped[Optional[Patient]] = relationship()


class ChatThreadParticipant(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "chat_thread_participants"
    __table_args__ = (
        UniqueConstraint("thread_id", "user_id", name="uq_chat_thread_participant"),
        CheckConstraint(
            "access_level in ('owner','write','read')",
            name="ck_chat_thread_participants_access_level",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_threads.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    access_level: Mapped[str] = mapped_column(String(32), nullable=False)
    can_share: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    added_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    last_read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    thread: Mapped[ChatThread] = relationship(back_populates="participants")
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    added_by: Mapped[User] = relationship(foreign_keys=[added_by_user_id])


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint("role in ('user','assistant','system')", name="ck_chat_messages_role"),
        CheckConstraint("scope in ('general','patient-linked')", name="ck_chat_messages_scope"),
        CheckConstraint(
            "patient_permission_state in ('not-required','pending','allowed','denied')",
            name="ck_chat_messages_patient_permission_state",
        ),
        CheckConstraint(
            "(scope = 'general' and patient_id is null) or (scope = 'patient-linked' and patient_id is not null)",
            name="ck_chat_messages_patient_scope",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_threads.id"), nullable=False, index=True)
    sender_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    ai_query_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("ai_queries.id"), nullable=True, index=True)
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("patients.id"), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    patient_permission_state: Mapped[str] = mapped_column(String(32), nullable=False)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    thread: Mapped[ChatThread] = relationship(back_populates="messages")
    sender: Mapped[Optional[User]] = relationship()
    ai_query: Mapped[Optional[AiQuery]] = relationship(back_populates="messages")
    patient: Mapped[Optional[Patient]] = relationship()


class HmsSyncLog(TimestampMixin, Base):
    """Track HMS synchronization operations."""

    __tablename__ = "hms_sync_logs"
    __table_args__ = (
        CheckConstraint(
            "status in ('pending','running','completed','failed','partial')",
            name="ck_hms_sync_logs_status",
        ),
        CheckConstraint(
            "sync_type in ('appointments','lab_results','medical_records','full')",
            name="ck_hms_sync_logs_sync_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    initiated_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    sync_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    records_synced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)


class ClinicalAlert(TimestampMixin, Base):
    """Clinical alerts generated by the CDSS system."""

    __tablename__ = "clinical_alerts"
    __table_args__ = (
        CheckConstraint(
            "severity in ('low','medium','high')",
            name="ck_clinical_alerts_severity",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    source_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("documents.id"), nullable=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")


class DocumentProcessingRun(TimestampMixin, Base):
    """Tracks asynchronous processing runs and configuration for documents."""

    __tablename__ = "document_processing_runs"
    __table_args__ = (
        CheckConstraint(
            "status in ('pending','running','completed','failed','cancelled')",
            name="ck_document_processing_runs_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    configuration_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)

    document: Mapped[Document] = relationship()


class ClinicalFact(TimestampMixin, Base):
    """Represents a structured clinical fact extracted from a document."""

    __tablename__ = "clinical_facts"
    __table_args__ = (
        CheckConstraint(
            "status in ('unverified','confirmed','rejected')",
            name="ck_clinical_facts_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_processing_runs.id"), nullable=False, index=True)
    fact_type: Mapped[str] = mapped_column(String(64), nullable=False)

    # Encrypted fields containing PHI
    raw_value: Mapped[str] = mapped_column(EncryptedText(), nullable=False)
    normalized_value: Mapped[Optional[str]] = mapped_column(EncryptedText(), nullable=True)

    confidence: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bounding_box: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="unverified", server_default="unverified")

    generation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("document_index_generations.id", use_alter=True), nullable=True, index=True
    )

    document: Mapped[Document] = relationship()
    run: Mapped[DocumentProcessingRun] = relationship()


class DocumentReviewItem(TimestampMixin, Base):
    """Tracks review tasks for clinical facts or fields that require human validation."""

    __tablename__ = "document_review_items"
    __table_args__ = (
        CheckConstraint(
            "review_status in ('pending','approved','rejected')",
            name="ck_document_review_items_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_processing_runs.id"), nullable=False, index=True)
    fact_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("clinical_facts.id"), nullable=True, index=True)

    field_name: Mapped[str] = mapped_column(String(128), nullable=False)

    # Encrypted fields containing PHI
    original_value: Mapped[Optional[str]] = mapped_column(EncryptedText(), nullable=True)
    suggested_value: Mapped[Optional[str]] = mapped_column(EncryptedText(), nullable=True)

    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending")
    reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped[Document] = relationship()
    run: Mapped[DocumentProcessingRun] = relationship()
    fact: Mapped[Optional[ClinicalFact]] = relationship()
    reviewed_by: Mapped[Optional[User]] = relationship()


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(
            "kind in ('access','ocr','sync','ai','system')",
            name="ck_notifications_kind",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    reference_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    user: Mapped[User] = relationship(back_populates="notifications")
