from __future__ import annotations

import asyncio
import hashlib
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Optional, Protocol
from urllib.parse import urlsplit

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import ValidationAppError

SAFE_NAME_PATTERN = re.compile(r"[^a-zA-Z0-9._-]+")
R2_SCHEME = "r2"


@dataclass(frozen=True)
class StorageObjectHead:
    key: str
    byte_size: int
    etag: str
    content_type: Optional[str]


@dataclass(frozen=True)
class PresignedPut:
    url: str
    required_headers: dict[str, str]


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

    def create_presigned_put(self, *, key: str, content_type: str, expires_seconds: int) -> PresignedPut: ...

    def head_object(self, key: str) -> StorageObjectHead: ...

    def read_stream(self, key: str) -> BinaryIO: ...

    def delete_object(self, key: str) -> None: ...


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
            validated_uri = validate_storage_object_key(storage_uri, allowed_prefixes=("source/", "patients/"))
            candidate = root / validated_uri
        resolved = candidate.resolve()
        if not resolved.is_relative_to(root):
            raise ValueError("Storage URI points outside the configured local storage root.")
        return resolved

    def create_presigned_put(self, *, key: str, content_type: str, expires_seconds: int) -> PresignedPut:
        validated_key = validate_storage_object_key(key, allowed_prefixes=("source/", "patients/"))
        root = os.path.realpath(os.fspath(self.root))
        target = os.path.realpath(os.path.join(root, validated_key))
        if target != root and not target.startswith(root + os.sep):
            raise ValueError("Storage URI points outside the configured local storage root.")
        target_path = Path(target)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        return PresignedPut(
            url=f"local://{validated_key}",
            required_headers={"Content-Type": content_type, "If-None-Match": "*"},
        )

    def head_object(self, key: str) -> StorageObjectHead:
        validated_key = validate_storage_object_key(key, allowed_prefixes=("source/", "patients/"))
        root = os.path.realpath(os.fspath(self.root))
        target = os.path.realpath(os.path.join(root, validated_key))
        if target != root and not target.startswith(root + os.sep):
            raise ValueError("Storage URI points outside the configured local storage root.")
        target_path = Path(target)
        if not target_path.exists():
            raise FileNotFoundError("Storage object not found.")
        return StorageObjectHead(
            key=validated_key,
            byte_size=target_path.stat().st_size,
            etag='"local-etag"',
            content_type=None,
        )

    def read_stream(self, key: str) -> BinaryIO:
        validated_key = validate_storage_object_key(key, allowed_prefixes=("source/", "patients/"))
        target_path = self._resolve_local_path(validated_key)
        return target_path.open("rb")

    def delete_object(self, key: str) -> None:
        validated_key = validate_storage_object_key(key, allowed_prefixes=("source/", "patients/"))
        target_path = self._resolve_local_path(validated_key)
        target_path.unlink(missing_ok=True)


class R2StorageService:
    def __init__(self, settings: Settings, *, client: Optional[Any] = None) -> None:
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

    def create_presigned_put(self, *, key: str, content_type: str, expires_seconds: int) -> PresignedPut:
        validate_storage_object_key(key, allowed_prefixes=("source/", "patients/"))
        url = self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_seconds,
        )
        return PresignedPut(
            url=url,
            required_headers={"Content-Type": content_type, "If-None-Match": "*"},
        )

    def head_object(self, key: str) -> StorageObjectHead:
        validate_storage_object_key(key, allowed_prefixes=("source/", "patients/"))
        try:
            row = self.client.head_object(Bucket=self.bucket, Key=key)
            return StorageObjectHead(
                key=key, byte_size=int(row["ContentLength"]), etag=str(row["ETag"]), content_type=row.get("ContentType")
            )
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if code in {"404", "NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
                raise FileNotFoundError("Storage object not found.") from exc
            raise

    def read_stream(self, key: str) -> BinaryIO:
        validate_storage_object_key(key, allowed_prefixes=("source/", "patients/"))
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            body = response["Body"]
            return body
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if code in {"404", "NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
                raise FileNotFoundError("Storage object not found.") from exc
            raise

    def delete_object(self, key: str) -> None:
        validate_storage_object_key(key, allowed_prefixes=("source/", "patients/"))
        self.client.delete_object(Bucket=self.bucket, Key=key)


def parse_r2_uri(storage_uri: str) -> str:
    parsed = urlsplit(storage_uri)
    if parsed.scheme != R2_SCHEME or parsed.query or parsed.fragment:
        raise ValueError("Storage URI must be an r2:// URI without query or fragment.")

    key = f"{parsed.netloc}{parsed.path}"
    return validate_storage_object_key(key, allowed_prefixes=("source/", "patients/"))


def validate_storage_object_key(key: str, *, allowed_prefixes: tuple[str, ...] = ()) -> str:
    """Validate a storage key before it reaches a local or remote backend."""
    if not isinstance(key, str) or not key or key.startswith(("/", "\\")):
        raise ValueError("Storage object key must be a non-empty relative path.")
    if "\\" in key or (len(key) >= 2 and key[1] == ":"):
        raise ValueError("Storage object key must not contain a drive or backslash.")
    if any(ord(char) < 32 for char in key):
        raise ValueError("Storage object key contains an unsafe character.")
    parts = key.split("/")
    if any(not part or part in {".", ".."} for part in parts):
        raise ValueError("Storage object key contains an unsafe path segment.")
    if allowed_prefixes and not any(key.startswith(prefix) for prefix in allowed_prefixes):
        raise ValueError("Storage object key uses an unexpected prefix.")
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
