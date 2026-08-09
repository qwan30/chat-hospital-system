from __future__ import annotations

import asyncio
import hashlib
import uuid
from pathlib import Path

import pytest
from sqlalchemy import select

from hospital_ai.db.clinical_documents import DocumentExtractionRun, DocumentPageRevision, DocumentUpload
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import Document, DocumentChunk, User
from hospital_ai.workers.extraction_jobs import extract_document
from hospital_ai.workers.ocr_models import ModelArtifact, ModelRegistry, OcrModelManager, OcrResourceError


@pytest.fixture
async def finalized_document(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    if not doctor:
        doctor = User(id=uuid.uuid4(), email="doc@test.com", full_name="Doc", role="doctor", is_active=True)
        session.add(doctor)
        await session.commit()

    doc = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id,
        title="Extraction Test Doc",
        document_type="progress_note",
        storage_uri="pending",
        mime_type="application/pdf",
        status="uploaded",
    )
    session.add(doc)
    await session.flush()
    content = b"verified source bytes"
    source_hash = hashlib.sha256(content).hexdigest()
    upload_id = uuid.uuid4()
    object_key = f"source/{PATIENT_ALICE_ID}/{doc.id}/{upload_id}/original.pdf"
    source_path = Path(settings.storage_root) / object_key
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_bytes(content)
    upload = DocumentUpload(
        id=upload_id,
        document_id=doc.id,
        state="finalized",
        object_key=object_key,
        expected_sha256=source_hash,
        byte_size=len(content),
        mime_type="application/pdf",
        actor_user_id=doctor.id,
    )
    session.add(upload)
    doc.finalized_upload_id = upload.id
    doc.storage_uri = str(source_path)
    doc.indexed_source_sha256 = source_hash
    await session.commit()
    return doc


@pytest.mark.asyncio
async def test_extraction_creates_machine_revisions_but_no_chunks(
    session_and_settings, finalized_document, monkeypatch: pytest.MonkeyPatch
) -> None:
    session, settings = session_and_settings

    # Mock file retrieval and OCR pipeline so unit test runs quickly without R2/actual models
    from hospital_ai.services.ocr_routing import OcrPageResult, OcrSpanResult

    async def mock_extract(*args, **kwargs):
        span = OcrSpanResult(
            text="Extracted text",
            start_offset=0,
            end_offset=14,
            polygon=((0.0, 0.0), (10.0, 0.0), (10.0, 5.0), (0.0, 5.0)),
            confidence=0.95,
            reading_order=1,
            engine_family="paddle_printed",
            engine_model="v4",
            engine_revision="r1",
        )
        return [
            OcrPageResult(
                page_number=1,
                raw_text="Extracted text",
                confidence=0.95,
                route="paddle_printed",
                spans=(span,),
                latency_ms=100,
                peak_rss_mb=200,
            )
        ]

    monkeypatch.setattr("hospital_ai.workers.extraction_jobs.ocr_pipeline_extract", mock_extract, raising=False)

    await extract_document(session, finalized_document.id, settings)
    revisions = list(
        await session.scalars(
            select(DocumentPageRevision).where(DocumentPageRevision.document_id == finalized_document.id)
        )
    )
    chunks = list(
        await session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == finalized_document.id))
    )
    assert revisions and all(row.revision_type == "machine_ocr" for row in revisions)
    assert chunks == []
    assert (await session.get(Document, finalized_document.id)).status == "review_required"


@pytest.mark.asyncio
async def test_extraction_skips_document_without_finalized_upload(session_and_settings, monkeypatch) -> None:
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    assert doctor is not None
    document = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id,
        title="Unfinalized document",
        document_type="progress_note",
        storage_uri="pending",
        mime_type="application/pdf",
        status="uploaded",
    )
    session.add(document)
    await session.commit()

    async def fail_if_called(*args, **kwargs):
        raise AssertionError("OCR must not run before finalization")

    monkeypatch.setattr("hospital_ai.workers.extraction_jobs.ocr_pipeline.extract", fail_if_called)
    await extract_document(session, document.id, settings)

    assert (
        await session.scalar(select(DocumentExtractionRun).where(DocumentExtractionRun.document_id == document.id))
        is None
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("upload_state", ["rejected", "quarantined"])
async def test_extraction_skips_non_finalized_upload(
    finalized_document, session_and_settings, upload_state, monkeypatch
):
    session, settings = session_and_settings
    upload = await session.get(DocumentUpload, finalized_document.finalized_upload_id)
    assert upload is not None
    upload.state = upload_state
    await session.commit()

    async def fail_if_called(*args, **kwargs):
        raise AssertionError("OCR must not run for a rejected or quarantined upload")

    monkeypatch.setattr("hospital_ai.workers.extraction_jobs.ocr_pipeline.extract", fail_if_called)
    await extract_document(session, finalized_document.id, settings)

    assert (
        await session.scalar(
            select(DocumentExtractionRun).where(DocumentExtractionRun.document_id == finalized_document.id)
        )
        is None
    )


@pytest.mark.asyncio
async def test_extraction_skips_upload_bound_to_another_document(finalized_document, session_and_settings, monkeypatch):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    assert doctor is not None
    other = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id,
        title="Other document",
        document_type="progress_note",
        storage_uri="pending",
        mime_type="application/pdf",
        status="uploaded",
    )
    session.add(other)
    await session.flush()
    other_upload = DocumentUpload(
        id=uuid.uuid4(),
        document_id=other.id,
        state="finalized",
        object_key="source/other/document/upload/original.pdf",
        expected_sha256="a" * 64,
        byte_size=1,
        mime_type="application/pdf",
        actor_user_id=doctor.id,
    )
    session.add(other_upload)
    finalized_document.finalized_upload_id = other_upload.id
    await session.commit()

    async def fail_if_called(*args, **kwargs):
        raise AssertionError("OCR must not run for a mismatched upload")

    monkeypatch.setattr("hospital_ai.workers.extraction_jobs.ocr_pipeline.extract", fail_if_called)
    await extract_document(session, finalized_document.id, settings)

    assert (
        await session.scalar(
            select(DocumentExtractionRun).where(DocumentExtractionRun.document_id == finalized_document.id)
        )
        is None
    )


@pytest.mark.asyncio
async def test_extraction_fails_closed_on_source_hash_drift(finalized_document, session_and_settings, monkeypatch):
    session, settings = session_and_settings
    source_path = Path(finalized_document.storage_uri)
    source_path.write_bytes(b"tampered source bytes")

    from hospital_ai.services.ocr_routing import OcrPageResult

    monkeypatch.setattr(
        "hospital_ai.services.ocr.OcrService.extract_page_results",
        lambda *args, **kwargs: [
            OcrPageResult(
                page_number=1,
                raw_text="Would otherwise be extracted",
                confidence=1.0,
                route="native",
                spans=(),
                latency_ms=1,
                peak_rss_mb=1,
            )
        ],
    )

    await extract_document(session, finalized_document.id, settings)

    run = await session.scalar(
        select(DocumentExtractionRun).where(DocumentExtractionRun.document_id == finalized_document.id)
    )
    assert run is not None and run.status == "failed"
    assert (await session.get(Document, finalized_document.id)).status == "failed"
    assert not list(
        await session.scalars(
            select(DocumentPageRevision).where(DocumentPageRevision.document_id == finalized_document.id)
        )
    )


@pytest.mark.asyncio
async def test_acquire_model_and_resource_limits(tmp_path: Path) -> None:
    artifact_path = tmp_path / "oom.model"
    artifact_bytes = b"approved model artifact"
    artifact_path.write_bytes(artifact_bytes)
    artifact = ModelArtifact(
        route="force_oom",
        path=str(artifact_path),
        sha256=hashlib.sha256(artifact_bytes).hexdigest(),
        revision="oom-r1",
    )
    manager = OcrModelManager(registry=ModelRegistry({"force_oom": artifact}))
    with pytest.raises(OcrResourceError):
        async with manager.acquire_model("force_oom"):
            pass


@pytest.mark.asyncio
async def test_model_artifact_hash_is_verified_and_idle_unload_is_real(tmp_path: Path) -> None:
    artifact_path = tmp_path / "native.model"
    artifact_bytes = b"approved model artifact"
    artifact_path.write_bytes(artifact_bytes)
    artifact = ModelArtifact(
        route="native",
        path=str(artifact_path),
        sha256=hashlib.sha256(artifact_bytes).hexdigest(),
        revision="native-r1",
    )
    manager = OcrModelManager(
        registry=ModelRegistry({"native": artifact}),
        idle_unload_seconds=0.01,
    )

    async with manager.acquire_model("native") as recognizer:
        assert recognizer.route == "native"
    await asyncio.sleep(0.03)
    assert "native" not in manager._loaded


@pytest.mark.asyncio
async def test_model_oom_is_classified_with_rss_evidence(tmp_path: Path) -> None:
    artifact_path = tmp_path / "oom.model"
    artifact_bytes = b"approved model artifact"
    artifact_path.write_bytes(artifact_bytes)
    artifact = ModelArtifact(
        route="force_oom",
        path=str(artifact_path),
        sha256=hashlib.sha256(artifact_bytes).hexdigest(),
        revision="oom-r1",
    )
    manager = OcrModelManager(registry=ModelRegistry({"force_oom": artifact}))

    with pytest.raises(OcrResourceError):
        async with manager.acquire_model("force_oom"):
            pass
    assert manager.telemetry.oom_events
    assert manager.telemetry.oom_events[0]["route"] == "force_oom"
