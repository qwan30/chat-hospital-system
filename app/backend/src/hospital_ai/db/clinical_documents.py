import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from hospital_ai.db.models import Base, TimestampMixin

DOCUMENT_UPLOAD_STATES = frozenset(
    {"pending_upload", "uploaded_unverified", "quarantined", "verified", "finalized", "rejected"}
)
PAGE_REVISION_STATES = frozenset(
    {"machine_draft", "human_draft", "approved", "rejected", "superseded"}
)
REVISION_SET_STATES = frozenset({"submitted", "approved", "rejected", "superseded"})
GENERATION_STATES = frozenset({"building", "active", "failed", "superseded"})
ALIGNMENT_STATES = frozenset({"aligned", "partially_aligned", "stale"})


class DocumentUpload(TimestampMixin, Base):
    __tablename__ = "document_uploads"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    object_key: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    expected_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    byte_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    actor_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    def apply_verification(self, decision: Any) -> None:
        self.state = decision.state
        self.quarantine_result = getattr(decision, "quarantine_result", "clean")


class DocumentExtractionRun(Base):
    __tablename__ = "document_extraction_runs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    engine_family: Mapped[str] = mapped_column(String(64), nullable=False)
    engine_model: Mapped[str] = mapped_column(String(64), nullable=False)
    engine_revision: Mapped[str] = mapped_column(String(64), nullable=False)
    engine_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    peak_rss_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)


class DocumentPageRevision(Base):
    __tablename__ = "document_page_revisions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_revision_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("document_page_revisions.id"), nullable=True)
    extraction_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("document_extraction_runs.id"), nullable=True)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    revision_type: Mapped[str] = mapped_column(String(32), nullable=False)
    raw_text_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    edit_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class DocumentDraftHead(TimestampMixin, Base):
    __tablename__ = "document_draft_heads"
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), primary_key=True)
    selected_pages: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    lock_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    updated_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)


class DocumentRevisionSet(Base):
    __tablename__ = "document_revision_sets"
    __table_args__ = (
        CheckConstraint(
            "status in ('submitted','approved','rejected','superseded')",
            name="ck_document_revision_sets_status",
        ),
        UniqueConstraint("document_id", "revision_number", name="uq_document_revision_set_number"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DocumentRevisionPage(Base):
    __tablename__ = "document_revision_pages"
    revision_set_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_revision_sets.id"), primary_key=True)
    page_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    page_revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_page_revisions.id"), nullable=False, index=True)


class DocumentRevisionEvent(Base):
    __tablename__ = "document_revision_events"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    actor_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    next_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    changed_page_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


class DocumentIndexGeneration(Base):
    __tablename__ = "document_index_generations"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    revision_set_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_revision_sets.id"), nullable=False, index=True
    )
    retry_of_generation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_index_generations.id"), nullable=True
    )
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="building")
    revision_set_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    generation_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_code: Mapped[str | None] = mapped_column(String(64))
    failure_detail: Mapped[str | None] = mapped_column(Text)


class GenerationStageResult(Base):
    __tablename__ = "generation_stage_results"
    __table_args__ = (
        UniqueConstraint("generation_id", "stage", name="uq_generation_stage_result"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    generation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_index_generations.id"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)


class OcrBlock(Base):
    __tablename__ = "ocr_blocks"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    page_revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_page_revisions.id"), nullable=False, index=True)
    text_start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    text_end_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    polygon: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    reading_order: Mapped[int] = mapped_column(Integer, nullable=False)
    alignment_status: Mapped[str] = mapped_column(String(32), nullable=False)


class OcrLine(Base):
    __tablename__ = "ocr_lines"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    block_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ocr_blocks.id"), nullable=False, index=True)
    page_revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_page_revisions.id"), nullable=False, index=True)
    text_start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    text_end_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    polygon: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    reading_order: Mapped[int] = mapped_column(Integer, nullable=False)
    alignment_status: Mapped[str] = mapped_column(String(32), nullable=False)


class OcrSpan(Base):
    __tablename__ = "ocr_spans"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    line_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ocr_lines.id"), nullable=False, index=True)
    page_revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_page_revisions.id"), nullable=False, index=True)
    text_start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    text_end_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    polygon: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    reading_order: Mapped[int] = mapped_column(Integer, nullable=False)
    alignment_status: Mapped[str] = mapped_column(String(32), nullable=False)
    normalized_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_engine_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint("actor_user_id", "scope", "key_hash", name="uq_idempotency_record"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(64), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class ClaimValidationResult(Base):
    __tablename__ = "claim_validation_results"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    validation_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    is_supported: Mapped[bool] = mapped_column(Boolean, nullable=False)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


class ClinicalTimelineEvent(Base):
    __tablename__ = "clinical_timeline_events"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    clinical_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_evidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    confidence: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    reviewer_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    conflict_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    supersession_lineage: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
