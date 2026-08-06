import re

with open("app/backend/tests/cdi_v2/test_upload_sessions.py", "a") as f:
    f.write("""

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

    content = b"%PDF-short\\n"
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

    content = b"%PDF-1.4\\n"
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

    content = b"%PDF-1.4\\n"
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
""")
