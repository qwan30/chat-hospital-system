from __future__ import annotations

import io

import pytest

from hospital_ai.core.errors import ValidationAppError
from hospital_ai.services.storage import validate_storage_object_key
from hospital_ai.services.upload_sessions import hash_stream, sniff_magic_mime


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


def test_hash_stream_rejects_unreadable_stream() -> None:
    class BrokenStream:
        def read(self) -> bytes:
            raise OSError("read failed")

    with pytest.raises(ValidationAppError, match="read"):
        hash_stream(BrokenStream())


def test_unknown_magic_bytes_are_rejected() -> None:
    with pytest.raises(ValidationAppError, match="MIME"):
        sniff_magic_mime(b"not a supported document")


def test_hash_stream_derives_digest_and_size_from_bytes() -> None:
    result = hash_stream(io.BytesIO(b"%PDF-1.7\ncontent"))

    assert result.byte_size == 16
    assert result.sha256
