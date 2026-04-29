"""PDF document loader using PyMuPDF (fitz)."""

from __future__ import annotations

from pathlib import Path
from typing import List, Set

from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.services.loaders.base import BaseDocumentLoader, LoadedPage


class PdfLoader(BaseDocumentLoader):
    """Extract text from PDF files page by page.

    Uses PyMuPDF (fitz) as the primary extraction engine.
    Falls back to pdfplumber if fitz is unavailable.
    """

    def supported_extensions(self) -> Set[str]:
        return {".pdf"}

    def load(self, file_path: Path, mime_type: str = "") -> List[LoadedPage]:
        if not file_path.exists():
            raise ExternalServiceError(f"PDF file not found: {file_path}")

        try:
            return self._load_with_fitz(file_path)
        except ImportError:
            pass

        try:
            return self._load_with_pdfplumber(file_path)
        except ImportError:
            raise ExternalServiceError(
                "No PDF library available. Install PyMuPDF (`pip install pymupdf`) "
                "or pdfplumber (`pip install pdfplumber`)."
            )

    def _load_with_fitz(self, file_path: Path) -> List[LoadedPage]:
        import fitz  # type: ignore[import-untyped]

        pages: List[LoadedPage] = []
        try:
            doc = fitz.open(str(file_path))
        except Exception as exc:
            raise ExternalServiceError(f"Failed to open PDF: {exc}") from exc

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            pages.append(
                LoadedPage(
                    page_number=page_num + 1,
                    text=text.strip(),
                    confidence=1.0 if text.strip() else 0.0,
                    metadata={"width": str(page.rect.width), "height": str(page.rect.height)},
                )
            )
        doc.close()

        if not pages:
            raise ExternalServiceError("PDF contains no pages.")
        return pages

    def _load_with_pdfplumber(self, file_path: Path) -> List[LoadedPage]:
        import pdfplumber  # type: ignore[import-untyped]

        pages: List[LoadedPage] = []
        try:
            with pdfplumber.open(str(file_path)) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    pages.append(
                        LoadedPage(
                            page_number=page_num,
                            text=text.strip(),
                            confidence=1.0 if text.strip() else 0.0,
                        )
                    )
        except Exception as exc:
            raise ExternalServiceError(f"Failed to open PDF with pdfplumber: {exc}") from exc

        if not pages:
            raise ExternalServiceError("PDF contains no pages.")
        return pages
