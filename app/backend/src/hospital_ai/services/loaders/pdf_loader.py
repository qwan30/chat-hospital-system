"""PDF document loader using PyMuPDF (fitz) with table-aware extraction."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Set

from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.services.loaders.base import BaseDocumentLoader, LoadedPage

logger = logging.getLogger(__name__)


class PdfLoader(BaseDocumentLoader):
    """Extract text and tables from PDF files page by page.

    Uses PyMuPDF (fitz) as the primary extraction engine.
    Falls back to pdfplumber if fitz is unavailable.

    Table extraction is attempted using pdfplumber (even when fitz
    is used for text) because pdfplumber has superior table detection.
    Tables are converted to markdown format and appended to page text.
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

        # Try to extract tables via pdfplumber (better table detection)
        page_tables = self._extract_tables_pdfplumber(file_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")

            # Append table markdown if tables were found on this page
            tables_md = page_tables.get(page_num + 1, "")
            if tables_md:
                text = text.strip() + "\n\n" + tables_md

            pages.append(
                LoadedPage(
                    page_number=page_num + 1,
                    text=text.strip(),
                    confidence=1.0 if text.strip() else 0.0,
                    metadata={
                        "width": str(page.rect.width),
                        "height": str(page.rect.height),
                        "has_tables": "true" if tables_md else "false",
                    },
                )
            )
        doc.close()

        if not pages:
            raise ExternalServiceError("PDF contains no pages.")
        return pages

    def _load_with_pdfplumber(self, file_path: Path) -> List[LoadedPage]:
        import pdfplumber  # type: ignore[import-untyped]

        from hospital_ai.services.loaders.table_parser import tables_to_markdown

        pages: List[LoadedPage] = []
        try:
            with pdfplumber.open(str(file_path)) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""

                    # Extract tables from this page
                    tables_md = ""
                    try:
                        raw_tables = page.extract_tables()
                        if raw_tables:
                            tables_md = tables_to_markdown(raw_tables)
                    except Exception as exc:
                        logger.debug("Table extraction failed for page %d: %s", page_num, exc)

                    if tables_md:
                        text = text.strip() + "\n\n" + tables_md

                    pages.append(
                        LoadedPage(
                            page_number=page_num,
                            text=text.strip(),
                            confidence=1.0 if text.strip() else 0.0,
                            metadata={
                                "has_tables": "true" if tables_md else "false",
                            },
                        )
                    )
        except Exception as exc:
            raise ExternalServiceError(f"Failed to open PDF with pdfplumber: {exc}") from exc

        if not pages:
            raise ExternalServiceError("PDF contains no pages.")
        return pages

    def _extract_tables_pdfplumber(self, file_path: Path) -> dict[int, str]:
        """Extract tables from all pages using pdfplumber.

        Returns a dict mapping page_number (1-indexed) to markdown table text.
        Returns empty dict if pdfplumber is not available.
        """
        try:
            import pdfplumber  # type: ignore[import-untyped]
        except ImportError:
            logger.debug("pdfplumber not installed, skipping table extraction")
            return {}

        from hospital_ai.services.loaders.table_parser import tables_to_markdown

        page_tables: dict[int, str] = {}
        try:
            with pdfplumber.open(str(file_path)) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    try:
                        raw_tables = page.extract_tables()
                        if raw_tables:
                            md = tables_to_markdown(raw_tables)
                            if md.strip():
                                page_tables[page_num] = md
                    except Exception as exc:
                        logger.debug(
                            "Table extraction failed for page %d: %s",
                            page_num, exc,
                        )
        except Exception as exc:
            logger.warning("pdfplumber table extraction failed entirely: %s", exc)

        return page_tables
