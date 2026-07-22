from __future__ import annotations

import hashlib
import os
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select, update
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from hospital_ai.core.config import Settings
from hospital_ai.db.migrations import PATIENT_ALICE_ID, seed_synthetic_data
from hospital_ai.db.models import Base, Document, DocumentChunk, DocumentPage
from hospital_ai.evaluation.ingestion import IngestFileResult, IngestionRun, certify_ingestion, ingest_one
from hospital_ai.evaluation.models import CorpusFile, CorpusManifest
from hospital_ai.services.embeddings import deterministic_embedding
from hospital_ai.services.ocr import OcrPage
from hospital_ai.workers.jobs import process_document
from scripts.ingest_synthetic_dataset import ingest_file


@pytest_asyncio.fixture
async def ingestion_session_and_settings(tmp_path: Path) -> AsyncIterator[tuple[AsyncSession, Settings]]:
    database_url = os.environ.get("HOSPITAL_AI_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    if database_url.startswith("postgresql") and not (make_url(database_url).database or "").endswith("_test"):
        raise RuntimeError("ingestion certification requires a database named with the _test suffix")
    settings = Settings(
        database_url=database_url,
        storage_root=tmp_path / "storage",
        worker_inline=True,
        embedding_provider="deterministic",
        chat_provider="stub",
        evidence_threshold=0.0,
    )
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        await seed_synthetic_data(session)
        await _delete_test_document(session)
        yield session, settings
        await session.rollback()
        await _delete_test_document(session)

    await engine.dispose()


async def _delete_test_document(session: AsyncSession) -> None:
    document_id = uuid.uuid5(
        uuid.NAMESPACE_URL,
        "hospital-ai://synthetic/patients_documents/patient_MRN0001_report.pdf",
    )
    worker_ids = await session.scalars(
        select(Document.id).where(Document.title.in_(("Sensitive failure", "Stale generation")))
    )
    document_ids = (document_id, *worker_ids.all())
    await session.execute(delete(DocumentChunk).where(DocumentChunk.document_id.in_(document_ids)))
    await session.execute(delete(DocumentPage).where(DocumentPage.document_id.in_(document_ids)))
    await session.execute(delete(Document).where(Document.id.in_(document_ids)))
    await session.commit()


class FailingProcessor:
    def __init__(self, error_code: str) -> None:
        self.error_code = error_code

    async def __call__(self, session, document) -> None:
        raise RuntimeError(self.error_code)


class SuccessfulProcessor:
    async def __call__(self, session, document) -> None:
        page = DocumentPage(document_id=document.id, page_number=1, ocr_text="synthetic evidence", ocr_confidence=1.0)
        session.add(page)
        await session.flush()
        session.add(
            DocumentChunk(
                document_id=document.id,
                page_id=page.id,
                patient_id=document.patient_id,
                chunk_index=0,
                content="synthetic evidence",
                token_count=2,
                embedding=[0.0] * 1024,
                meta={"page_number": 1},
            )
        )


@pytest.fixture
def manifest_file() -> CorpusFile:
    return CorpusFile(
        relative_path="patients_documents/patient_MRN0001_report.pdf",
        sha256="a" * 64,
        byte_size=17,
        patient_id=PATIENT_ALICE_ID,
        document_id="MRN0001-report",
        document_type="report",
        mime_type="application/pdf",
        generator="HOSP-AI-001 synthetic dataset generator",
        generator_version="1.0",
        source="test",
        synthetic=True,
        license_state="synthetic-approved",
        classification="patient_record",
        quarantine_state="active",
        runtime_approved=True,
    )


@pytest.fixture
def manifest(manifest_file: CorpusFile) -> CorpusManifest:
    return CorpusManifest(
        schema_version="1.0",
        corpus_version="test",
        patient_count=1,
        patient_record_count=1,
        files=(manifest_file,),
    )


@pytest.mark.asyncio
async def test_failed_existing_document_is_retried_not_skipped(
    ingestion_session_and_settings, manifest_file: CorpusFile
) -> None:
    session, _settings = ingestion_session_and_settings

    first = await ingest_one(
        session,
        manifest_file,
        processor=FailingProcessor("ocr_failed"),
        actual_fingerprint=manifest_file.sha256,
    )
    assert first.state == "failed"
    assert first.error_code == "ocr_failed"
    failed_document = await session.get(Document, first.document_id)
    assert failed_document is not None
    assert failed_document.status == "ocr_failed"
    assert failed_document.ocr_error == "ocr_failed__attempt_1"

    second = await ingest_one(
        session,
        manifest_file,
        processor=SuccessfulProcessor(),
        actual_fingerprint=manifest_file.sha256,
    )
    assert second.state == "indexed"
    assert second.attempts == 2


@pytest.mark.asyncio
async def test_unchanged_second_run_has_no_duplicate_derived_rows(
    ingestion_session_and_settings, manifest: CorpusManifest, manifest_file: CorpusFile
) -> None:
    session, _settings = ingestion_session_and_settings

    first_result = await ingest_one(
        session,
        manifest_file,
        processor=SuccessfulProcessor(),
        actual_fingerprint=manifest_file.sha256,
    )
    second_result = await ingest_one(
        session,
        manifest_file,
        processor=SuccessfulProcessor(),
        actual_fingerprint=manifest_file.sha256,
    )
    first_run = IngestionRun(manifest=manifest, results=(first_result,))
    second_run = IngestionRun(manifest=manifest, results=(second_result,))
    report = certify_ingestion(manifest, first_run, second_run)

    page_count = await session.scalar(select(func.count()).select_from(DocumentPage))
    chunk_count = await session.scalar(select(func.count()).select_from(DocumentChunk))

    assert report.missing_files == ()
    assert report.duplicate_documents == ()
    assert report.duplicate_pages == ()
    assert report.duplicate_chunks == ()
    assert report.source_fingerprint_mismatches == ()
    assert page_count == 1
    assert chunk_count == 1


@pytest.mark.asyncio
async def test_worker_rejects_source_that_does_not_match_manifest_fingerprint(
    ingestion_session_and_settings, manifest_file: CorpusFile
) -> None:
    session, settings = ingestion_session_and_settings
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    source_path = settings.storage_root / "changed-source.pdf"
    source_path.write_bytes(b"not the manifest bytes")

    async def processor(session, document) -> None:
        await process_document(
            session,
            document.id,
            settings,
            expected_source_sha256=manifest_file.sha256,
        )

    result = await ingest_one(
        session,
        manifest_file,
        processor=processor,
        storage_uri=str(source_path),
        actual_fingerprint=manifest_file.sha256,
    )

    assert result.state == "failed"
    assert result.error_code == "source_fingerprint_mismatch"
    assert result.page_ids == ()
    assert result.chunk_ids == ()


@pytest.mark.asyncio
async def test_quarantined_public_knowledge_is_accounted_without_processing(
    ingestion_session_and_settings, manifest: CorpusManifest, manifest_file: CorpusFile
) -> None:
    session, _settings = ingestion_session_and_settings
    quarantined_file = manifest_file.copy(
        update={
            "patient_id": None,
            "classification": "public_knowledge",
            "license_state": "pending-review",
            "quarantine_state": "excluded_pending_review",
            "runtime_approved": False,
        }
    )

    async def forbidden_processor(_session, _document) -> None:
        raise AssertionError("quarantined public knowledge must not be processed")

    first = await ingest_one(session, quarantined_file, processor=forbidden_processor)
    second = await ingest_one(session, quarantined_file, processor=forbidden_processor)
    quarantined_manifest = manifest.copy(update={"files": (quarantined_file,)})
    report = certify_ingestion(
        quarantined_manifest,
        IngestionRun(manifest=quarantined_manifest, results=(first,)),
        IngestionRun(manifest=quarantined_manifest, results=(second,)),
    )

    assert first.state == "excluded"
    assert first.error_code == "not_runtime_approved"
    assert first.document_id is None
    assert report.is_certified


@pytest.mark.asyncio
async def test_unknown_actual_fingerprint_fails_closed_without_processing(
    ingestion_session_and_settings, manifest_file: CorpusFile
) -> None:
    session, _settings = ingestion_session_and_settings

    async def forbidden_processor(_session, _document) -> None:
        raise AssertionError("unknown fingerprints must fail before processing")

    result = await ingest_one(session, manifest_file, processor=forbidden_processor)

    assert result.state == "failed"
    assert result.error_code == "source_fingerprint_unknown"
    assert result.document_id is not None
    assert await session.get(Document, result.document_id) is None


@pytest.mark.asyncio
async def test_completed_generation_with_missing_embedding_fails_closed(
    ingestion_session_and_settings, manifest_file: CorpusFile
) -> None:
    session, _settings = ingestion_session_and_settings
    first = await ingest_one(
        session,
        manifest_file,
        processor=SuccessfulProcessor(),
        actual_fingerprint=manifest_file.sha256,
    )
    await session.execute(
        update(DocumentChunk).where(DocumentChunk.document_id == first.document_id).values(embedding=None)
    )
    await session.commit()

    async def forbidden_processor(_session, _document) -> None:
        raise AssertionError("corrupt completed generations must fail closed")

    second = await ingest_one(
        session,
        manifest_file,
        processor=forbidden_processor,
        actual_fingerprint=manifest_file.sha256,
    )

    assert second.state == "failed"
    assert second.error_code == "embedding_count_mismatch"


@pytest.mark.asyncio
async def test_attempts_survive_repeated_failures_and_reuse_does_not_increment(
    ingestion_session_and_settings, manifest_file: CorpusFile
) -> None:
    session, _settings = ingestion_session_and_settings
    first = await ingest_one(
        session,
        manifest_file,
        processor=FailingProcessor("ocr_failed"),
        actual_fingerprint=manifest_file.sha256,
    )
    second = await ingest_one(
        session,
        manifest_file,
        processor=FailingProcessor("ocr_failed"),
        actual_fingerprint=manifest_file.sha256,
    )
    third = await ingest_one(
        session,
        manifest_file,
        processor=SuccessfulProcessor(),
        actual_fingerprint=manifest_file.sha256,
    )

    async def forbidden_processor(_session, _document) -> None:
        raise AssertionError("a reusable completed generation must not be processed")

    reused = await ingest_one(
        session,
        manifest_file,
        processor=forbidden_processor,
        actual_fingerprint=manifest_file.sha256,
    )

    assert (first.attempts, second.attempts, third.attempts, reused.attempts) == (1, 2, 3, 3)


@pytest.mark.asyncio
async def test_importer_accounts_for_missing_source_file(
    ingestion_session_and_settings, manifest_file: CorpusFile, tmp_path: Path
) -> None:
    session, settings = ingestion_session_and_settings

    result = await ingest_file(session, manifest_file, {}, tmp_path, settings)

    assert result.path == manifest_file.relative_path
    assert result.state == "failed"
    assert result.error_code == "source_unavailable"


@pytest.mark.asyncio
async def test_importer_does_not_overwrite_target_before_fingerprint_validation(
    ingestion_session_and_settings, manifest_file: CorpusFile, tmp_path: Path
) -> None:
    session, settings = ingestion_session_and_settings
    source_path = tmp_path / manifest_file.relative_path
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_bytes(b"bytes do not match the manifest")
    target_directory = settings.storage_root / "patients" / str(manifest_file.patient_id)
    target_directory.mkdir(parents=True, exist_ok=True)
    target_path = target_directory / f"{manifest_file.document_id}_{source_path.name}"
    target_path.write_bytes(b"trusted indexed bytes")

    result = await ingest_file(session, manifest_file, {}, tmp_path, settings)

    assert result.error_code == "source_fingerprint_mismatch"
    assert target_path.read_bytes() == b"trusted indexed bytes"


@pytest.mark.asyncio
async def test_worker_returns_sanitized_ocr_failure_code(
    ingestion_session_and_settings, monkeypatch, tmp_path: Path
) -> None:
    session, settings = ingestion_session_and_settings
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    source_path = settings.storage_root / "sensitive-failure.txt"
    source_path.write_text("synthetic source", encoding="utf-8")
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=uuid.UUID("10000000-0000-0000-0000-000000000002"),
        title="Sensitive failure",
        document_type="clinical_note",
        storage_uri=str(source_path),
        mime_type="text/plain",
        status="uploaded",
    )
    session.add(document)
    await session.commit()

    def fail_ocr(self, **_kwargs):
        raise RuntimeError("synthetic patient secret must not persist")

    monkeypatch.setattr("hospital_ai.services.ocr.OcrService.extract_pages", fail_ocr)
    error_code = await process_document(
        session,
        document.id,
        settings,
        expected_source_sha256=source_hash,
    )

    refreshed = await session.get(Document, document.id, populate_existing=True)
    assert error_code == "ocr_failed"
    assert refreshed.ocr_error == "ocr_failed"


@pytest.mark.asyncio
async def test_worker_returns_stale_generation_terminal_code(
    ingestion_session_and_settings, monkeypatch, tmp_path: Path
) -> None:
    session, settings = ingestion_session_and_settings
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    source_path = settings.storage_root / "stale-generation.txt"
    source_path.write_text("replacement content", encoding="utf-8")
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=uuid.UUID("10000000-0000-0000-0000-000000000002"),
        title="Stale generation",
        document_type="clinical_note",
        storage_uri=str(source_path),
        mime_type="text/plain",
        status="uploaded",
    )
    session.add(document)
    await session.commit()
    document_id = document.id

    def extract_pages(self, **_kwargs):
        return [OcrPage(page_number=1, text="stale content", confidence=1.0)]

    async def complete_newer_generation(self, contents):
        texts = list(contents)
        await session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(index_generation=Document.index_generation + 1, status="indexed")
        )
        await session.commit()
        return [deterministic_embedding(text) for text in texts]

    monkeypatch.setattr("hospital_ai.services.ocr.OcrService.extract_pages", extract_pages)
    monkeypatch.setattr("hospital_ai.services.embeddings.EmbeddingService.embed_many", complete_newer_generation)
    error_code = await process_document(
        session,
        document_id,
        settings,
        expected_source_sha256=source_hash,
    )

    assert error_code == "stale_generation"


@pytest.mark.asyncio
async def test_worker_exception_race_returns_stale_without_overwriting_newer_generation(
    ingestion_session_and_settings, monkeypatch
) -> None:
    session, settings = ingestion_session_and_settings
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    source_path = settings.storage_root / "stale-exception.txt"
    source_path.write_text("replacement content", encoding="utf-8")
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=uuid.UUID("10000000-0000-0000-0000-000000000002"),
        title="Stale exception",
        document_type="clinical_note",
        storage_uri=str(source_path),
        mime_type="text/plain",
        status="uploaded",
    )
    session.add(document)
    await session.commit()
    document_id = document.id

    def extract_pages(self, **_kwargs):
        return [OcrPage(page_number=1, text="stale content", confidence=1.0)]

    async def fail_after_newer_generation(self, contents):
        list(contents)
        await session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(index_generation=Document.index_generation + 1, status="indexed")
        )
        await session.commit()
        raise RuntimeError("embedding failed after a newer generation committed")

    monkeypatch.setattr("hospital_ai.services.ocr.OcrService.extract_pages", extract_pages)
    monkeypatch.setattr("hospital_ai.services.embeddings.EmbeddingService.embed_many", fail_after_newer_generation)
    error_code = await process_document(
        session,
        document_id,
        settings,
        expected_source_sha256=source_hash,
    )

    refreshed = await session.get(Document, document_id, populate_existing=True)
    assert error_code == "stale_generation"
    assert refreshed.status == "indexed"


def test_certification_rejects_generation_and_fingerprint_drift(
    manifest: CorpusManifest, manifest_file: CorpusFile
) -> None:
    document_id = uuid.uuid4()
    page_id = uuid.uuid4()
    chunk_id = uuid.uuid4()
    first_result = IngestFileResult(
        path=manifest_file.relative_path,
        fingerprint="b" * 64,
        state="indexed",
        document_id=document_id,
        page_ids=(page_id,),
        chunk_ids=(chunk_id,),
        generation=1,
        attempts=1,
        error_code=None,
    )
    second_result = IngestFileResult(
        path=manifest_file.relative_path,
        fingerprint=manifest_file.sha256,
        state="indexed",
        document_id=document_id,
        page_ids=(page_id,),
        chunk_ids=(chunk_id,),
        generation=2,
        attempts=2,
        error_code=None,
    )

    report = certify_ingestion(
        manifest,
        IngestionRun(manifest=manifest, results=(first_result,)),
        IngestionRun(manifest=manifest, results=(second_result,)),
    )

    assert not report.is_certified
    assert report.source_fingerprint_mismatches == (manifest_file.relative_path,)
    assert report.generation_drift == (manifest_file.relative_path,)
    assert report.attempt_drift == (manifest_file.relative_path,)
