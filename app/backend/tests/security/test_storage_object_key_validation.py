from __future__ import annotations

import io

import pytest

from hospital_ai.core.errors import ValidationAppError
from hospital_ai.services.storage import validate_storage_object_key


@pytest.mark.parametrize(
    "key",
    [
        "",
        "/absolute/file.pdf",
        "C:/absolute/file.pdf",
        "source/../secret.pdf",
        "source//missing-segment.pdf",
        "source\\patient\\file.pdf",
    ],
)
def test_storage_object_key_rejects_unsafe_paths(key: str) -> None:
    with pytest.raises(ValueError):
        validate_storage_object_key(key, allowed_prefixes=("source/", "patients/"))


def test_storage_object_key_rejects_unexpected_prefix() -> None:
    with pytest.raises(ValueError):
        validate_storage_object_key("tmp/file.pdf", allowed_prefixes=("source/", "patients/"))


def test_storage_object_key_accepts_generated_source_key() -> None:
    key = "source/patient/document/upload/original.pdf"

    assert validate_storage_object_key(key, allowed_prefixes=("source/", "patients/")) == key


from hospital_ai.services.upload_sessions import StorageContentReader
import asyncio
from unittest.mock import Mock

@pytest.mark.asyncio
async def test_hash_stream_rejects_unreadable_stream() -> None:
    class BrokenStream:
        def read(self) -> bytes:
            raise OSError("read failed")

    storage = Mock()
    storage.read_stream.return_value = BrokenStream()
    reader = StorageContentReader(storage)

    with pytest.raises(ValidationAppError, match="read"):
        await reader.hash_and_sniff("key")


@pytest.mark.asyncio
async def test_unknown_magic_bytes_are_rejected() -> None:
    storage = Mock()
    storage.read_stream.return_value = io.BytesIO(b"not a supported document")
    reader = StorageContentReader(storage)
    with pytest.raises(ValidationAppError, match="MIME"):
        await reader.hash_and_sniff("key")


@pytest.mark.asyncio
async def test_hash_stream_derives_digest_and_size_from_bytes() -> None:
    storage = Mock()
    storage.read_stream.return_value = io.BytesIO(b"%PDF-1.7\ncontent")
    reader = StorageContentReader(storage)
    result = await reader.hash_and_sniff("key")

    assert result.byte_size == 16
    assert result.sha256
