"""Source-backed OCR gold pages and reproducible rendered scan variants."""

from __future__ import annotations

import hashlib
import importlib.util
import re
from collections.abc import Callable
from importlib.machinery import ModuleSpec
from pathlib import Path

import fitz
import numpy as np

from hospital_ai.evaluation.contracts import ClinicalField, OcrEngineStatus, OcrGoldPage, ScanVariant
from hospital_ai.evaluation.corpus_manifest import CorpusManifestV2

_FIELD_PATTERNS = (
    ("date", re.compile(r"\b\d{4}-\d{2}-\d{2}\b")),
    (
        "dose",
        re.compile(
            r"\b\d+(?:\.\d+)?\s*(?:mcg|mg|g|mL|L|units?|mmol/L|mg/dL|g/dL|mEq/L)\b",
            re.IGNORECASE,
        ),
    ),
    ("number", re.compile(r"\b\d+(?:\.\d+)?\b")),
)


def _clinical_fields(text: str) -> tuple[ClinicalField, ...]:
    fields: list[ClinicalField] = []
    occupied: set[tuple[int, int]] = set()
    for field_type, pattern in _FIELD_PATTERNS:
        for match in pattern.finditer(text):
            span = match.span()
            if field_type == "number" and any(start <= span[0] and span[1] <= end for start, end in occupied):
                continue
            occupied.add(span)
            fields.append(
                ClinicalField(
                    field_type=field_type,
                    value=match.group(0),
                    span_start=span[0],
                    span_end=span[1],
                )
            )
    return tuple(sorted(fields, key=lambda field: (field.span_start, field.span_end, field.field_type)))


def build_ocr_gold_pages(
    manifest: CorpusManifestV2,
    data_root: Path,
    *,
    limit: int | None = None,
) -> tuple[OcrGoldPage, ...]:
    """Read canonical PDF text layers into page-addressed OCR ground truth."""
    document_artifacts = sorted(
        (artifact for artifact in manifest.artifacts if artifact.kind == "patient_document"),
        key=lambda artifact: artifact.canonical_relative_path,
    )
    pages: list[OcrGoldPage] = []
    for artifact in document_artifacts:
        source = data_root / artifact.canonical_relative_path
        with fitz.open(source) as document:
            for page_index, page in enumerate(document):
                text = page.get_text("text")
                pages.append(
                    OcrGoldPage(
                        source_path=artifact.canonical_relative_path,
                        source_sha256=artifact.source_sha256,
                        page_number=page_index + 1,
                        native_text=text,
                        clinical_fields=_clinical_fields(text),
                    )
                )
                if limit is not None and len(pages) >= limit:
                    return tuple(pages)
    return tuple(pages)


def _render_rgb(page: fitz.Page, dpi: int) -> np.ndarray:
    pixmap = page.get_pixmap(dpi=dpi, alpha=False, colorspace=fitz.csRGB)
    return np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, 3).copy()


def _encode_png(rgb: np.ndarray) -> bytes:
    height, width, channels = rgb.shape
    if channels != 3:
        raise ValueError("scan variants require RGB pixels")
    pixmap = fitz.Pixmap(fitz.csRGB, width, height, np.ascontiguousarray(rgb).tobytes(), False)
    return pixmap.tobytes("png")


def _variant(name: str, seed: int, rgb: np.ndarray) -> ScanVariant:
    png_bytes = _encode_png(rgb)
    return ScanVariant(
        name=name,
        seed=seed,
        width=rgb.shape[1],
        height=rgb.shape[0],
        sha256=hashlib.sha256(png_bytes).hexdigest(),
        png_bytes=png_bytes,
    )


def _skew(rgb: np.ndarray) -> np.ndarray:
    height, width, _ = rgb.shape
    max_shift = max(1, round(width * 0.025))
    output = np.full((height, width + max_shift, 3), 255, dtype=np.uint8)
    for row in range(height):
        shift = round(max_shift * row / max(height - 1, 1))
        output[row, shift : shift + width] = rgb[row]
    return output


def _blur(rgb: np.ndarray) -> np.ndarray:
    padded = np.pad(rgb.astype(np.uint16), ((1, 1), (1, 1), (0, 0)), mode="edge")
    summed = sum(
        padded[row : row + rgb.shape[0], column : column + rgb.shape[1]] for row in range(3) for column in range(3)
    )
    return (summed // 9).astype(np.uint8)


def render_scan_variants(pdf_path: Path, *, page_number: int, seed: int) -> tuple[ScanVariant, ...]:
    """Render four deterministic image-only variants for a one-based PDF page."""
    if page_number < 1:
        raise ValueError("page_number must be positive")
    with fitz.open(pdf_path) as document:
        if page_number > len(document):
            raise ValueError("page_number exceeds PDF page count")
        page = document[page_number - 1]
        low_dpi = _render_rgb(page, 72)
        base = _render_rgb(page, 144)
    rng = np.random.default_rng(seed)
    noise = np.clip(base.astype(np.int16) + rng.normal(0, 12, base.shape), 0, 255).astype(np.uint8)
    return (
        _variant("low_dpi", seed, low_dpi),
        _variant("skew", seed, _skew(base)),
        _variant("blur", seed, _blur(base)),
        _variant("noise", seed, noise),
    )


def probe_image_ocr_engine(
    *,
    find_spec: Callable[[str], ModuleSpec | object | None] = importlib.util.find_spec,
) -> OcrEngineStatus:
    missing = []
    if find_spec("paddleocr") is None:
        missing.append("paddleocr")
    if find_spec("paddle") is None:
        missing.append("paddlepaddle")
    if missing:
        return OcrEngineStatus(
            status="engine_unavailable",
            available=False,
            reason=f"missing image OCR dependencies: {', '.join(missing)}",
        )
    return OcrEngineStatus(
        status="engine_available_not_run",
        available=True,
        reason="Paddle dependencies are available but image OCR was not executed by this deterministic adapter",
    )
