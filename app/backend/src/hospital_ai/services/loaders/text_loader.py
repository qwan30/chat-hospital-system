"""Plain text and markdown loader.
Bộ nạp tệp văn bản thuần (Plain text) và Markdown (.txt, .md, .log, .csv, ...).
"""

from __future__ import annotations

from pathlib import Path

from hospital_ai.services.loaders.base import BaseDocumentLoader, LoadedPage


class TextLoader(BaseDocumentLoader):
    """Load plain text and markdown files.
    Bộ nạp chuyên dụng đọc tệp văn bản thuần, markdown, log, hoặc cấu hình.
    """

    def supported_extensions(self) -> set[str]:
        """Trả về tập hợp đuôi mở rộng hỗ trợ (.txt, .md, .text, .log, .csv, .json, .xml, .yaml, .yml)."""
        return {".txt", ".md", ".text", ".log", ".csv", ".json", ".xml", ".yaml", ".yml"}

    def load(self, file_path: Path, mime_type: str = "") -> list[LoadedPage]:
        """Đọc toàn bộ văn bản trong tệp với bảng mã UTF-8 (thay thế ký tự lỗi nếu có) và trả về LoadedPage."""
        text = file_path.read_text(encoding="utf-8", errors="replace")
        return [LoadedPage(page_number=1, text=text, confidence=1.0)]
