import re
import uuid
from pathlib import Path
from typing import BinaryIO

from fastapi import UploadFile

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import ValidationAppError

SAFE_NAME_PATTERN = re.compile(r"[^a-zA-Z0-9._-]+")


class LocalStorageService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.root = settings.storage_root

    async def save_upload(
        self,
        *,
        patient_id: uuid.UUID,
        document_id: uuid.UUID,
        file: UploadFile,
    ) -> str:
        filename = sanitize_filename(file.filename or "document.bin")
        target_dir = self.root / "patients" / str(patient_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{document_id}_{filename}"

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

    def open_binary(self, storage_uri: str) -> BinaryIO:
        return Path(storage_uri).open("rb")

    def read_bytes(self, storage_uri: str) -> bytes:
        return Path(storage_uri).read_bytes()


def sanitize_filename(filename: str) -> str:
    sanitized = SAFE_NAME_PATTERN.sub("_", filename.strip()).strip("._")
    return sanitized or "document.bin"
