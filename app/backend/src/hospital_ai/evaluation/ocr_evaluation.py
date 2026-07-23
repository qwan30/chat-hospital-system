"""Source-backed OCR gold pages and reproducible rendered scan variants."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from importlib.machinery import ModuleSpec
from pathlib import Path
from typing import Literal

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

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True)
class IsolatedOcrExecution:
    """The explicit result of invoking the Pydantic-2/PaddleOCR worker."""

    status: Literal["engine_unavailable", "executed", "execution_failed"]
    available: bool
    reason: str
    text: str = ""
    rec_scores: tuple[float, ...] = ()


def _default_worker_script() -> Path:
    return Path(__file__).parents[3] / "scripts" / "run_paddle_ocr_worker.py"


def _failed_worker_result(reason: str) -> IsolatedOcrExecution:
    return IsolatedOcrExecution(status="execution_failed", available=False, reason=reason)


def _terminate_worker_process_tree(
    process: subprocess.Popen[str],
    *,
    run: Callable[..., subprocess.CompletedProcess[str]],
    is_windows: bool,
) -> None:
    """Best-effort cleanup that includes worker children on Windows."""
    if process.poll() is not None:
        return
    try:
        if is_windows:
            run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                check=False,
                text=True,
                shell=False,
                timeout=5,
            )
        else:
            process.kill()
    except (OSError, subprocess.TimeoutExpired):
        # Preserve the explicit timeout contract even if cleanup itself fails.
        pass


def run_isolated_paddle_ocr(
    png_bytes: bytes,
    *,
    isolated_python: Path | None,
    worker_script: Path | None = None,
    timeout_seconds: float = 60.0,
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    popen: Callable[..., subprocess.Popen[str]] = subprocess.Popen,
    is_windows: bool | None = None,
) -> IsolatedOcrExecution:
    """Execute PaddleOCR in its isolated interpreter and validate its JSON result.

    The backend itself remains on Pydantic 1.x.  This adapter writes only a
    trusted, generated PNG to a temporary file and passes its path as a single
    subprocess argument; no image data is interpolated into shell input.
    """
    if isolated_python is None:
        return IsolatedOcrExecution(
            status="engine_unavailable",
            available=False,
            reason="isolated PaddleOCR Python executable is not configured",
        )
    if not png_bytes.startswith(_PNG_SIGNATURE):
        return _failed_worker_result("OCR worker input must be a PNG image")
    if timeout_seconds <= 0:
        return _failed_worker_result("OCR worker timeout must be positive")

    script = worker_script or _default_worker_script()
    windows = os.name == "nt" if is_windows is None else is_windows
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix="hms-eval-ocr-", suffix=".png", delete=False) as temporary_file:
            temporary_file.write(png_bytes)
            temporary_path = Path(temporary_file.name)
        process = popen(
            [str(isolated_python), str(script), "--image", str(temporary_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if windows else 0,
        )
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        _terminate_worker_process_tree(process, run=run, is_windows=windows)
        return _failed_worker_result("isolated PaddleOCR worker timed out")
    except OSError as exc:
        return IsolatedOcrExecution(
            status="engine_unavailable",
            available=False,
            reason=f"isolated PaddleOCR worker could not start: {exc}",
        )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    if process.returncode != 0:
        detail = stderr.strip() or "worker exited without an error message"
        return _failed_worker_result(f"isolated PaddleOCR worker failed: {detail}")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return _failed_worker_result("isolated PaddleOCR worker returned invalid JSON")
    if not isinstance(payload, dict):
        return _failed_worker_result("isolated PaddleOCR worker JSON must be an object")
    if payload.get("status") != "executed":
        detail = payload.get("reason")
        return _failed_worker_result(f"isolated PaddleOCR worker did not execute: {detail or 'unknown status'}")
    text = payload.get("text")
    scores = payload.get("rec_scores")
    if (
        not isinstance(text, str)
        or not isinstance(scores, list)
        or any(not isinstance(score, (int, float)) or isinstance(score, bool) for score in scores)
    ):
        return _failed_worker_result("isolated PaddleOCR worker returned an invalid OCR result contract")
    return IsolatedOcrExecution(
        status="executed",
        available=True,
        reason="isolated PaddleOCR worker executed",
        text=text,
        rec_scores=tuple(float(score) for score in scores),
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
