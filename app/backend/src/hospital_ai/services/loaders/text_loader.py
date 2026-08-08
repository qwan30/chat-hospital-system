"""Plain text and markdown loader."""

from __future__ import annotations

from pathlib import Path

from hospital_ai.services.loaders.base import BaseDocumentLoader, LoadedPage


class TextLoader(BaseDocumentLoader):
    """Load plain text and markdown files."""

    def supported_extensions(self) -> set[str]:
        return {".txt", ".md", ".text", ".log", ".csv", ".json", ".xml", ".yaml", ".yml"}

    def load(self, file_path: Path, mime_type: str = "") -> list[LoadedPage]:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        return [LoadedPage(page_number=1, text=text, confidence=1.0)]
