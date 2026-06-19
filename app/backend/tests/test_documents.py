import hashlib
from pathlib import Path

import pytest
from sqlalchemy import select, update

from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, RECORDS_ID
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage
from hospital_ai.services.embeddings import deterministic_embedding
from hospital_ai.services.ocr import OcrPage
from hospital_ai.services.retrieval import RetrievalService
from hospital_ai.workers.jobs import process_document
from tests.conftest import create_indexed_document


def _storage_file(settings, name: str) -> Path:
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    return settings.storage_root / name


async def _attach_source_file(
    document: Document,
    session,
    settings,
    name: str,
    content: str,
) -> Path:
    storage_file = _storage_file(settings, name)
    storage_file.write_text(content, encoding="utf-8")
    document.storage_uri = str(storage_file)
    document.indexed_source_sha256 = hashlib.sha256(storage_file.read_bytes()).hexdigest()
    await session.commit()
    return storage_file


@pytest.mark.asyncio
async def test_text_document_moves_to_indexed(session_and_settings, tmp_path: Path):
    session, settings = session_and_settings
    storage_file = _storage_file(settings, "note.txt")
    storage_file.write_text(
        "Patient reports dizziness. Follow up with cardiology.",
        encoding="utf-8",
    )
    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Synthetic note",
        document_type="clinical_note",
        storage_uri=str(storage_file),
        mime_type="text/plain",
        status="uploaded",
    )
    session.add(document)
    await session.commit()

    await process_document(session, document.id, settings)

    refreshed = await session.get(Document, document.id)
    assert refreshed.status == "indexed"
    assert refreshed.page_count == 1
    assert refreshed.indexed_source_sha256 == hashlib.sha256(storage_file.read_bytes()).hexdigest()
    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document.id))
    assert len(result.scalars().all()) == 1


@pytest.mark.asyncio
async def test_failed_ocr_creates_no_chunks(session_and_settings, tmp_path: Path, monkeypatch):
    session, settings = session_and_settings
    storage_file = _storage_file(settings, "scan.pdf")
    storage_file.write_bytes(b"%PDF-1.4 synthetic")
    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Bad scan",
        document_type="scan",
        storage_uri=str(storage_file),
        mime_type="application/pdf",
        status="uploaded",
    )
    session.add(document)
    await session.commit()

    def fail_ocr(self, **_kwargs):
        raise RuntimeError("ocr failed")

    monkeypatch.setattr("hospital_ai.services.ocr.OcrService.extract_pages", fail_ocr)
    await process_document(session, document.id, settings)

    refreshed = await session.get(Document, document.id)
    assert refreshed.status == "ocr_failed"
    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document.id))
    assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_failed_reindex_preserves_existing_searchable_chunks(
    session_and_settings,
    monkeypatch,
):
    session, settings = session_and_settings
    document = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Previously indexed note",
        content="Original indexed content remains searchable.",
    )
    await _attach_source_file(
        document,
        session,
        settings,
        "previously-indexed-note.txt",
        "Original indexed content remains searchable.",
    )

    def fail_ocr(self, **_kwargs):
        raise RuntimeError("ocr failed")

    monkeypatch.setattr("hospital_ai.services.ocr.OcrService.extract_pages", fail_ocr)
    await process_document(session, document.id, settings)

    refreshed = await session.get(Document, document.id)
    assert refreshed.status == "indexed"
    assert refreshed.ocr_error == "ocr failed"
    assert refreshed.index_generation == 0

    chunk_result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document.id))
    chunks = list(chunk_result.scalars().all())
    assert len(chunks) == 1
    assert chunks[0].content == "Original indexed content remains searchable."

    page_result = await session.execute(select(DocumentPage).where(DocumentPage.document_id == document.id))
    assert len(page_result.scalars().all()) == 1


@pytest.mark.asyncio
async def test_failed_reindex_after_ocr_preserves_existing_chunks(
    session_and_settings,
    monkeypatch,
):
    session, settings = session_and_settings
    document = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Previously indexed note",
        content="Original indexed content survives embedding failure.",
    )
    await _attach_source_file(
        document,
        session,
        settings,
        "embedding-failure-note.txt",
        "Original indexed content survives embedding failure.",
    )

    def extract_pages(self, **_kwargs):
        return [OcrPage(page_number=1, text="Replacement content", confidence=1.0)]

    async def fail_embeddings(self, contents):
        raise RuntimeError("embedding failed")

    monkeypatch.setattr("hospital_ai.services.ocr.OcrService.extract_pages", extract_pages)
    monkeypatch.setattr(
        "hospital_ai.services.embeddings.EmbeddingService.embed_many",
        fail_embeddings,
    )
    await process_document(session, document.id, settings)

    refreshed = await session.get(Document, document.id)
    assert refreshed.status == "indexed"
    assert refreshed.ocr_error == "embedding failed"
    assert refreshed.index_generation == 0

    chunk_result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document.id))
    chunks = list(chunk_result.scalars().all())
    assert len(chunks) == 1
    assert chunks[0].content == "Original indexed content survives embedding failure."


@pytest.mark.asyncio
async def test_failed_reindex_for_changed_source_marks_index_failed(
    session_and_settings,
    tmp_path: Path,
    monkeypatch,
):
    session, settings = session_and_settings
    storage_file = _storage_file(settings, "changed-note.txt")
    storage_file.write_text("Original file content.", encoding="utf-8")
    document = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Changed source note",
        content="Original indexed content should become stale.",
    )
    document.storage_uri = str(storage_file)
    source_hash = hashlib.sha256(storage_file.read_bytes()).hexdigest()
    document.indexed_source_sha256 = source_hash
    await session.commit()

    storage_file.write_text("Replacement file content.", encoding="utf-8")

    async def fail_embeddings(self, contents):
        raise RuntimeError("embedding failed")

    monkeypatch.setattr(
        "hospital_ai.services.embeddings.EmbeddingService.embed_many",
        fail_embeddings,
    )
    await process_document(session, document.id, settings)

    refreshed = await session.get(Document, document.id)
    assert refreshed.status == "index_failed"
    assert refreshed.ocr_error == "embedding failed"
    assert refreshed.index_generation == 0

    chunk_result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document.id))
    chunks = list(chunk_result.scalars().all())
    assert len(chunks) == 1
    assert chunks[0].content == "Original indexed content should become stale."

    results = await RetrievalService(session).search(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        query_embedding=deterministic_embedding("Original indexed content"),
        top_k=5,
    )
    assert results == []


@pytest.mark.asyncio
async def test_failed_reindex_with_unknown_source_hash_marks_index_failed(
    session_and_settings,
    monkeypatch,
):
    session, settings = session_and_settings
    document = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Unknown source note",
        content="Original indexed content should not be trusted without a source hash.",
    )
    document.storage_uri = "missing-source.txt"
    document.indexed_source_sha256 = None
    await session.commit()

    def fail_ocr(self, **_kwargs):
        raise RuntimeError("ocr failed")

    monkeypatch.setattr("hospital_ai.services.ocr.OcrService.extract_pages", fail_ocr)
    await process_document(session, document.id, settings)

    refreshed = await session.get(Document, document.id)
    assert refreshed.status == "ocr_failed"
    assert refreshed.ocr_error == "ocr failed"


@pytest.mark.asyncio
async def test_embedding_count_mismatch_marks_index_failed(session_and_settings, monkeypatch):
    session, settings = session_and_settings
    storage_file = _storage_file(settings, "embedding-count-note.txt")
    storage_file.write_text("Replacement content needs one embedding.", encoding="utf-8")
    document = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Embedding count note",
        document_type="clinical_note",
        storage_uri=str(storage_file),
        mime_type="text/plain",
        status="uploaded",
    )
    session.add(document)
    await session.commit()

    async def return_no_embeddings(self, contents):
        list(contents)
        return []

    monkeypatch.setattr(
        "hospital_ai.services.embeddings.EmbeddingService.embed_many",
        return_no_embeddings,
    )
    await process_document(session, document.id, settings)

    refreshed = await session.get(Document, document.id)
    assert refreshed.status == "index_failed"
    assert "Embedding count mismatch" in refreshed.ocr_error

    chunk_result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document.id))
    assert chunk_result.scalars().all() == []


@pytest.mark.asyncio
async def test_stale_reindex_attempt_does_not_overwrite_newer_generation(
    session_and_settings,
    monkeypatch,
):
    session, settings = session_and_settings
    document = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Concurrent indexed note",
        content="Original generation content remains authoritative.",
    )
    document_id = document.id

    def extract_pages(self, **_kwargs):
        return [OcrPage(page_number=1, text="Stale replacement content", confidence=1.0)]

    async def simulate_newer_index(self, contents):
        texts = list(contents)
        await session.execute(
            update(Document).where(Document.id == document_id).values(index_generation=Document.index_generation + 1)
        )
        await session.commit()
        return [deterministic_embedding(text) for text in texts]

    monkeypatch.setattr("hospital_ai.services.ocr.OcrService.extract_pages", extract_pages)
    monkeypatch.setattr(
        "hospital_ai.services.embeddings.EmbeddingService.embed_many",
        simulate_newer_index,
    )
    await process_document(session, document_id, settings)

    refreshed = await session.get(Document, document_id)
    assert refreshed.status == "indexed"
    assert refreshed.index_generation == 1
    assert refreshed.ocr_error is None

    chunk_result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id))
    chunks = list(chunk_result.scalars().all())
    assert len(chunks) == 1
    assert chunks[0].content == "Original generation content remains authoritative."
