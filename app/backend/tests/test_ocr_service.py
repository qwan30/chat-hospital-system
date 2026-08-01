from __future__ import annotations

import builtins

try:
    import tomllib
except ImportError:
    import tomli as tomllib
from pathlib import Path
from typing import Any

import fitz
import pytest

from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.services.ocr import OcrService, _parse_paddle_v3_results


class _StorageStub:
    def read_bytes(self, storage_uri: str) -> bytes:
        return Path(storage_uri).read_bytes()

    def save_page_image(self, patient_id: str, document_id: str, page_number: int, image_bytes: bytes) -> None:
        assert patient_id
        assert document_id
        assert page_number > 0
        assert image_bytes


class _BytesStorageStub(_StorageStub):
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.read_uris: list[str] = []

    def read_bytes(self, storage_uri: str) -> bytes:
        self.read_uris.append(storage_uri)
        return self.payload


class _PaddleV3Result:
    json = {
        "res": {
            "rec_texts": ["Aspirin 81 mg", "daily"],
            "rec_scores": [0.98, 0.94],
        }
    }


def test_image_only_pdf_without_ocr_engine_fails_explicitly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pdf_path = tmp_path / "image-only.pdf"
    document = fitz.open()
    document.new_page()
    document.save(pdf_path)
    document.close()

    real_import = builtins.__import__

    def import_without_paddle(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "paddleocr":
            raise ImportError("PaddleOCR intentionally unavailable in test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_paddle)

    with pytest.raises(ExternalServiceError, match="OCR engine is unavailable"):
        OcrService().extract_pages(
            storage_uri=str(pdf_path),
            mime_type="application/pdf",
            patient_id="patient-1",
            document_id="document-1",
            storage_service=_StorageStub(),
        )


def test_ocr_reads_pdf_from_storage_bytes_and_saves_page_png() -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Native text from R2")
    payload = document.tobytes()
    document.close()
    storage = _BytesStorageStub(payload)

    pages = OcrService().extract_pages(
        storage_uri="r2://patients/patient-1/documents/document-1/source.pdf",
        mime_type="application/pdf",
        patient_id="patient-1",
        document_id="document-1",
        storage_service=storage,
    )

    assert pages[0].text == "Native text from R2"
    assert storage.read_uris == ["r2://patients/patient-1/documents/document-1/source.pdf"]


def test_paddle_v3_result_contract_extracts_text_and_scores() -> None:
    text, confidence = _parse_paddle_v3_results([_PaddleV3Result()])

    assert text == "Aspirin 81 mg\ndaily"
    assert confidence == pytest.approx(0.96)


def test_ocr_extra_pins_supported_paddle_3_cpu_contract() -> None:
    config = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    ocr_dependencies = config["project"]["optional-dependencies"]["ocr"]

    assert "paddleocr>=3.0.0,<4.0.0" in ocr_dependencies
    assert "paddlepaddle>=3.2.0,<4.0.0" in ocr_dependencies
