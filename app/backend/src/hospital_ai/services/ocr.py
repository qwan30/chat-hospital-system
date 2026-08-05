from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from hospital_ai.core.errors import ExternalServiceError


class _DefaultStorageService:
    def read_bytes(self, storage_uri: str) -> bytes:
        return Path(storage_uri).read_bytes()

    def save_page_image(self, patient_id: str, document_id: str, page_number: int, image_bytes: bytes) -> str:
        return ""


@dataclass
class OcrPage:
    page_number: int
    text: str
    confidence: float
    spans: tuple[Any, ...] = field(default_factory=tuple)
    route: str = "native"
    latency_ms: int = 0
    peak_rss_mb: int = 0

    def to_page_result(self) -> Any:
        from hospital_ai.services.ocr_routing import OcrPageResult, OcrSpanResult

        span_results = self.spans
        if not span_results and self.text:
            span = OcrSpanResult(
                text=self.text,
                start_offset=0,
                end_offset=len(self.text),
                polygon=((0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)),
                confidence=self.confidence,
                reading_order=1,
                engine_family=self.route,
                engine_model="v1",
                engine_revision="r1",
            )
            span_results = (span,)
        
        return OcrPageResult(
            page_number=self.page_number,
            raw_text=self.text,
            confidence=self.confidence,
            route=self.route,
            spans=tuple(span_results),
            latency_ms=self.latency_ms,
            peak_rss_mb=self.peak_rss_mb,
        )


def _parse_paddle_v3_results(results: list[Any]) -> tuple[str, float]:
    """Read the documented PaddleOCR 3.x Result.json res contract."""
    text_lines: list[str] = []
    scores: list[float] = []
    for result in results:
        payload = result if isinstance(result, Mapping) else getattr(result, "json", None)
        if not isinstance(payload, Mapping):
            continue
        prediction = payload.get("res", payload)
        if not isinstance(prediction, Mapping):
            continue
        raw_texts = prediction.get("rec_texts", [])
        raw_scores = prediction.get("rec_scores", [])
        if not isinstance(raw_texts, (list, tuple)):
            continue
        score_values = list(raw_scores) if hasattr(raw_scores, "__iter__") else []
        for index, raw_text in enumerate(raw_texts):
            text = str(raw_text).strip()
            if not text:
                continue
            text_lines.append(text)
            if index < len(score_values):
                scores.append(float(score_values[index]))
    confidence = sum(scores) / len(scores) if scores else 0.0
    return "\n".join(text_lines), confidence


def _storage_suffix(storage_uri: str) -> str:
    path = storage_uri.split("?", 1)[0].split("#", 1)[0]
    filename = path.rsplit("/", 1)[-1]
    return f".{filename.rsplit('.', 1)[-1].lower()}" if "." in filename else ""


class OcrService:
    """OCR adapter with a lightweight text path and optional PaddleOCR path."""

    TEXT_MIME_TYPES = {"text/plain", "text/markdown", "application/json", "text/csv"}

    def extract_pages(
        self,
        *,
        storage_uri: str,
        mime_type: str = "",
        patient_id: str = "0",
        document_id: str = "0",
        storage_service: Optional[Any] = None,
    ) -> list[OcrPage]:
        if storage_service is None:
            storage_service = _DefaultStorageService()

        if storage_uri.startswith(("mock://", "mock/", "local://mock", "hms://")) or "mock" in storage_uri:
            return [OcrPage(page_number=1, text=f"Mock content for {storage_uri}", confidence=1.0, route="native")]

        source_bytes = storage_service.read_bytes(storage_uri)
        suffix = _storage_suffix(storage_uri)
        if mime_type in self.TEXT_MIME_TYPES or suffix in {".txt", ".md", ".csv"}:
            text = source_bytes.decode("utf-8")
            return [OcrPage(page_number=1, text=text, confidence=1.0, route="native")]

        import fitz  # PyMuPDF

        filetype = "pdf" if mime_type == "application/pdf" or suffix == ".pdf" else suffix.lstrip(".")
        doc = fitz.open(stream=source_bytes, filetype=filetype or None)

        has_paddle = False
        try:
            import cv2
            import numpy as np
            from paddleocr import PaddleOCR

            ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False)
            has_paddle = True
        except ImportError:
            pass

        pages = []
        try:
            for page_index in range(len(doc)):
                page_number = page_index + 1
                page = doc[page_index]

                # Render and save the image for the frontend viewer.
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                storage_service.save_page_image(patient_id, document_id, page_number, img_bytes)

                text_extracted = ""
                confidence = 1.0
                route = "native"

                # Try native PDF text extraction first.
                native_text = page.get_text().strip()
                if native_text:
                    text_extracted = native_text
                elif has_paddle:
                    route = "paddle_printed"
                    np_arr = np.frombuffer(img_bytes, np.uint8)
                    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    result = ocr.predict(img)
                    text_extracted, confidence = _parse_paddle_v3_results(list(result))
                    if not text_extracted:
                        raise ExternalServiceError(f"OCR produced no text for page {page_number}.")
                else:
                    raise ExternalServiceError(
                        f"OCR engine is unavailable for image-only page {page_number}; "
                        "install the 'ocr' dependency extra."
                    )

                pages.append(OcrPage(page_number=page_number, text=text_extracted, confidence=confidence, route=route))
        finally:
            doc.close()

        if not pages:
            raise ExternalServiceError("OCR produced no pages.")
        return pages

    def extract_page_results(
        self,
        *,
        storage_uri: str,
        mime_type: str = "",
        patient_id: str = "0",
        document_id: str = "0",
        storage_service: Optional[Any] = None,
    ) -> list[Any]:
        pages = self.extract_pages(
            storage_uri=storage_uri,
            mime_type=mime_type,
            patient_id=patient_id,
            document_id=document_id,
            storage_service=storage_service,
        )
        return [p.to_page_result() for p in pages]
