from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings
from hospital_ai.db.clinical_documents import (
    DocumentDraftHead,
    DocumentExtractionRun,
    DocumentPageRevision,
    DocumentUpload,
    OcrBlock,
    OcrLine,
    OcrSpan,
)
from hospital_ai.db.models import Document, DocumentProcessingEvent
from hospital_ai.services.ocr import OcrService


class PageExtractionError(Exception):
    """Raised when page OCR extraction fails."""

    def __init__(self, message: str, error_code: str = "OCR_FAILED") -> None:
        super().__init__(message)
        self.error_code = error_code


async def require_finalized_document_for_extraction(
    session: AsyncSession, document_id: uuid.UUID
) -> Optional[Document]:
    document = await session.get(Document, document_id)
    if not document or not document.finalized_upload_id or document.storage_uri == "pending":
        return None
    upload = await session.get(DocumentUpload, document.finalized_upload_id)
    if not upload or upload.document_id != document.id or upload.state != "finalized":
        return None
    return document


class _ExtractionRuns:
    async def start(self, session: AsyncSession, document: Document, settings: Settings) -> DocumentExtractionRun:
        source_hash = (
            getattr(document, "content_sha256", None) or getattr(document, "indexed_source_sha256", None) or "none"
        )
        run = DocumentExtractionRun(
            document_id=document.id,
            source_sha256=source_hash,
            engine_family="paddle_printed",
            engine_model="v4",
            engine_revision="r1",
            started_at=datetime.now(UTC),
            status="processing",
        )
        session.add(run)
        await session.flush()
        return run

    async def fail_pagewise(
        self, session: AsyncSession, document: Document, run: DocumentExtractionRun, exc: Exception
    ) -> None:
        run.status = "failed"
        run.error_code = getattr(exc, "error_code", "OCR_FAILED")
        run.completed_at = datetime.now(UTC)
        document.status = "failed"


async def ocr_pipeline_extract(
    document: Document,
    run: DocumentExtractionRun,
    settings: Settings,
    expected_source_sha256: Optional[str] = None,
) -> list[Any]:
    from hospital_ai.workers import jobs

    storage = jobs.get_storage_service(settings)
    try:
        source_sha256 = storage.source_sha256(document.storage_uri)
    except (FileNotFoundError, OSError, ValueError, Exception) as exc:
        raise PageExtractionError(
            "Unable to verify the finalized source object.", error_code="MISSING_SOURCE_OBJECT"
        ) from exc
    if expected_source_sha256 and source_sha256 != expected_source_sha256:
        raise PageExtractionError(
            "Finalized source hash does not match upload evidence.", error_code="SOURCE_HASH_DRIFT"
        )
    document.indexed_source_sha256 = source_sha256
    run.source_sha256 = source_sha256

    try:
        ocr = OcrService()
        pages = ocr.extract_page_results(
            storage_uri=document.storage_uri,
            mime_type=document.mime_type,
            patient_id=str(document.patient_id),
            document_id=str(document.id),
            storage_service=storage,
        )
        return pages
    except Exception as exc:
        raise PageExtractionError(f"Extraction failed: {exc}") from exc


class _OcrPipeline:
    async def extract(
        self,
        document: Document,
        run: DocumentExtractionRun,
        settings: Settings,
        expected_source_sha256: Optional[str] = None,
    ) -> list[Any]:
        return await ocr_pipeline_extract(document, run, settings, expected_source_sha256)


class _RevisionIngest:
    async def persist_machine_drafts(
        self, session: AsyncSession, document: Document, run: DocumentExtractionRun, pages: list[Any]
    ) -> None:
        selected: dict[str, str] = {}
        for p in pages:
            sha256_val = hashlib.sha256(p.raw_text.encode("utf-8")).hexdigest()
            rev = DocumentPageRevision(
                document_id=document.id,
                page_number=p.page_number,
                extraction_run_id=run.id,
                revision_number=1,
                revision_type="machine_ocr",
                raw_text_snapshot=p.raw_text,
                corrected_text=p.raw_text,
                confidence=p.confidence,
                status="machine_draft",
                created_by_user_id=document.uploaded_by,
                content_sha256=sha256_val,
                version=1,
            )
            session.add(rev)
            await session.flush()
            selected[str(p.page_number)] = str(rev.id)

            spans = getattr(p, "spans", ())
            if spans:
                block = OcrBlock(
                    page_revision_id=rev.id,
                    text_start_offset=0,
                    text_end_offset=len(p.raw_text),
                    reading_order=1,
                    alignment_status="aligned",
                )
                session.add(block)
                await session.flush()

                line = OcrLine(
                    block_id=block.id,
                    page_revision_id=rev.id,
                    text_start_offset=0,
                    text_end_offset=len(p.raw_text),
                    reading_order=1,
                    alignment_status="aligned",
                )
                session.add(line)
                await session.flush()

                for span in spans:
                    span_row = OcrSpan(
                        line_id=line.id,
                        page_revision_id=rev.id,
                        text_start_offset=getattr(span, "start_offset", 0),
                        text_end_offset=getattr(span, "end_offset", len(p.raw_text)),
                        polygon={"coords": list(getattr(span, "polygon", []))},
                        confidence=getattr(span, "confidence", p.confidence),
                        reading_order=getattr(span, "reading_order", 1),
                        alignment_status="aligned",
                        normalized_text=getattr(span, "text", ""),
                        source_engine_metadata={
                            "family": getattr(span, "engine_family", "native"),
                            "model": getattr(span, "engine_model", "v4"),
                            "revision": getattr(span, "engine_revision", "r1"),
                        },
                    )
                    session.add(span_row)

        head = await session.get(DocumentDraftHead, document.id)
        if not head:
            head = DocumentDraftHead(
                document_id=document.id,
                selected_pages=selected,
                lock_version=1,
                updated_by_user_id=document.uploaded_by,
            )
            session.add(head)
        else:
            head.selected_pages = {**head.selected_pages, **selected}
            head.updated_by_user_id = document.uploaded_by


class _ProcessingEvents:
    async def complete_extraction(
        self, session: AsyncSession, document_id: uuid.UUID, run_id: uuid.UUID, count: int
    ) -> None:
        stages = ["preflight_document", "classify_document", "ocr"]
        for stage in stages:
            max_seq = await session.scalar(
                select(func.max(DocumentProcessingEvent.sequence)).where(
                    DocumentProcessingEvent.document_id == document_id,
                    DocumentProcessingEvent.attempt == 1,
                )
            )
            seq = int(max_seq or 0) + 1
            evt = DocumentProcessingEvent(
                document_id=document_id,
                attempt=1,
                sequence=seq,
                stage=stage,
                state="completed",
                progress_current=count,
                progress_total=count,
            )
            session.add(evt)
            await session.flush()


extraction_runs = _ExtractionRuns()
ocr_pipeline = _OcrPipeline()
revision_ingest = _RevisionIngest()
processing_events = _ProcessingEvents()


async def extract_document(session: AsyncSession, document_id: uuid.UUID, settings: Settings) -> None:
    document = await require_finalized_document_for_extraction(session, document_id)
    if not document:
        return
    upload = await session.get(DocumentUpload, document.finalized_upload_id)
    if not upload or upload.document_id != document.id or upload.state != "finalized":
        return
    run = await extraction_runs.start(session, document, settings)
    try:
        pages = await ocr_pipeline.extract(
            document,
            run,
            settings,
            expected_source_sha256=upload.expected_sha256,
        )
        await revision_ingest.persist_machine_drafts(session, document, run, pages)
        if pages:
            run.peak_rss_mb = max((int(getattr(p, "peak_rss_mb", 0)) for p in pages), default=0)
            run.latency_ms = sum(int(getattr(p, "latency_ms", 0)) for p in pages)
            for p in pages:
                spans = getattr(p, "spans", ())
                if spans:
                    first_span = spans[0]
                    if hasattr(first_span, "engine_family"):
                        run.engine_family = first_span.engine_family
                    if hasattr(first_span, "engine_model"):
                        run.engine_model = first_span.engine_model
                    if hasattr(first_span, "engine_revision"):
                        run.engine_revision = first_span.engine_revision
                    break

        document.status = "review_required"
        run.status = "completed"
        run.completed_at = datetime.now(UTC)
        await processing_events.complete_extraction(session, document.id, run.id, len(pages))
        await session.commit()
    except PageExtractionError as exc:
        await extraction_runs.fail_pagewise(session, document, run, exc)
        await session.commit()
