"""Định nghĩa các mô hình cơ sở dữ liệu (ORM Models) với SQLAlchemy cho Hệ thống Trợ lý AI Bệnh viện.

Bao gồm các thực thể cốt lõi: Người dùng (User), Bệnh nhân (Patient), Phân quyền (PatientPermission),
Tài liệu (Document/Page/Chunk) cho RAG, Lịch sử trò chuyện (ChatThread/ChatMessage), và Nhật ký kiểm toán (AuditLog).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

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
    """Lớp cơ sở declarative cho toàn bộ các model SQLAlchemy trong hệ thống."""
    pass


class EmbeddingVector(TypeDecorator):
    """Store vectors as pgvector in PostgreSQL and JSON in test databases.
    Kiểu dữ liệu tùy chỉnh cho vector nhúng (embedding): dùng pgvector trên PostgreSQL
    và JSON khi chạy trên CSDL kiểm thử (SQLite/JSON).
    """

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
    """Kiểu dữ liệu địa chỉ IP: sử dụng kiểu INET trên PostgreSQL và String(64) cho các CSDL khác."""
    impl = String(64)
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(INET())
        return dialect.type_descriptor(String(64))


class TimestampMixin:
    """Mixin tự động thêm thời gian tạo (created_at) và cập nhật (updated_at) cho các bản ghi."""
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
    """Mixin hỗ trợ xóa mềm (soft delete) bằng trường deleted_at thay vì xóa vĩnh viễn khỏi CSDL."""
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class User(TimestampMixin, SoftDeleteMixin, Base):
    """Mô hình Người dùng (bác sĩ, điều dưỡng, dược sĩ, quản trị viên...) trong hệ thống."""
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role in ('doctor','nurse','pharmacist','lab_staff','records_staff','security','admin')",
            name="ck_users_role",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    permissions: Mapped[list[PatientPermission]] = relationship(back_populates="user")


class Patient(TimestampMixin, SoftDeleteMixin, Base):
    """Mô hình Bệnh nhân kèm thông tin hành chính cơ bản và mã hồ sơ y tế (MRN)."""
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    mrn: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")

    permissions: Mapped[list[PatientPermission]] = relationship(back_populates="patient")
    documents: Mapped[list[Document]] = relationship(back_populates="patient")
    chat_threads: Mapped[list[ChatThread]] = relationship(back_populates="patient")


class PatientPermission(TimestampMixin, SoftDeleteMixin, Base):
    """Mô hình quyền truy cập cụ thể của người dùng đối với một hồ sơ bệnh nhân theo phạm vi (scope)."""
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
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="permissions")
    patient: Mapped[Patient] = relationship(back_populates="permissions")


class AccessRequest(TimestampMixin, Base):
    """Mô hình Yêu cầu truy cập (khi người dùng xin quyền truy cập hồ sơ bệnh nhân
    kèm lý do giải trình justification).
    """
    __tablename__ = "access_requests"
    __table_args__ = (
        CheckConstraint("status in ('pending','approved','denied','pending_info')", name="ck_access_requests_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    patient: Mapped[Patient] = relationship()
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    reviewed_by: Mapped[User | None] = relationship(foreign_keys=[reviewed_by_user_id])


class Document(TimestampMixin, SoftDeleteMixin, Base):
    """Mô hình Tài liệu y tế gốc (PDF, DOCX, hình ảnh...) gắn với một bệnh nhân cụ thể."""
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "status in ('uploaded','ocr_processing','ocr_failed','ocr_completed','indexing',"
            "'index_failed','indexed','archived')",
            name="ck_documents_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_uri: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded")
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ocr_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    index_generation: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    indexed_source_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    patient: Mapped[Patient] = relationship(back_populates="documents")
    pages: Mapped[list[DocumentPage]] = relationship(back_populates="document", cascade="all, delete-orphan")
    chunks: Mapped[list[DocumentChunk]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentPage(TimestampMixin, SoftDeleteMixin, Base):
    """Mô hình Trang tài liệu chứa văn bản bóc tách từ OCR kèm độ tin cậy confidence."""
    __tablename__ = "document_pages"
    __table_args__ = (UniqueConstraint("document_id", "page_number", name="uq_document_page_number"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    ocr_text: Mapped[str] = mapped_column(Text, nullable=False)
    ocr_confidence: Mapped[float | None] = mapped_column(Numeric, nullable=True)

    document: Mapped[Document] = relationship(back_populates="pages")
    chunks: Mapped[list[DocumentChunk]] = relationship(back_populates="page")


class DocumentChunk(TimestampMixin, SoftDeleteMixin, Base):
    """Mô hình Đoạn văn bản (Chunk) của trang tài liệu, lưu trữ vector nhúng embedding cho tìm kiếm RAG."""
    __tablename__ = "document_chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    page_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_pages.id"), nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector(1024), nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)

    document: Mapped[Document] = relationship(back_populates="chunks")
    page: Mapped[DocumentPage] = relationship(back_populates="chunks")


class AuditLog(Base):
    """Mô hình Nhật ký kiểm toán (Audit Log) ghi nhận mọi hành động truy cập,
    thao tác và kết quả cho mục đích tuân thủ.
    """
    __tablename__ = "audit_logs"
    __table_args__ = (CheckConstraint("outcome in ('allowed','denied','failed')", name="ck_audit_logs_outcome"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    object_type: Mapped[str] = mapped_column(String(64), nullable=False)
    object_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("patients.id"), nullable=True, index=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(InetAddress(), nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AiQuery(Base):
    """Mô hình Lịch sử truy vấn AI (câu hỏi, câu trả lời, độ trễ và mô hình LLM sử dụng)."""
    __tablename__ = "ai_queries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("patients.id"), nullable=True, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    evidence: Mapped[list[RetrievedEvidence]] = relationship(back_populates="query", cascade="all, delete-orphan")
    messages: Mapped[list[ChatMessage]] = relationship(back_populates="ai_query")


class RetrievedEvidence(Base):
    """Mô hình Bằng chứng trích xuất (Evidence Chunk) liên kết giữa câu hỏi AI và đoạn văn bản đã tìm kiếm từ RAG."""
    __tablename__ = "retrieved_evidence"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ai_query_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ai_queries.id"), nullable=False, index=True)
    chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_chunks.id"), nullable=False, index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Numeric, nullable=False)
    citation_label: Mapped[str] = mapped_column(String(16), nullable=False)

    # RAG trace observability fields
    rerank_score: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    retrieval_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    rerank_method: Mapped[str | None] = mapped_column(String(32), nullable=True)

    query: Mapped[AiQuery] = relationship(back_populates="evidence")


class ChatThread(TimestampMixin, SoftDeleteMixin, Base):
    """Mô hình Cuộc trò chuyện (Thread), phân chia theo phạm vi chung (general)
    hoặc gắn với một bệnh nhân (patient-linked).
    """
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
    patient_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("patients.id"), nullable=True, index=True)
    created_trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped[User] = relationship()
    patient: Mapped[Patient | None] = relationship(back_populates="chat_threads")
    participants: Mapped[list[ChatThreadParticipant]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
    )
    memory: Mapped[ChatSessionMemory | None] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        uselist=False,
    )


class ChatSessionMemory(TimestampMixin, Base):
    """Mô hình Bộ nhớ tóm tắt hội thoại (Memory Summary) lưu trữ tóm tắt và thực thể đang hoạt động của thread."""
    __tablename__ = "chat_session_memory"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_threads.id"), nullable=False, unique=True, index=True)
    active_patient_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("patients.id"), nullable=True, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    active_entities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    source_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    thread: Mapped[ChatThread] = relationship(back_populates="memory")
    active_patient: Mapped[Patient | None] = relationship()


class ChatThreadParticipant(TimestampMixin, SoftDeleteMixin, Base):
    """Mô hình Thành viên tham gia cuộc trò chuyện (hỗ trợ tính năng hội chẩn chia sẻ thread giữa các bác sĩ)."""
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
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    thread: Mapped[ChatThread] = relationship(back_populates="participants")
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    added_by: Mapped[User] = relationship(foreign_keys=[added_by_user_id])


class ChatMessage(Base):
    """Mô hình Tin nhắn hội thoại (Message) kèm trích dẫn (citations) và trạng thái phân quyền truy cập PHI."""
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
    sender_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    ai_query_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ai_queries.id"), nullable=True, index=True)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("patients.id"), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    patient_permission_state: Mapped[str] = mapped_column(String(32), nullable=False)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    thread: Mapped[ChatThread] = relationship(back_populates="messages")
    sender: Mapped[User | None] = relationship()
    ai_query: Mapped[AiQuery | None] = relationship(back_populates="messages")
    patient: Mapped[Patient | None] = relationship()


class HmsSyncLog(TimestampMixin, Base):
    """Track HMS synchronization operations.
    Mô hình Nhật ký đồng bộ hóa với hệ thống quản lý bệnh viện (HMS), theo dõi lịch hẹn, kết quả xét nghiệm, bệnh án.
    """

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
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)


class ClinicalAlert(TimestampMixin, Base):
    """Clinical alerts generated by the CDSS system.
    Mô hình Cảnh báo lâm sàng (chống chỉ định, tương tác thuốc, nguy cơ nhiễm trùng...) sinh ra bởi hệ thống CDSS.
    """

    __tablename__ = "clinical_alerts"
    __table_args__ = (
        CheckConstraint(
            "severity in ('low','medium','high')",
            name="ck_clinical_alerts_severity",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
