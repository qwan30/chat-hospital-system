"""Optical Character Recognition (OCR) adapter service.
Dịch vụ trích xuất văn bản từ hình ảnh và tài liệu PDF (sử dụng PyMuPDF & PaddleOCR).
"""

from dataclasses import dataclass
from pathlib import Path

from hospital_ai.core.errors import ExternalServiceError


@dataclass
class OcrPage:
    """Kết quả OCR cho từng trang tài liệu, bao gồm số trang, văn bản trích xuất và độ tin cậy."""
    page_number: int
    text: str
    confidence: float


class OcrService:
    """OCR adapter with a lightweight text path and optional PaddleOCR path.
    Bộ trích xuất OCR hỗ trợ đọc văn bản thuần (txt, md), PDF gốc qua PyMuPDF và fallback dùng PaddleOCR cho hình ảnh.
    """

    TEXT_MIME_TYPES = {"text/plain", "text/markdown", "application/json"}

    def extract_pages(
        self, *, storage_uri: str, mime_type: str, patient_id: str, document_id: str, storage_service
    ) -> list[OcrPage]:
        """Trích xuất văn bản và lưu ảnh từng trang tài liệu để phục vụ hiển thị trên trình xem (PDF viewer)."""
        path = Path(storage_uri)
        if mime_type in self.TEXT_MIME_TYPES or path.suffix.lower() in {".txt", ".md"}:
            text = path.read_text(encoding="utf-8")
            return [OcrPage(page_number=1, text=text, confidence=1.0)]

        import fitz  # PyMuPDF

        # If it's a PDF or image, we render images first.
        doc = fitz.open(str(path))

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
        for page_index in range(len(doc)):
            page_number = page_index + 1
            page = doc[page_index]

            # 1. Render and save the image for the frontend viewer
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            storage_service.save_page_image(patient_id, document_id, page_number, img_bytes)

            text_extracted = ""
            confidence = 1.0

            # 2. Try native PDF text extraction first
            native_text = page.get_text().strip()
            if native_text:
                text_extracted = native_text
            elif has_paddle:
                # 3. Fallback to OCR on the rendered image if no native text exists and paddle is installed
                np_arr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                result = ocr.predict(img)
                text_lines = []
                scores = []
                if result and result[0]:
                    for item in result[0]:
                        if len(item) == 2 and isinstance(item[1], tuple):
                            text_lines.append(str(item[1][0]))
                            scores.append(float(item[1][1]))
                confidence = sum(scores) / len(scores) if scores else 0.0
                text_extracted = "\n".join(text_lines)

            pages.append(OcrPage(page_number=page_number, text=text_extracted, confidence=confidence))

        if not pages:
            raise ExternalServiceError("OCR produced no pages.")
        return pages
