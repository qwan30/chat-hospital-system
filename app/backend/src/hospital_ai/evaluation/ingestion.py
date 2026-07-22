"""Durable, idempotent accounting contracts for governed corpus ingestion."""

from __future__ import annotations

import re
import uuid
from collections import Counter
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.db.migrations import RECORDS_ID
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage
from hospital_ai.evaluation.models import CorpusFile, CorpusManifest

IngestionProcessor = Callable[[AsyncSession, Document], Awaitable[Optional[str]]]
_ATTEMPT_MARKER = re.compile(r"^(?P<code>[a-z][a-z0-9_]{0,63})__attempt_(?P<count>[1-9][0-9]*)$")
_SAFE_ERROR_CODES = {
    "derived_rows_incomplete",
    "document_missing",
    "embedding_count_mismatch",
    "index_failed",
    "invalid_metadata",
    "not_runtime_approved",
    "ocr_failed",
    "patient_missing",
    "processing_failed",
    "source_fingerprint_mismatch",
    "source_fingerprint_unknown",
    "source_unavailable",
    "stale_generation",
}


@dataclass(frozen=True)
class DerivedIds:
    page_ids: tuple[uuid.UUID, ...]
    chunk_ids: tuple[uuid.UUID, ...]


@dataclass(frozen=True)
class IngestFileResult:
    """One completely accounted corpus-file ingestion outcome."""

    path: str
    fingerprint: Optional[str]
    state: str
    document_id: uuid.UUID | None
    page_ids: tuple[uuid.UUID, ...]
    chunk_ids: tuple[uuid.UUID, ...]
    generation: int
    attempts: int
    error_code: str | None


@dataclass(frozen=True)
class IngestionRun:
    """Immutable results for one complete manifest ingestion attempt."""

    manifest: CorpusManifest
    results: tuple[IngestFileResult, ...]


@dataclass(frozen=True)
class IngestCertificationReport:
    """Accounting and cross-run idempotency differences."""

    manifest_file_count: int
    first_run_accounted_count: int
    second_run_accounted_count: int
    missing_files: tuple[str, ...]
    unexpected_files: tuple[str, ...]
    manifest_mismatches: tuple[str, ...]
    duplicate_documents: tuple[str, ...]
    duplicate_pages: tuple[str, ...]
    duplicate_chunks: tuple[str, ...]
    source_fingerprint_mismatches: tuple[str, ...]
    generation_drift: tuple[str, ...]
    attempt_drift: tuple[str, ...]
    failed_files: tuple[str, ...]

    @property
    def is_certified(self) -> bool:
        return not any(
            (
                self.missing_files,
                self.unexpected_files,
                self.manifest_mismatches,
                self.duplicate_documents,
                self.duplicate_pages,
                self.duplicate_chunks,
                self.source_fingerprint_mismatches,
                self.generation_drift,
                self.attempt_drift,
                self.failed_files,
            )
        )


@dataclass(frozen=True)
class _Preparation:
    document: Document | None
    start_generation: int
    attempts: int
    result: IngestFileResult | None = None


async def ingest_one(
    session: AsyncSession,
    manifest_file: CorpusFile,
    *,
    processor: IngestionProcessor,
    storage_uri: str | None = None,
    title: str | None = None,
    uploaded_by: uuid.UUID = RECORDS_ID,
    access_tags: Iterable[str] = (),
    actual_fingerprint: str | None = None,
) -> IngestFileResult:
    """Ingest or safely reuse one governed file and return a durable outcome."""
    if not manifest_file.runtime_approved or manifest_file.quarantine_state != "active":
        return account_failure(
            manifest_file,
            "not_runtime_approved",
            state="excluded",
            document_id=None,
            fingerprint=manifest_file.sha256,
        )
    if actual_fingerprint is None:
        return account_failure(manifest_file, "source_fingerprint_unknown", fingerprint=None)
    if actual_fingerprint != manifest_file.sha256:
        return account_failure(manifest_file, "source_fingerprint_mismatch", fingerprint=actual_fingerprint)

    preparation = await _prepare_ingestion(
        session,
        manifest_file,
        storage_uri=storage_uri,
        title=title,
        uploaded_by=uploaded_by,
    )
    if preparation.result is not None:
        return preparation.result
    if preparation.document is None:
        return account_failure(manifest_file, "document_missing")
    return await _process_prepared(
        session,
        manifest_file,
        preparation,
        processor,
        access_tags,
    )


def account_failure(
    manifest_file: CorpusFile,
    error_code: str,
    *,
    state: str = "failed",
    document_id: uuid.UUID | None = None,
    fingerprint: Optional[str] = None,
) -> IngestFileResult:
    """Create a sanitized accounting result when persistence cannot start."""
    persisted_document_id = (
        document_id if document_id is not None or state == "excluded" else _document_uuid(manifest_file)
    )
    return _result(
        manifest_file,
        document_id=persisted_document_id,
        state=state,
        fingerprint=fingerprint,
        error_code=_sanitize_error_code(error_code),
    )


async def _prepare_ingestion(
    session: AsyncSession,
    manifest_file: CorpusFile,
    *,
    storage_uri: str | None,
    title: str | None,
    uploaded_by: uuid.UUID,
) -> _Preparation:
    document_id = _document_uuid(manifest_file)
    document = await session.get(Document, document_id, populate_existing=True)
    if document is None:
        document = Document(
            id=document_id,
            patient_id=manifest_file.patient_id,
            uploaded_by=uploaded_by,
            title=title or manifest_file.document_id,
            document_type=manifest_file.document_type,
            storage_uri=storage_uri or manifest_file.relative_path,
            mime_type=manifest_file.mime_type,
            status="uploaded",
        )
        session.add(document)
        await session.commit()
        return _Preparation(document=document, start_generation=0, attempts=1)
    return await _prepare_existing(
        session,
        manifest_file,
        document,
        storage_uri=storage_uri,
        title=title,
        uploaded_by=uploaded_by,
    )


async def _prepare_existing(
    session: AsyncSession,
    manifest_file: CorpusFile,
    document: Document,
    *,
    storage_uri: str | None,
    title: str | None,
    uploaded_by: uuid.UUID,
) -> _Preparation:
    derived = await _derived_ids(session, document.id)
    persisted_attempts = await _persisted_attempts(session, document, derived)
    fingerprint_error = _existing_fingerprint_error(document, manifest_file.sha256)
    if fingerprint_error is not None:
        result = _database_result(manifest_file, document, derived, persisted_attempts, "failed", fingerprint_error)
        return _Preparation(None, document.index_generation, persisted_attempts, result)

    if document.status == "indexed" and document.index_generation > 0:
        reuse_decision = await _completed_reuse_decision(session, document, derived)
        if reuse_decision == "reuse":
            result = _database_result(manifest_file, document, derived, persisted_attempts, "indexed", None)
            return _Preparation(None, document.index_generation, persisted_attempts, result)
        if reuse_decision != "retry":
            await _persist_failure(
                session,
                document.id,
                reuse_decision,
                max(persisted_attempts, 1),
                expected_generation=document.index_generation,
            )
            failed = await session.get(Document, document.id, populate_existing=True)
            result = _database_result(manifest_file, failed, derived, persisted_attempts, "failed", reuse_decision)
            return _Preparation(None, document.index_generation, persisted_attempts, result)

    attempts = max(persisted_attempts + 1, 2)
    await _reset_for_processing(
        session,
        document,
        storage_uri=storage_uri,
        title=title,
        uploaded_by=uploaded_by,
    )
    refreshed = await session.get(Document, document.id, populate_existing=True)
    return _Preparation(refreshed, document.index_generation, attempts)


async def _reset_for_processing(
    session: AsyncSession,
    document: Document,
    *,
    storage_uri: str | None,
    title: str | None,
    uploaded_by: uuid.UUID,
) -> None:
    await session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
    await session.execute(delete(DocumentPage).where(DocumentPage.document_id == document.id))
    await session.execute(
        update(Document)
        .where(Document.id == document.id)
        .values(
            storage_uri=storage_uri or document.storage_uri,
            title=title or document.title,
            uploaded_by=uploaded_by,
            status="ocr_processing",
            ocr_error=None,
        )
    )
    await session.commit()


async def _process_prepared(
    session: AsyncSession,
    manifest_file: CorpusFile,
    preparation: _Preparation,
    processor: IngestionProcessor,
    access_tags: Iterable[str],
) -> IngestFileResult:
    document = preparation.document
    assert document is not None
    document_id = document.id
    try:
        processor_error = await processor(session, document)
        await session.flush()
    except Exception as exc:
        await session.rollback()
        return await _failed_processing_result(
            session,
            manifest_file,
            document_id,
            preparation.attempts,
            exc,
            expected_generation=preparation.start_generation,
        )

    if processor_error is not None:
        return await _returned_failure_result(
            session,
            manifest_file,
            document_id,
            preparation.attempts,
            processor_error,
            expected_generation=preparation.start_generation,
        )
    return await _complete_processing(session, manifest_file, preparation, access_tags)


async def _failed_processing_result(
    session: AsyncSession,
    manifest_file: CorpusFile,
    document_id: uuid.UUID,
    attempts: int,
    error: object,
    *,
    expected_generation: int | None = None,
) -> IngestFileResult:
    error_code = _sanitize_error_code(error)
    persisted = await _persist_failure(
        session,
        document_id,
        error_code,
        attempts,
        expected_generation=expected_generation,
    )
    if not persisted:
        error_code = "stale_generation"
    document = await session.get(Document, document_id, populate_existing=True)
    derived = await _derived_ids(session, document_id)
    return _database_result(manifest_file, document, derived, attempts, "failed", error_code)


async def _returned_failure_result(
    session: AsyncSession,
    manifest_file: CorpusFile,
    document_id: uuid.UUID,
    attempts: int,
    error: object,
    *,
    expected_generation: int | None = None,
) -> IngestFileResult:
    error_code = _sanitize_error_code(error)
    document = await session.get(Document, document_id, populate_existing=True)
    if document is not None and error_code != "stale_generation":
        persisted = await _persist_failure(
            session,
            document_id,
            error_code,
            attempts,
            expected_generation=expected_generation,
        )
        if not persisted:
            error_code = "stale_generation"
        document = await session.get(Document, document_id, populate_existing=True)
    derived = await _derived_ids(session, document_id)
    return _database_result(manifest_file, document, derived, attempts, "failed", error_code)


async def _complete_processing(
    session: AsyncSession,
    manifest_file: CorpusFile,
    preparation: _Preparation,
    access_tags: Iterable[str],
) -> IngestFileResult:
    document = await session.get(Document, preparation.document.id, populate_existing=True)
    if document is None:
        return account_failure(manifest_file, "document_missing")
    derived = await _derived_ids(session, document.id)
    derived_error = await _derived_error(session, document.id, derived)
    if document.status in {"ocr_failed", "index_failed"}:
        return await _returned_failure_result(
            session,
            manifest_file,
            document.id,
            preparation.attempts,
            document.ocr_error,
            expected_generation=preparation.start_generation,
        )
    if derived_error is not None:
        return await _failed_processing_result(
            session,
            manifest_file,
            document.id,
            preparation.attempts,
            derived_error,
            expected_generation=preparation.start_generation,
        )
    return await _finalize_success(session, manifest_file, document, derived, preparation, access_tags)


async def _finalize_success(
    session: AsyncSession,
    manifest_file: CorpusFile,
    document: Document,
    derived: DerivedIds,
    preparation: _Preparation,
    access_tags: Iterable[str],
) -> IngestFileResult:
    expected_generation = preparation.start_generation + 1
    if document.status == "indexed":
        if document.index_generation != expected_generation:
            return _database_result(
                manifest_file, document, derived, preparation.attempts, "failed", "stale_generation"
            )
        if document.indexed_source_sha256 != manifest_file.sha256:
            return _database_result(
                manifest_file, document, derived, preparation.attempts, "failed", "source_fingerprint_mismatch"
            )
    else:
        await session.execute(
            update(Document)
            .where(Document.id == document.id)
            .values(
                status="indexed",
                index_generation=expected_generation,
                indexed_source_sha256=manifest_file.sha256,
                page_count=len(derived.page_ids),
                ocr_error=None,
            )
        )
    await _stamp_chunk_metadata(session, document.id, expected_generation, preparation.attempts, access_tags)
    await session.commit()
    refreshed = await session.get(Document, document.id, populate_existing=True)
    return _database_result(manifest_file, refreshed, derived, preparation.attempts, "indexed", None)


def certify_ingestion(
    manifest: CorpusManifest,
    first_run: IngestionRun,
    second_run: IngestionRun,
) -> IngestCertificationReport:
    """Compare two complete runs without trusting importer success logging."""
    manifest_fingerprints = {item.relative_path: item.sha256 for item in manifest.files}
    first_by_path = _results_by_path(first_run.results)
    second_by_path = _results_by_path(second_run.results)
    manifest_paths = set(manifest_fingerprints)
    unexpected_files = tuple(sorted((set(first_by_path) | set(second_by_path)) - manifest_paths))
    missing_files = tuple(
        sorted(
            path
            for path in manifest_paths
            if len(first_by_path.get(path, ())) != 1 or len(second_by_path.get(path, ())) != 1
        )
    )
    differences = _idempotency_differences(
        manifest_fingerprints,
        first_run.results,
        second_run.results,
        first_by_path,
        second_by_path,
    )
    return IngestCertificationReport(
        manifest_file_count=len(manifest.files),
        first_run_accounted_count=len(first_run.results),
        second_run_accounted_count=len(second_run.results),
        missing_files=missing_files,
        unexpected_files=unexpected_files,
        manifest_mismatches=_manifest_mismatches(manifest, first_run, second_run),
        duplicate_documents=differences[0],
        duplicate_pages=differences[1],
        duplicate_chunks=differences[2],
        source_fingerprint_mismatches=differences[3],
        generation_drift=differences[4],
        attempt_drift=differences[5],
        failed_files=differences[6],
    )


def _idempotency_differences(
    manifest_fingerprints: dict[str, str],
    first_results: tuple[IngestFileResult, ...],
    second_results: tuple[IngestFileResult, ...],
    first_by_path: dict[str, tuple[IngestFileResult, ...]],
    second_by_path: dict[str, tuple[IngestFileResult, ...]],
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    documents = set(_duplicate_ids(first_results, "document_id")) | set(_duplicate_ids(second_results, "document_id"))
    pages = set(_duplicate_ids(first_results, "page_ids")) | set(_duplicate_ids(second_results, "page_ids"))
    chunks = set(_duplicate_ids(first_results, "chunk_ids")) | set(_duplicate_ids(second_results, "chunk_ids"))
    fingerprints: set[str] = set()
    generations: set[str] = set()
    attempts: set[str] = set()
    failed: set[str] = set()
    for path, fingerprint in manifest_fingerprints.items():
        first = _single_result(first_by_path, path)
        second = _single_result(second_by_path, path)
        if first is None or second is None:
            continue
        if first.fingerprint != fingerprint or second.fingerprint != fingerprint:
            fingerprints.add(path)
        if first.document_id != second.document_id:
            documents.add(path)
        if first.generation != second.generation:
            generations.add(path)
        if first.attempts != second.attempts:
            attempts.add(path)
        if first.state == "indexed" and second.state == "indexed" and first.page_ids != second.page_ids:
            pages.add(path)
        if first.state == "indexed" and second.state == "indexed" and first.chunk_ids != second.chunk_ids:
            chunks.add(path)
        if first.state == "failed" or second.state == "failed":
            failed.add(path)
    return tuple(map(tuple, map(sorted, (documents, pages, chunks, fingerprints, generations, attempts, failed))))


def _manifest_mismatches(
    manifest: CorpusManifest,
    first_run: IngestionRun,
    second_run: IngestionRun,
) -> tuple[str, ...]:
    mismatches = []
    for label, run in (("first_run", first_run), ("second_run", second_run)):
        if run.manifest.corpus_version != manifest.corpus_version or run.manifest.files != manifest.files:
            mismatches.append(label)
    return tuple(mismatches)


def _document_uuid(manifest_file: CorpusFile) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"hospital-ai://synthetic/{manifest_file.relative_path}")


def _existing_fingerprint_error(document: Document, fingerprint: str) -> str | None:
    if document.status != "indexed" and document.indexed_source_sha256 is None:
        return None
    if document.indexed_source_sha256 is None:
        return "source_fingerprint_unknown"
    if document.indexed_source_sha256 != fingerprint:
        return "source_fingerprint_mismatch"
    return None


async def _completed_reuse_decision(session: AsyncSession, document: Document, derived: DerivedIds) -> str:
    if not derived.page_ids or not derived.chunk_ids or document.page_count != len(derived.page_ids):
        return "retry"
    rows = await session.execute(
        select(DocumentChunk.embedding, DocumentChunk.meta).where(DocumentChunk.document_id == document.id)
    )
    chunk_rows = rows.all()
    if len(chunk_rows) != len(derived.chunk_ids) or any(not embedding for embedding, _meta in chunk_rows):
        return "embedding_count_mismatch"
    generations = [(meta or {}).get("index_generation") for _embedding, meta in chunk_rows]
    if any(generation is None for generation in generations):
        return "retry"
    if any(generation != document.index_generation for generation in generations):
        return "stale_generation"
    return "reuse"


async def _derived_ids(session: AsyncSession, document_id: uuid.UUID) -> DerivedIds:
    pages = await session.execute(
        select(DocumentPage.id)
        .where(DocumentPage.document_id == document_id)
        .order_by(DocumentPage.page_number, DocumentPage.id)
    )
    chunks = await session.execute(
        select(DocumentChunk.id)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index, DocumentChunk.id)
    )
    return DerivedIds(tuple(pages.scalars().all()), tuple(chunks.scalars().all()))


async def _derived_error(session: AsyncSession, document_id: uuid.UUID, derived: DerivedIds) -> str | None:
    if not derived.page_ids or not derived.chunk_ids:
        return "derived_rows_incomplete"
    embeddings = await session.execute(select(DocumentChunk.embedding).where(DocumentChunk.document_id == document_id))
    values = embeddings.scalars().all()
    if len(values) != len(derived.chunk_ids) or any(not embedding for embedding in values):
        return "embedding_count_mismatch"
    return None


async def _persisted_attempts(session: AsyncSession, document: Document, derived: DerivedIds) -> int:
    marker = _ATTEMPT_MARKER.fullmatch(document.ocr_error or "")
    marker_attempts = int(marker.group("count")) if marker else 0
    if not derived.chunk_ids:
        return max(marker_attempts, document.index_generation)
    rows = await session.execute(select(DocumentChunk.meta).where(DocumentChunk.document_id == document.id))
    chunk_attempts = [int((meta or {}).get("ingestion_attempts", 0)) for meta in rows.scalars().all()]
    return max([marker_attempts, document.index_generation, *chunk_attempts])


async def _persist_failure(
    session: AsyncSession,
    document_id: uuid.UUID,
    error_code: str,
    attempts: int,
    *,
    expected_generation: int | None = None,
) -> bool:
    safe_code = _sanitize_error_code(error_code)
    status = "ocr_failed" if safe_code == "ocr_failed" else "index_failed"
    statement = update(Document).where(Document.id == document_id)
    if expected_generation is not None:
        statement = statement.where(Document.index_generation == expected_generation)
    result = await session.execute(
        statement.values(status=status, ocr_error=f"{safe_code}__attempt_{attempts}")
    )
    await session.commit()
    return result.rowcount == 1


async def _stamp_chunk_metadata(
    session: AsyncSession,
    document_id: uuid.UUID,
    generation: int,
    attempts: int,
    access_tags: Iterable[str],
) -> None:
    tags = tuple(sorted(set(access_tags)))
    rows = await session.execute(
        select(DocumentChunk.id, DocumentChunk.meta).where(DocumentChunk.document_id == document_id)
    )
    for chunk_id, meta in rows.all():
        stamped = {**(meta or {}), "index_generation": generation, "ingestion_attempts": attempts}
        if tags:
            stamped["access_tags"] = list(tags)
        await session.execute(update(DocumentChunk).where(DocumentChunk.id == chunk_id).values(meta=stamped))


def _database_result(
    manifest_file: CorpusFile,
    document: Document | None,
    derived: DerivedIds,
    attempts: int,
    state: str,
    error_code: str | None,
) -> IngestFileResult:
    return _result(
        manifest_file,
        document_id=document.id if document is not None else _document_uuid(manifest_file),
        state=state,
        fingerprint=manifest_file.sha256,
        page_ids=derived.page_ids,
        chunk_ids=derived.chunk_ids,
        generation=document.index_generation if document is not None else 0,
        attempts=attempts,
        error_code=error_code,
    )


def _result(
    manifest_file: CorpusFile,
    *,
    document_id: uuid.UUID | None,
    state: str,
    fingerprint: Optional[str] = None,
    page_ids: tuple[uuid.UUID, ...] = (),
    chunk_ids: tuple[uuid.UUID, ...] = (),
    generation: int = 0,
    attempts: int = 0,
    error_code: str | None = None,
) -> IngestFileResult:
    return IngestFileResult(
        path=manifest_file.relative_path,
        fingerprint=fingerprint,
        state=state,
        document_id=document_id,
        page_ids=page_ids,
        chunk_ids=chunk_ids,
        generation=generation,
        attempts=attempts,
        error_code=error_code,
    )


def _sanitize_error_code(error: object) -> str:
    message = str(error or "").strip().lower()
    marker = _ATTEMPT_MARKER.fullmatch(message)
    if marker:
        return marker.group("code")
    if message in _SAFE_ERROR_CODES:
        return message
    if "embedding count mismatch" in message:
        return "embedding_count_mismatch"
    if "fingerprint" in message and "unknown" in message:
        return "source_fingerprint_unknown"
    if "fingerprint" in message or "sha-256" in message:
        return "source_fingerprint_mismatch"
    if "ocr" in message:
        return "ocr_failed"
    return "processing_failed"


def _results_by_path(results: tuple[IngestFileResult, ...]) -> dict[str, tuple[IngestFileResult, ...]]:
    paths = {result.path for result in results}
    return {path: tuple(result for result in results if result.path == path) for path in paths}


def _single_result(results_by_path: dict[str, tuple[IngestFileResult, ...]], path: str) -> IngestFileResult | None:
    results = results_by_path.get(path, ())
    return results[0] if len(results) == 1 else None


def _duplicate_ids(results: tuple[IngestFileResult, ...], field_name: str) -> tuple[str, ...]:
    owners: dict[uuid.UUID, list[str]] = {}
    for result in results:
        value = getattr(result, field_name)
        identifiers = value if isinstance(value, tuple) else (() if value is None else (value,))
        for identifier in identifiers:
            owners.setdefault(identifier, []).append(result.path)
    duplicate_paths = {path for paths in owners.values() if len(paths) > 1 for path in paths}
    path_counts = Counter(result.path for result in results)
    duplicate_paths.update(path for path, count in path_counts.items() if count > 1)
    return tuple(sorted(duplicate_paths))
