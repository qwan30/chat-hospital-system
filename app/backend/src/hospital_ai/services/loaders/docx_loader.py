"""DOCX document loader using python-docx."""
from __future__ import annotations


from pathlib import Path

from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.services.loaders.base import BaseDocumentLoader, LoadedPage


class DocxLoader(BaseDocumentLoader):
    """Extract text from DOCX files.

    Treats each paragraph as content. Header/table content is also extracted.
    """

    def supported_extensions(self) -> set[str]:
        return {".docx", ".doc"}

    def load(self, file_path: Path, mime_type: str = "") -> list[LoadedPage]:
        if not file_path.exists():
            raise ExternalServiceError(f"DOCX file not found: {file_path}")

        try:
            from docx import Document  # type: ignore[import-untyped]
        except ImportError:
            raise ExternalServiceError(
                "python-docx is not installed. Install it with `pip install python-docx`."
            ) from None

        try:
            doc = Document(str(file_path))
        except Exception as exc:
            raise ExternalServiceError(f"Failed to open DOCX: {exc}") from exc

        text_parts: list[str] = []

        # Extract paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                text_parts.append(text)

        # Extract table content
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    text_parts.append(row_text)

        full_text = "\n".join(text_parts)
        if not full_text.strip():
            raise ExternalServiceError("DOCX document is empty or contains no extractable text.")

        return [LoadedPage(page_number=1, text=full_text, confidence=1.0)]
