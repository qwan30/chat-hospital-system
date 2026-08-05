"""Composite document loader — auto-detect + fallback chain.

Inspired by kotaemon's composite_loader.py pattern.
"""
from __future__ import annotations


import logging
from pathlib import Path
from typing import Optional

from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.services.loaders.base import BaseDocumentLoader, LoadedPage

logger = logging.getLogger(__name__)


class CompositeLoader:
    """Routes files to the correct loader based on extension.

    Maintains a registry of loaders, tries them in order,
    and falls back to OCR for unrecognized binary formats.
    """

    def __init__(self, loaders: Optional[list[BaseDocumentLoader]] = None) -> None:
        if loaders is not None:
            self._loaders = loaders
        else:
            self._loaders = self._default_loaders()

    @staticmethod
    def _default_loaders() -> list[BaseDocumentLoader]:
        from hospital_ai.services.loaders.docx_loader import DocxLoader
        from hospital_ai.services.loaders.excel_loader import ExcelLoader
        from hospital_ai.services.loaders.html_loader import HtmlLoader
        from hospital_ai.services.loaders.pdf_loader import PdfLoader
        from hospital_ai.services.loaders.text_loader import TextLoader

        return [
            TextLoader(),
            PdfLoader(),
            DocxLoader(),
            ExcelLoader(),
            HtmlLoader(),
        ]

    @property
    def supported_extensions(self) -> set:
        """Return the union of all loader extensions."""
        result: set = set()
        for loader in self._loaders:
            result.update(loader.supported_extensions())
        return result

    def load(self, file_path: Path, mime_type: str = "") -> list[LoadedPage]:
        """Load a document by finding the first matching loader.

        Args:
            file_path: Path to the file on disk.
            mime_type: Optional MIME type hint.

        Returns:
            List of LoadedPage extracted from the document.

        Raises:
            ExternalServiceError: If no loader can handle the file.
        """
        path = Path(file_path)
        errors: list[str] = []

        for loader in self._loaders:
            if loader.can_handle(path, mime_type):
                try:
                    pages = loader.load(path, mime_type)
                    logger.info(
                        "Loaded %d pages from %s using %s",
                        len(pages),
                        path.name,
                        type(loader).__name__,
                    )
                    return pages
                except ExternalServiceError as exc:
                    errors.append(f"{type(loader).__name__}: {exc}")
                    logger.warning("Loader %s failed for %s: %s", type(loader).__name__, path.name, exc)
                    continue

        # Fall back to OCR if no loader matched
        try:
            return self._fallback_ocr(path, mime_type)
        except ExternalServiceError as exc:
            errors.append(f"OCR fallback: {exc}")

        ext = path.suffix.lower()
        supported = ", ".join(sorted(self.supported_extensions))
        raise ExternalServiceError(
            f"No loader can handle '{ext}' files. Supported: {supported}. Errors: {'; '.join(errors)}"
        )

    def _fallback_ocr(self, file_path: Path, mime_type: str) -> list[LoadedPage]:
        """Fall back to the existing OCR service for images and scanned documents."""
        from hospital_ai.services.ocr import OcrService

        ocr = OcrService()
        ocr_pages = ocr.extract_page_results(storage_uri=str(file_path), mime_type=mime_type)
        return [
            LoadedPage(
                page_number=page.page_number,
                text=page.raw_text,
                confidence=page.confidence,
            )
            for page in ocr_pages
        ]

    def load_page_results(self, file_path: Path, mime_type: str = "") -> list[Any]:
        from hospital_ai.services.ocr import OcrService
        from hospital_ai.services.ocr_routing import OcrPageResult, OcrSpanResult

        try:
            pages = self.load(file_path, mime_type)
            res = []
            for p in pages:
                span = OcrSpanResult(
                    text=p.text,
                    start_offset=0,
                    end_offset=len(p.text),
                    polygon=((0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)),
                    confidence=p.confidence,
                    reading_order=1,
                    engine_family="native",
                    engine_model="loader",
                    engine_revision="v1",
                )
                res.append(
                    OcrPageResult(
                        page_number=p.page_number,
                        raw_text=p.text,
                        confidence=p.confidence,
                        route="native",
                        spans=(span,),
                        latency_ms=0,
                        peak_rss_mb=0,
                    )
                )
            return res
        except ExternalServiceError:
            return OcrService().extract_page_results(storage_uri=str(file_path), mime_type=mime_type)

    def register(self, loader: BaseDocumentLoader) -> None:
        """Register an additional loader."""
        self._loaders.append(loader)
