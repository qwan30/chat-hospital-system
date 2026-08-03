from __future__ import annotations

import asyncio
import hashlib
import re
import uuid
from pathlib import Path
from typing import Any, BinaryIO, Protocol
from urllib.parse import urlsplit

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import ValidationAppError

SAFE_NAME_PATTERN = re.compile(r"[^a-zA-Z0-9._-]+")
R2_SCHEME = "r2"


class StorageService(Protocol):
    async def save_upload(
        self,
        *,
        patient_id: uuid.UUID | str,
        document_id: uuid.UUID | str,
        file: UploadFile,
    ) -> str: ...

    def read_bytes(self, storage_uri: str) -> bytes: ...

    def source_sha256(self, storage_uri: str) -> str: ...

    def save_page_image(
        self,
        patient_id: uuid.UUID | str,
        document_id: uuid.UUID | str,
        page_number: int,
        image_bytes: bytes,
    ) -> str: ...

    def read_page_image(
        self,
        patient_id: uuid.UUID | str,
        document_id: uuid.UUID | str,
        page_number: int,
    ) -> bytes: ...


class LocalStorageService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.root = settings.storage_root

    async def save_upload(
        self,
        *,
        patient_id: uuid.UUID | str,
        document_id: uuid.UUID | str,
        file: UploadFile,
    ) -> str:
        filename = sanitize_filename(file.filename or "document.bin")
        target_dir = self.root / "patients" / _key_segment(patient_id, "patient_id")
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{_key_segment(document_id, 'document_id')}_{filename}"

        size = 0
        with target_path.open("wb") as output:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > self.settings.max_upload_bytes:
                    target_path.unlink(missing_ok=True)
                    raise ValidationAppError("Uploaded file exceeds the configured size limit.")
                output.write(chunk)
        return str(target_path)

    def save_page_image(
        self,
        patient_id: uuid.UUID | str,
        document_id: uuid.UUID | str,
        page_number: int,
        image_bytes: bytes,
    ) -> str:
        target_path = self.get_page_image_path(patient_id, document_id, page_number)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(image_bytes)
        return str(target_path)

    def get_page_image_path(
        self,
        patient_id: uuid.UUID | str,
        document_id: uuid.UUID | str,
        page_number: int,
    ) -> Path:
        _validate_page_number(page_number)
        return (
            self.root
            / "patients"
            / _key_segment(patient_id, "patient_id")
            / "pages"
            / f"{_key_segment(document_id, 'document_id')}_{page_number}.png"
        )

    def open_binary(self, storage_uri: str) -> BinaryIO:
        return self._resolve_local_path(storage_uri).open("rb")

    def read_bytes(self, storage_uri: str) -> bytes:
        return self._resolve_local_path(storage_uri).read_bytes()

    def source_sha256(self, storage_uri: str) -> str:
        return hashlib.sha256(self.read_bytes(storage_uri)).hexdigest()

    def read_page_image(
        self,
        patient_id: uuid.UUID | str,
        document_id: uuid.UUID | str,
        page_number: int,
    ) -> bytes:
        return self.get_page_image_path(patient_id, document_id, page_number).read_bytes()

    def _resolve_local_path(self, storage_uri: str) -> Path:
        if storage_uri.startswith(("r2://", "hms://", "local://")):
            raise ValueError("The local storage backend cannot read this storage URI.")

        root = self.root.resolve()
        candidate = Path(storage_uri)
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        resolved = candidate.resolve()
        if not resolved.is_relative_to(root):
            raise ValueError("Storage URI points outside the configured local storage root.")
        return resolved


class R2StorageService:
    def __init__(self, settings: Settings, *, client: Any | None = None) -> None:
        self.settings = settings
        missing = [
            name
            for name, value in (
                ("endpoint", settings.r2_endpoint),
                ("bucket", settings.r2_bucket),
                ("access key", settings.r2_access_key_id),
                ("secret key", settings.r2_secret_access_key),
            )
            if not value.strip()
        ]
        if missing:
            raise ValueError(f"R2 storage requires: {', '.join(missing)}.")

        self.bucket = settings.r2_bucket
        self.client = (
            client
            if client is not None
            else boto3.client(
                "s3",
                endpoint_url=settings.r2_endpoint,
                region_name=settings.r2_region,
                aws_access_key_id=settings.r2_access_key_id,
                aws_secret_access_key=settings.r2_secret_access_key,
            )
        )

    async def save_upload(
        self,
        *,
        patient_id: uuid.UUID | str,
        document_id: uuid.UUID | str,
        file: UploadFile,
    ) -> str:
        filename = sanitize_filename(file.filename or "document.bin")
        chunks: list[bytes] = []
        size = 0
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > self.settings.max_upload_bytes:
                raise ValidationAppError("Uploaded file exceeds the configured size limit.")
            chunks.append(chunk)

        key = _document_key(patient_id, document_id, filename)
        await asyncio.to_thread(
            self.client.put_object,
            Bucket=self.bucket,
            Key=key,
            Body=b"".join(chunks),
            ContentType=file.content_type or "application/octet-stream",
        )
        return _r2_uri(key)

    def read_bytes(self, storage_uri: str) -> bytes:
        key = parse_r2_uri(storage_uri)
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            body = response["Body"]
            return body if isinstance(body, bytes) else body.read()
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if code in {"404", "NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
                raise FileNotFoundError("Storage object not found.") from exc
            raise

    def source_sha256(self, storage_uri: str) -> str:
        return hashlib.sha256(self.read_bytes(storage_uri)).hexdigest()

    def save_page_image(
        self,
        patient_id: uuid.UUID | str,
        document_id: uuid.UUID | str,
        page_number: int,
        image_bytes: bytes,
    ) -> str:
        _validate_page_number(page_number)
        key = _page_key(patient_id, document_id, page_number)
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=image_bytes,
            ContentType="image/png",
        )
        return _r2_uri(key)

    def read_page_image(
        self,
        patient_id: uuid.UUID | str,
        document_id: uuid.UUID | str,
        page_number: int,
    ) -> bytes:
        return self.read_bytes(_r2_uri(_page_key(patient_id, document_id, page_number)))


def parse_r2_uri(storage_uri: str) -> str:
    parsed = urlsplit(storage_uri)
    if parsed.scheme != R2_SCHEME or parsed.query or parsed.fragment:
        raise ValueError("Storage URI must be an r2:// URI without query or fragment.")

    key = f"{parsed.netloc}{parsed.path}"
    parts = key.split("/")
    if (
        not key
        or key.startswith(("/", "\\"))
        or "\\" in key
        or any(not part or part in {".", ".."} for part in parts)
        or any(ord(char) < 32 for char in key)
    ):
        raise ValueError("R2 storage URI contains an unsafe object key.")
    return key


def get_storage_service(settings: Settings) -> StorageService:
    backend = settings.storage_backend.strip().lower()
    if backend == "local":
        return LocalStorageService(settings)
    if backend == "r2":
        return R2StorageService(settings)
    raise ValueError(f"Unsupported storage backend: {settings.storage_backend!r}.")


def _document_key(patient_id: uuid.UUID | str, document_id: uuid.UUID | str, filename: str) -> str:
    return (
        f"patients/{_key_segment(patient_id, 'patient_id')}/"
        f"documents/{_key_segment(document_id, 'document_id')}/{sanitize_filename(filename)}"
    )


def _page_key(patient_id: uuid.UUID | str, document_id: uuid.UUID | str, page_number: int) -> str:
    return (
        f"patients/{_key_segment(patient_id, 'patient_id')}/"
        f"documents/{_key_segment(document_id, 'document_id')}/"
        f"pages/{_validate_page_number(page_number)}.png"
    )


def _r2_uri(key: str) -> str:
    return f"{R2_SCHEME}://{key}"


def _validate_page_number(page_number: int) -> int:
    if page_number < 1:
        raise ValueError("Page number must be positive.")
    return page_number


def _key_segment(value: uuid.UUID | str, field_name: str) -> str:
    segment = str(value)
    if not segment or segment in {".", ".."} or any(char in segment for char in "/\\"):
        raise ValueError(f"{field_name} must be a single storage path segment.")
    if any(ord(char) < 32 for char in segment):
        raise ValueError(f"{field_name} contains an unsafe character.")
    return segment


def sanitize_filename(filename: str) -> str:
    sanitized = SAFE_NAME_PATTERN.sub("_", filename.strip()).strip("._")
    return sanitized or "document.bin"
