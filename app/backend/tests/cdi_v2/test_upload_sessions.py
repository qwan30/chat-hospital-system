from __future__ import annotations

import hashlib
import io
import uuid
from unittest.mock import Mock

import pytest

from hospital_ai.core.errors import ConflictError, ValidationAppError
from hospital_ai.services.upload_sessions import UploadSessionService, StorageContentReader, MalwareScanResult, UnavailableMalwareScanner


@pytest.mark.asyncio
async def test_unverified_upload_cannot_be_finalized_or_queued(session_and_settings) -> None:
    session, settings = session_and_settings
    from hospital_ai.services.storage import PresignedPut
    from hospital_ai.services.upload_sessions import UploadSessionService

    r2_client = Mock()
    r2_client.head_object.side_effect = FileNotFoundError
    r2_client.create_presigned_put.return_value = PresignedPut(
        url="https://presigned", required_headers={"Content-Type": "application/pdf"}
    )
    r2_client.read_stream.return_value = io.BytesIO(b"%PDF-1.4\nx")
    actor = Mock()
    actor.id = uuid.uuid4()
    actor.role = "doctor"
    patient_id = uuid.uuid4()

    service = UploadSessionService(session, r2_client, content_reader=StorageContentReader(r2_client), scanner=_CleanScanner())
    created = await service.create(
        actor=actor,
        patient_id=patient_id,
        filename="scan.pdf",
        expected_size=12,
        expected_sha256="a" * 64,
        claimed_mime_type="application/pdf",
        idempotency_key="upload-1",
    )
    r2_client.head_object.return_value = {"ContentLength": 11, "ETag": '"etag"'}
    with pytest.raises(ValidationAppError):
        await service.finalize(created.document_id, created.upload_id)

    from hospital_ai.db.clinical_documents import DocumentUpload

    assert (await session.get(DocumentUpload, created.upload_id)).state == "rejected"


@pytest.mark.asyncio
async def test_duplicate_immutable_key_is_a_conflict(session_and_settings) -> None:
    session, settings = session_and_settings
    from hospital_ai.services.upload_sessions import UploadSessionService

    r2_client = Mock()
    r2_client.head_object.return_value = {
        "ContentLength": 12,
        "ETag": '"existing"',
        "ContentType": "application/pdf",
    }

    actor = Mock()
    actor.id = uuid.uuid4()
    actor.role = "doctor"

    with pytest.raises(ConflictError):
        await UploadSessionService(session, r2_client, content_reader=StorageContentReader(r2_client), scanner=_CleanScanner()).create(
            actor=actor,
            patient_id=uuid.uuid4(),
            filename="scan.pdf",
            expected_size=12,
            expected_sha256="a" * 64,
            claimed_mime_type="application/pdf",
            idempotency_key="upload-1",
        )


@pytest.mark.asyncio
async def test_malware_scanner_unavailable_rejects_without_finalizing(session_and_settings) -> None:
    session, _ = session_and_settings
    from hospital_ai.db.models import Document
    from hospital_ai.services.storage import PresignedPut
    from hospital_ai.services.upload_sessions import UploadSessionService

    content = b"%PDF-1.4\n"
    storage = Mock()
    storage.head_object.side_effect = FileNotFoundError
    storage.create_presigned_put.return_value = PresignedPut("https://presigned", {})
    storage.read_stream.return_value = io.BytesIO(content)
    actor = Mock(id=uuid.uuid4())
    service = UploadSessionService(session, storage, content_reader=StorageContentReader(storage), scanner=UnavailableMalwareScanner())
    created = await service.create(
        actor=actor,
        patient_id=uuid.uuid4(),
        filename="scan.pdf",
        expected_size=len(content),
        expected_sha256=hashlib.sha256(content).hexdigest(),
        claimed_mime_type="application/pdf",
    )
    from hospital_ai.services.storage import StorageObjectHead

    storage.head_object.side_effect = None
    storage.head_object.return_value = StorageObjectHead(created.object_key, len(content), '"etag"', "application/pdf")

    with pytest.raises(ValidationAppError, match="scanner unavailable"):
        await service.finalize(created.document_id, created.upload_id, actor=actor)

    document = await session.get(Document, created.document_id)
    assert document.finalized_upload_id is None


@pytest.mark.asyncio
async def test_storage_head_error_rejects_upload_session_creation(session_and_settings) -> None:
    session, _ = session_and_settings
    from hospital_ai.services.upload_sessions import UploadSessionService

    storage = Mock()
    storage.head_object.side_effect = OSError("head failed")

    with pytest.raises(ValidationAppError, match="storage object availability"):
        await UploadSessionService(session, storage, content_reader=StorageContentReader(storage), scanner=_CleanScanner()).create(
            patient_id=uuid.uuid4(),
            filename="scan.pdf",
            expected_size=10,
            expected_sha256="a" * 64,
            claimed_mime_type="application/pdf",
        )


@pytest.mark.asyncio
async def test_claimed_mime_mismatch_rejects_without_finalizing(session_and_settings) -> None:
    session, _ = session_and_settings
    from hospital_ai.db.models import Document
    from hospital_ai.services.storage import PresignedPut
    from hospital_ai.services.upload_sessions import UploadSessionService

    content = b"\x89PNG\r\n\x1a\nimage"
    storage = Mock()
    storage.head_object.side_effect = FileNotFoundError
    storage.create_presigned_put.return_value = PresignedPut("https://presigned", {})
    storage.read_stream.return_value = io.BytesIO(content)
    actor = Mock(id=uuid.uuid4())
    service = UploadSessionService(session, storage, content_reader=StorageContentReader(storage), scanner=_CleanScanner())
    created = await service.create(
        actor=actor,
        patient_id=uuid.uuid4(),
        filename="scan.pdf",
        expected_size=len(content),
        expected_sha256=hashlib.sha256(content).hexdigest(),
        claimed_mime_type="application/pdf",
    )
    from hospital_ai.services.storage import StorageObjectHead

    storage.head_object.side_effect = None
    storage.head_object.return_value = StorageObjectHead(created.object_key, len(content), '"etag"', "image/png")

    with pytest.raises(ValidationAppError, match="MIME"):
        await service.finalize(created.document_id, created.upload_id, actor=actor)

    assert (await session.get(Document, created.document_id)).finalized_upload_id is None


@pytest.mark.asyncio
async def test_presign_error_does_not_leave_upload_rows(session_and_settings) -> None:
    session, _ = session_and_settings
    from sqlalchemy import select

    from hospital_ai.db.clinical_documents import DocumentUpload
    from hospital_ai.services.upload_sessions import UploadSessionService

    storage = Mock()
    storage.head_object.side_effect = FileNotFoundError
    storage.create_presigned_put.side_effect = OSError("presign failed")

    with pytest.raises(ValidationAppError, match="upload session"):
        await UploadSessionService(session, storage, content_reader=StorageContentReader(storage), scanner=_CleanScanner()).create(
            patient_id=uuid.uuid4(),
            filename="scan.pdf",
            expected_size=10,
            expected_sha256="a" * 64,
            claimed_mime_type="application/pdf",
        )

    assert (await session.scalars(select(DocumentUpload))).all() == []


def test_presigned_put_requires_conditional_create() -> None:
    from hospital_ai.core.config import Settings
    from hospital_ai.services.storage import R2StorageService

    settings = Settings(
        r2_bucket="test",
        r2_endpoint="https://test",
        r2_access_key_id="test",
        r2_secret_access_key="test",
    )
    r2_storage = R2StorageService(settings)
    r2_storage.client = Mock()
    r2_storage.client.generate_presigned_url.return_value = "https://presigned"

    result = r2_storage.create_presigned_put(
        key="source/patient/document/hash/original.pdf",
        content_type="application/pdf",
        expires_seconds=300,
    )
    assert result.required_headers == {
        "Content-Type": "application/pdf",
        "If-None-Match": "*",
    }


class _CleanScanner:
    async def scan(self, key: str) -> MalwareScanResult:
        return MalwareScanResult(status="clean")


class _CleanScanner:
    async def scan(self, key: str):
        from hospital_ai.services.upload_sessions import MalwareScanResult
        return MalwareScanResult(status="clean")

@pytest.mark.asyncio
async def test_short_stream_rejects_without_finalizing(session_and_settings) -> None:
    session, _ = session_and_settings
    from hospital_ai.services.storage import PresignedPut, StorageObjectHead
    from hospital_ai.services.upload_sessions import UploadSessionService, StorageContentReader
    from hospital_ai.db.models import Document

    content = b"%PDF-short"
    storage = Mock()
    storage.head_object.side_effect = FileNotFoundError
    storage.read_stream.return_value = io.BytesIO(content)
    storage.create_presigned_put.return_value = PresignedPut("https://presigned", {})
    actor = Mock(id=uuid.uuid4())
    service = UploadSessionService(session, storage, content_reader=StorageContentReader(storage), scanner=_CleanScanner())
    created = await service.create(
        actor=actor,
        patient_id=uuid.uuid4(),
        filename="scan.pdf",
        expected_size=1000,
        expected_sha256="a" * 64,
        claimed_mime_type="application/pdf",
    )
    storage.head_object.side_effect = None
    storage.head_object.return_value = StorageObjectHead(created.object_key, 1000, '"etag"', "application/pdf")

    with pytest.raises(ValidationAppError):
        await service.finalize(created.document_id, created.upload_id, actor=actor)

    document = await session.get(Document, created.document_id)
    assert document.finalized_upload_id is None

@pytest.mark.asyncio
async def test_sha_mismatch_rejects_without_finalizing(session_and_settings) -> None:
    session, _ = session_and_settings
    from hospital_ai.services.storage import PresignedPut, StorageObjectHead
    from hospital_ai.services.upload_sessions import UploadSessionService, StorageContentReader
    from hospital_ai.db.models import Document

    content = b"%PDF-short\n"
    storage = Mock()
    storage.head_object.side_effect = FileNotFoundError
    storage.read_stream.return_value = io.BytesIO(content)
    storage.create_presigned_put.return_value = PresignedPut("https://presigned", {})
    actor = Mock(id=uuid.uuid4())
    service = UploadSessionService(session, storage, content_reader=StorageContentReader(storage), scanner=_CleanScanner())
    created = await service.create(
        actor=actor,
        patient_id=uuid.uuid4(),
        filename="scan.pdf",
        expected_size=len(content),
        expected_sha256="a" * 64,
        claimed_mime_type="application/pdf",
    )
    storage.head_object.side_effect = None
    storage.head_object.return_value = StorageObjectHead(created.object_key, len(content), '"etag"', "application/pdf")

    with pytest.raises(ValidationAppError, match="SHA256 mismatch"):
        await service.finalize(created.document_id, created.upload_id, actor=actor)

    document = await session.get(Document, created.document_id)
    assert document.finalized_upload_id is None

@pytest.mark.asyncio
async def test_malware_positive_rejects_without_finalizing(session_and_settings) -> None:
    session, _ = session_and_settings
    from hospital_ai.services.storage import PresignedPut, StorageObjectHead
    from hospital_ai.services.upload_sessions import UploadSessionService, StorageContentReader, MalwareScanResult
    from hospital_ai.db.models import Document

    class MalwareScannerPositive:
        async def scan(self, key: str) -> MalwareScanResult:
            return MalwareScanResult(status="infected")

    content = b"%PDF-1.4\n"
    storage = Mock()
    storage.head_object.side_effect = FileNotFoundError
    storage.read_stream.return_value = io.BytesIO(content)
    storage.create_presigned_put.return_value = PresignedPut("https://presigned", {})
    actor = Mock(id=uuid.uuid4())
    service = UploadSessionService(session, storage, content_reader=StorageContentReader(storage), scanner=MalwareScannerPositive())
    created = await service.create(
        actor=actor,
        patient_id=uuid.uuid4(),
        filename="scan.pdf",
        expected_size=len(content),
        expected_sha256=hashlib.sha256(content).hexdigest(),
        claimed_mime_type="application/pdf",
    )
    storage.head_object.side_effect = None
    storage.head_object.return_value = StorageObjectHead(created.object_key, len(content), '"etag"', "application/pdf")

    with pytest.raises(ValidationAppError, match="Malware detected"):
        await service.finalize(created.document_id, created.upload_id, actor=actor)

    document = await session.get(Document, created.document_id)
    assert document.finalized_upload_id is None

@pytest.mark.asyncio
async def test_retry_of_finalized_upload(session_and_settings) -> None:
    session, _ = session_and_settings
    from hospital_ai.services.storage import PresignedPut, StorageObjectHead
    from hospital_ai.services.upload_sessions import UploadSessionService, StorageContentReader
    from hospital_ai.db.models import Document

    content = b"%PDF-1.4\n"
    storage = Mock()
    storage.head_object.side_effect = FileNotFoundError
    storage.read_stream.return_value = io.BytesIO(content)
    storage.create_presigned_put.return_value = PresignedPut("https://presigned", {})
    actor = Mock(id=uuid.uuid4())
    service = UploadSessionService(session, storage, content_reader=StorageContentReader(storage), scanner=_CleanScanner())
    created = await service.create(
        actor=actor,
        patient_id=uuid.uuid4(),
        filename="scan.pdf",
        expected_size=len(content),
        expected_sha256=hashlib.sha256(content).hexdigest(),
        claimed_mime_type="application/pdf",
    )
    storage.head_object.side_effect = None
    storage.head_object.return_value = StorageObjectHead(created.object_key, len(content), '"etag"', "application/pdf")

    await service.finalize(created.document_id, created.upload_id, actor=actor)
    
    # Retry
    res = await service.finalize(created.document_id, created.upload_id, actor=actor)
    assert res.state == "finalized"
@pytest.mark.asyncio
async def test_concurrent_finalize_handles_safely(session_and_settings) -> None:
    session, _ = session_and_settings
    from hospital_ai.services.storage import PresignedPut, StorageObjectHead
    from hospital_ai.services.upload_sessions import UploadSessionService, StorageContentReader
    from hospital_ai.db.models import Document
    import asyncio

    content = b"%PDF-1.4\n"
    storage = Mock()
    storage.head_object.side_effect = FileNotFoundError
    storage.read_stream.return_value = io.BytesIO(content)
    storage.create_presigned_put.return_value = PresignedPut("https://presigned", {})
    actor = Mock(id=uuid.uuid4())
    service = UploadSessionService(session, storage, content_reader=StorageContentReader(storage), scanner=_CleanScanner())
    
    created = await service.create(
        actor=actor,
        patient_id=uuid.uuid4(),
        filename="scan.pdf",
        expected_size=len(content),
        expected_sha256=hashlib.sha256(content).hexdigest(),
        claimed_mime_type="application/pdf",
    )
    storage.head_object.side_effect = None
    
    original_hash_and_sniff = service.content_reader.hash_and_sniff
    async def delayed_hash_and_sniff(key):
        await asyncio.sleep(0.01)
        storage.read_stream.return_value = io.BytesIO(content)
        return await original_hash_and_sniff(key)
    
    service.content_reader.hash_and_sniff = delayed_hash_and_sniff
    storage.head_object.return_value = StorageObjectHead(created.object_key, len(content), '"etag"', "application/pdf")

    results = await asyncio.gather(
        service.finalize(created.document_id, created.upload_id, actor=actor),
        service.finalize(created.document_id, created.upload_id, actor=actor),
        return_exceptions=True
    )
    
    successes = 0
    for r in results:
        if not isinstance(r, Exception) and getattr(r, "state", None) == "finalized":
            successes += 1
            
    assert successes >= 1, "At least one finalize should succeed"
    
    doc = await session.get(Document, created.document_id)
    assert doc.finalized_upload_id == created.upload_id

