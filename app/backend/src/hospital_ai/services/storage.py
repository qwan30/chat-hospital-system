"""Local file storage management service.
Dịch vụ quản lý và lưu trữ tập tin tài liệu y tế tại chỗ (local filesystem).
"""

import re
import uuid
from pathlib import Path
from typing import BinaryIO

from fastapi import UploadFile

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import ValidationAppError

SAFE_NAME_PATTERN = re.compile(r"[^a-zA-Z0-9._-]+")


class LocalStorageService:
    """Service for managing uploaded documents and rendered OCR page images on disk.
    Dịch vụ lưu trữ disk cho các tập tin tải lên và hình ảnh trang tài liệu sau OCR.
    """

    def __init__(self, settings: Settings) -> None:
        """Khởi tạo LocalStorageService với thư mục gốc `storage_root` từ cấu hình hệ thống Settings."""
        self.settings = settings
        self.root = settings.storage_root

    async def save_upload(
        self,
        *,
        patient_id: uuid.UUID,
        document_id: uuid.UUID,
        file: UploadFile,
    ) -> str:
        """Save an uploaded file asynchronously in streaming chunks, validating against size limits.
        Lưu tập tin tải lên theo từng phần (streaming chunks), kiểm tra giới hạn kích thước tối đa cho phép.
        """
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

    def save_page_image(
        self, patient_id: uuid.UUID, document_id: uuid.UUID, page_number: int, image_bytes: bytes
    ) -> str:
        """Lưu hình ảnh kết xuất của một trang tài liệu (định dạng PNG) xuống thư mục của bệnh nhân."""
        target_dir = self.root / "patients" / str(patient_id) / "pages"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{document_id}_{page_number}.png"
        target_path.write_bytes(image_bytes)
        return str(target_path)

    def get_page_image_path(self, patient_id: uuid.UUID, document_id: uuid.UUID, page_number: int) -> Path:
        """Lấy đối tượng Path chỉ đến tệp hình ảnh của trang tài liệu cụ thể."""
        return self.root / "patients" / str(patient_id) / "pages" / f"{document_id}_{page_number}.png"

    def open_binary(self, storage_uri: str) -> BinaryIO:
        """Mở tệp nhị phân từ URI lưu trữ trên ổ đĩa để đọc (chế độ 'rb')."""
        return Path(storage_uri).open("rb")

    def read_bytes(self, storage_uri: str) -> bytes:
        """Đọc toàn bộ nội dung nhị phân của tệp từ URI lưu trữ."""
        return Path(storage_uri).read_bytes()


def sanitize_filename(filename: str) -> str:
    """Làm sạch tên tệp tải lên, thay thế các ký tự đặc biệt/nguy hiểm bằng dấu gạch dưới `_` để bảo mật đường dẫn."""
    sanitized = SAFE_NAME_PATTERN.sub("_", filename.strip()).strip("._")
    return sanitized or "document.bin"
