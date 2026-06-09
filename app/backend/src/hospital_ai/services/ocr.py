from dataclasses import dataclass
from pathlib import Path

from hospital_ai.core.errors import ExternalServiceError


@dataclass
class OcrPage:
    page_number: int
    text: str
    confidence: float


class OcrService:
    """OCR adapter with a lightweight text path and optional PaddleOCR path."""

    TEXT_MIME_TYPES = {"text/plain", "text/markdown", "application/json"}

    def extract_pages(self, *, storage_uri: str, mime_type: str) -> list[OcrPage]:
        path = Path(storage_uri)
        if mime_type in self.TEXT_MIME_TYPES or path.suffix.lower() in {".txt", ".md"}:
            text = path.read_text(encoding="utf-8")
            return [OcrPage(page_number=1, text=text, confidence=1.0)]

        try:
            from paddleocr import PaddleOCR
        except Exception as exc:
            raise ExternalServiceError(
                "PaddleOCR is not installed. Install the backend with the 'ocr' extra for image/PDF OCR."
            ) from exc

        ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False)
        result = ocr.predict(str(path))
        pages: list[OcrPage] = []
        for page_index, page_result in enumerate(result, start=1):
            text_lines = []
            scores = []
            for item in page_result.get("rec_texts", []) or []:
                text_lines.append(str(item))
            for score in page_result.get("rec_scores", []) or []:
                scores.append(float(score))
            confidence = sum(scores) / len(scores) if scores else 0.0
            pages.append(OcrPage(page_number=page_index, text="\n".join(text_lines), confidence=confidence))
        if not pages:
            raise ExternalServiceError("OCR produced no pages.")
        return pages
