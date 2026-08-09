import uuid
from unittest.mock import Mock

import pytest

from hospital_ai.core.errors import ConflictError, ValidationAppError


@pytest.mark.asyncio
async def test_unverified_upload_cannot_be_finalized_or_queued(session_and_settings) -> None:
    session, settings = session_and_settings
    from hospital_ai.services.upload_sessions import UploadSessionService

    r2_client = Mock()
    actor = Mock()
    actor.id = uuid.uuid4()
    actor.role = "doctor"
    patient_id = uuid.uuid4()

    created = await UploadSessionService(session, r2_client).create(
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
        await UploadSessionService(session, r2_client).finalize(created.document_id, created.upload_id)

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
        await UploadSessionService(session, r2_client).create(
            actor=actor,
            patient_id=uuid.uuid4(),
            filename="scan.pdf",
            expected_size=12,
            expected_sha256="a" * 64,
            claimed_mime_type="application/pdf",
            idempotency_key="upload-1",
        )


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
