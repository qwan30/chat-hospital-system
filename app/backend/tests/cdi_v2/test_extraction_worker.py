from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from pathlib import Path

import pytest
from sqlalchemy import select

from hospital_ai.core.config import Settings
from hospital_ai.db.clinical_documents import (
    DocumentExtractionRun,
    DocumentPageRevision,
    DocumentUpload,
    OcrSpan,
)
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage, User
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
    compatibility_pages = list(
        await session.scalars(select(DocumentPage).where(DocumentPage.document_id == finalized_document.id))
    )
    assert revisions and all(row.revision_type == "machine_ocr" for row in revisions)
    assert chunks == []
    assert len(compatibility_pages) == 1
    assert compatibility_pages[0].page_number == 1
    assert compatibility_pages[0].ocr_text == "Extracted text"
    assert float(compatibility_pages[0].ocr_confidence) == 0.95
    assert (await session.get(Document, finalized_document.id)).status == "review_required"

    run = await session.scalar(
        select(DocumentExtractionRun).where(DocumentExtractionRun.document_id == finalized_document.id)
    )
    assert run is not None
    assert run.latency_ms == 100
    assert run.peak_rss_mb == 200
    assert run.engine_family == "paddle_printed"
    assert run.engine_model == "v4"
    assert run.engine_revision == "r1"

    spans = list(await session.scalars(select(OcrSpan).where(OcrSpan.page_revision_id == revisions[0].id)))
    assert spans[0].source_engine_metadata == {
        "family": "paddle_printed",
        "model": "v4",
        "revision": "r1",
    }


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
    assert run.error_code == "SOURCE_HASH_DRIFT"
    assert (await session.get(Document, finalized_document.id)).status == "failed"
    assert not list(
        await session.scalars(
            select(DocumentPageRevision).where(DocumentPageRevision.document_id == finalized_document.id)
        )
    )


@pytest.mark.asyncio
async def test_extraction_fails_closed_on_missing_source_object(finalized_document, session_and_settings):
    session, settings = session_and_settings
    source_path = Path(finalized_document.storage_uri)
    source_path.unlink(missing_ok=True)

    await extract_document(session, finalized_document.id, settings)

    run = await session.scalar(
        select(DocumentExtractionRun).where(DocumentExtractionRun.document_id == finalized_document.id)
    )
    assert run is not None and run.status == "failed"
    assert run.error_code == "MISSING_SOURCE_OBJECT"
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


@pytest.mark.asyncio
async def test_one_ocr_model_acquisition_at_a_time_on_4gb_profile(tmp_path: Path) -> None:
    path_a = tmp_path / "model_a.bin"
    path_b = tmp_path / "model_b.bin"
    path_a.write_bytes(b"model a content")
    path_b.write_bytes(b"model b content")

    art_a = ModelArtifact(
        route="paddle_printed",
        path=str(path_a),
        sha256=hashlib.sha256(b"model a content").hexdigest(),
        revision="r1",
    )
    art_b = ModelArtifact(
        route="vietocr_handwritten",
        path=str(path_b),
        sha256=hashlib.sha256(b"model b content").hexdigest(),
        revision="r1",
    )
    manager = OcrModelManager(
        registry=ModelRegistry({"paddle_printed": art_a, "vietocr_handwritten": art_b}),
        memory_budget_mb=4096,
    )

    async with manager.acquire_model("paddle_printed") as model_a:
        assert model_a.route == "paddle_printed"
    assert "paddle_printed" in manager._loaded

    async with manager.acquire_model("vietocr_handwritten") as model_b:
        assert model_b.route == "vietocr_handwritten"
        assert "paddle_printed" not in manager._loaded
        assert len(manager._loaded) == 1


@pytest.mark.asyncio
async def test_idle_unload_cancellation_on_reuse(tmp_path: Path) -> None:
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
        idle_unload_seconds=0.05,
    )

    async with manager.acquire_model("native") as recognizer:
        assert recognizer.route == "native"
    assert "native" in manager._loaded

    await asyncio.sleep(0.025)
    assert "native" in manager._loaded

    async with manager.acquire_model("native") as recognizer2:
        assert recognizer2.route == "native"

    await asyncio.sleep(0.035)
    assert "native" in manager._loaded
    await asyncio.sleep(0.045)
    assert "native" not in manager._loaded


@pytest.mark.asyncio
async def test_approved_artifact_manifest_from_settings(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    model_path = tmp_path / "test.model"
    model_path.write_bytes(b"approved content")
    sha = hashlib.sha256(b"approved content").hexdigest()

    manifest_data = {
        "models": {
            "test_route": {
                "path": str(model_path),
                "sha256": sha,
                "revision": "test-r1",
            }
        }
    }
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    settings = Settings(environment="local")
    settings.ocr_model_manifest_path = manifest_path

    manager = OcrModelManager.from_settings(settings)
    async with manager.acquire_model("test_route") as recognizer:
        assert recognizer.route == "test_route"
        assert recognizer.artifact.revision == "test-r1"


@pytest.mark.asyncio
async def test_deterministic_fallback_policy_and_telemetry(tmp_path: Path) -> None:
    path_native = tmp_path / "native.model"
    path_native.write_bytes(b"native content")
    artifact_oom = ModelArtifact(
        route="force_oom",
        path=str(path_native),
        sha256=hashlib.sha256(b"native content").hexdigest(),
        revision="oom-r1",
    )
    artifact_native = ModelArtifact(
        route="native",
        path=str(path_native),
        sha256=hashlib.sha256(b"native content").hexdigest(),
        revision="native-r1",
    )
    manager = OcrModelManager(registry=ModelRegistry({"force_oom": artifact_oom, "native": artifact_native}))

    async with manager.acquire_model_with_fallback("force_oom") as recognizer:
        assert recognizer.route == "native"

    assert len(manager.telemetry.oom_events) == 1
    assert manager.telemetry.oom_events[0]["route"] == "force_oom"
    assert len(manager.telemetry.fallback_events) == 1
    assert manager.telemetry.fallback_events[0]["from_route"] == "force_oom"
    assert manager.telemetry.fallback_events[0]["to_route"] == "native"
