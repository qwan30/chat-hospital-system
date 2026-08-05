from __future__ import annotations

import hashlib
import io
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from hospital_ai.core.config import Settings
from hospital_ai.services.storage import LocalStorageService, R2StorageService, get_storage_service


class _FakeS3:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.put_calls: list[Mapping[str, Any]] = []

    def put_object(self, **kwargs: Any) -> None:
        self.put_calls.append(kwargs)
        body = kwargs["Body"]
        self.objects[kwargs["Key"]] = body if isinstance(body, bytes) else body.read()

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        assert Bucket == "hospital-documents"
        return {"Body": io.BytesIO(self.objects[Key])}

    def generate_presigned_url(self, operation: str, Params: dict[str, Any], ExpiresIn: int) -> str:
        return f"https://presigned.r2/{Params['Key']}?expires={ExpiresIn}"

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        if Key not in self.objects:
            from botocore.exceptions import ClientError

            raise ClientError({"Error": {"Code": "404"}}, "head_object")
        return {"ContentLength": len(self.objects[Key]), "ETag": '"etag"', "ContentType": "application/pdf"}


def _r2_settings() -> Settings:
    return Settings(
        storage_backend="r2",
        r2_endpoint="https://account.r2.cloudflarestorage.com",
        r2_bucket="hospital-documents",
        r2_region="auto",
        r2_access_key_id="test-access",
        r2_secret_access_key="test-secret",
    )


@pytest.mark.asyncio
async def test_local_storage_upload_remains_readable(tmp_path: Path) -> None:
    settings = Settings(storage_root=tmp_path / "storage")
    storage = LocalStorageService(settings)
    payload = b"local document"
    upload = UploadFile(
        filename="note.txt",
        file=io.BytesIO(payload),
        headers=Headers({"content-type": "text/plain"}),
    )

    uri = await storage.save_upload(patient_id=uuid.uuid4(), document_id=uuid.uuid4(), file=upload)

    assert Path(uri).read_bytes() == payload
    assert storage.read_bytes(uri) == payload
    assert storage.source_sha256(uri) == hashlib.sha256(payload).hexdigest()


@pytest.mark.asyncio
async def test_r2_upload_read_and_source_fingerprint() -> None:
    client = _FakeS3()
    storage = R2StorageService(_r2_settings(), client=client)
    payload = b"r2 document bytes"
    upload = UploadFile(
        filename="clinical note.txt",
        file=io.BytesIO(payload),
        headers=Headers({"content-type": "text/plain"}),
    )

    uri = await storage.save_upload(patient_id="patient-1", document_id="document-1", file=upload)

    assert uri.startswith("r2://patients/patient-1/documents/document-1/")
    assert storage.read_bytes(uri) == payload
    assert storage.source_sha256(uri) == hashlib.sha256(payload).hexdigest()
    assert client.put_calls[0]["Bucket"] == "hospital-documents"
    assert client.put_calls[0]["Body"] == payload
    assert client.put_calls[0]["ContentType"] == "text/plain"


def test_r2_page_png_round_trip() -> None:
    client = _FakeS3()
    storage = R2StorageService(_r2_settings(), client=client)
    page_png = b"\x89PNG\r\n\x1a\nsynthetic-page"

    uri = storage.save_page_image("patient-1", "document-1", 2, page_png)

    assert uri == "r2://patients/patient-1/documents/document-1/pages/2.png"
    assert storage.read_page_image("patient-1", "document-1", 2) == page_png
    assert client.put_calls[0]["ContentType"] == "image/png"


def test_storage_factory_selects_local_and_r2(monkeypatch: pytest.MonkeyPatch) -> None:
    assert isinstance(get_storage_service(Settings()), LocalStorageService)

    fake = _FakeS3()
    monkeypatch.setattr("hospital_ai.services.storage.boto3.client", lambda *_, **__: fake)
    assert isinstance(get_storage_service(_r2_settings()), R2StorageService)


def test_r2_requires_all_connection_settings() -> None:
    with pytest.raises(ValueError, match="R2 storage requires"):
        R2StorageService(Settings(storage_backend="r2"), client=_FakeS3())


def test_r2_presigned_put_and_head_object() -> None:
    client = _FakeS3()
    storage = R2StorageService(_r2_settings(), client=client)
    put_res = storage.create_presigned_put(
        key="patients/test/file.pdf", content_type="application/pdf", expires_seconds=300
    )
    assert "https://presigned.r2/patients/test/file.pdf" in put_res.url
    assert put_res.required_headers == {"Content-Type": "application/pdf", "If-None-Match": "*"}

    with pytest.raises(FileNotFoundError):
        storage.head_object("patients/test/file.pdf")

    client.objects["patients/test/file.pdf"] = b"test content"
    head = storage.head_object("patients/test/file.pdf")
    assert head.byte_size == 12
    assert head.etag == '"etag"'
