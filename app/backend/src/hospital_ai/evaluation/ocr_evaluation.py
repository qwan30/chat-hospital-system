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

from hospital_ai.evaluation.contracts import (
    ClinicalField,
    ClinicalFieldMatchResult,
    OcrEngineStatus,
    OcrEvaluationSummary,
    OcrGoldPage,
    OcrVariantMetric,
    ScanVariant,
)
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
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if windows else 0,
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


def _parse_dose(value_str: str) -> tuple[float, str] | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z/]+)", value_str)
    if not m:
        return None
    try:
        return float(m.group(1)), m.group(2).lower()
    except ValueError:
        return None


def match_clinical_fields(
    gold_fields: tuple[ClinicalField, ...],
    extracted_text: str,
) -> tuple[ClinicalFieldMatchResult, ...]:
    """Evaluate gold clinical fields against extracted OCR text with normalization."""
    results: list[ClinicalFieldMatchResult] = []
    extracted_clean = re.sub(r"\s+", " ", extracted_text).strip()

    for field in gold_fields:
        exact_match = field.value in extracted_text or field.value in extracted_clean
        normalized_match = exact_match
        decimal_misread_risk = False
        found_extracted_value: str | None = field.value if exact_match else None

        if field.field_type == "dose":
            gold_parsed = _parse_dose(field.value)
            if gold_parsed:
                gold_num, gold_unit = gold_parsed
                dose_pattern = re.compile(
                    r"\b(\d+(?:\.\d+)?)\s*([a-zA-Z/]+)\b",
                    re.IGNORECASE,
                )
                for cand in dose_pattern.finditer(extracted_clean):
                    try:
                        cand_num = float(cand.group(1))
                        cand_unit = cand.group(2).lower()
                    except ValueError:
                        continue
                    if cand_unit == gold_unit:
                        if abs(cand_num - gold_num) < 1e-5:
                            normalized_match = True
                            found_extracted_value = cand.group(0)
                            decimal_misread_risk = False
                            break
                        else:
                            ratio = cand_num / max(gold_num, 1e-5)
                            if ratio >= 9.0 or ratio <= 0.11:
                                decimal_misread_risk = True
                                found_extracted_value = cand.group(0)

        elif field.field_type in ("mrn", "number"):
            gold_alpha = re.sub(r"[^a-zA-Z0-9]", "", field.value).upper()
            ext_alpha = re.sub(r"[^a-zA-Z0-9]", "", extracted_clean).upper()
            if gold_alpha and gold_alpha in ext_alpha:
                normalized_match = True
                found_extracted_value = field.value

        elif field.field_type == "date":
            dates_in_ext = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", extracted_clean)
            if field.value in dates_in_ext:
                normalized_match = True
                found_extracted_value = field.value

        results.append(
            ClinicalFieldMatchResult(
                field_type=field.field_type,
                gold_value=field.value,
                extracted_value=found_extracted_value,
                exact_match=exact_match,
                normalized_match=normalized_match,
                decimal_misread_risk=decimal_misread_risk,
            )
        )

    return tuple(results)



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


def _render_rgb(page: fitz.Page, dpi: int, rotation: int = 0) -> np.ndarray:
    mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    if rotation != 0:
        mat = mat.prerotate(rotation)
    pixmap = page.get_pixmap(matrix=mat, alpha=False, colorspace=fitz.csRGB)
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
        name=name,  # type: ignore[arg-type]
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


def _blur_kernel(rgb: np.ndarray, radius: int = 1) -> np.ndarray:
    padded = np.pad(rgb.astype(np.uint32), ((radius, radius), (radius, radius), (0, 0)), mode="edge")
    h, w, _ = rgb.shape
    ksize = (2 * radius + 1) ** 2
    summed = np.zeros((h, w, 3), dtype=np.uint32)
    for r in range(2 * radius + 1):
        for c in range(2 * radius + 1):
            summed += padded[r : r + h, c : c + w]
    return (summed // ksize).astype(np.uint8)


def _contrast_low(rgb: np.ndarray) -> np.ndarray:
    return np.clip(rgb.astype(np.float32) * 0.5 + 64.0, 0, 255).astype(np.uint8)


def render_scan_variants(pdf_path: Path, *, page_number: int, seed: int) -> tuple[ScanVariant, ...]:
    """Render ten deterministic image-only variants for a one-based PDF page."""
    if page_number < 1:
        raise ValueError("page_number must be positive")
    with fitz.open(pdf_path) as document:
        if page_number > len(document):
            raise ValueError("page_number exceeds PDF page count")
        page = document[page_number - 1]
        base = _render_rgb(page, 144)
        rot_90_rgb = _render_rgb(page, 144, rotation=90)
        rot_180_rgb = _render_rgb(page, 144, rotation=180)
        rot_270_rgb = _render_rgb(page, 144, rotation=270)
        low_72_rgb = _render_rgb(page, 72)
        low_150_rgb = _render_rgb(page, 150)

    rng = np.random.default_rng(seed)
    noise_rgb = np.clip(base.astype(np.int16) + rng.normal(0, 12, base.shape), 0, 255).astype(np.uint8)

    return (
        _variant("rot_90", seed, rot_90_rgb),
        _variant("rot_180", seed, rot_180_rgb),
        _variant("rot_270", seed, rot_270_rgb),
        _variant("low_res_72dpi", seed, low_72_rgb),
        _variant("low_res_150dpi", seed, low_150_rgb),
        _variant("blur_light", seed, _blur_kernel(base, radius=1)),
        _variant("blur_heavy", seed, _blur_kernel(base, radius=2)),
        _variant("noise_gaussian", seed, noise_rgb),
        _variant("contrast_low", seed, _contrast_low(base)),
        _variant("skew_slight", seed, _skew(base)),
    )



import time


def _calculate_cer(gold_text: str, ext_text: str) -> float:
    gold = gold_text.strip()
    ext = ext_text.strip()
    if not gold:
        return 0.0 if not ext else 1.0
    m, n = len(gold), len(ext)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            cost = 0 if gold[i - 1] == ext[j - 1] else 1
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
            prev = temp
    return min(1.0, dp[n] / max(m, 1))


def _calculate_wer(gold_text: str, ext_text: str) -> float:
    gold_words = gold_text.strip().split()
    ext_words = ext_text.strip().split()
    if not gold_words:
        return 0.0 if not ext_words else 1.0
    m, n = len(gold_words), len(ext_words)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            cost = 0 if gold_words[i - 1] == ext_words[j - 1] else 1
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
            prev = temp
    return min(1.0, dp[n] / max(m, 1))


def evaluate_ocr_corpus(
    manifest: CorpusManifestV2,
    data_root: Path,
    *,
    limit_pages: int | None = None,
    isolated_python: Path | None = None,
    use_mock_ocr: bool = False,
) -> OcrEvaluationSummary:
    """Evaluate OCR engine performance across 10 scan variants for gold pages."""
    gold_pages = build_ocr_gold_pages(manifest, data_root, limit=limit_pages)
    if not gold_pages:
        return OcrEvaluationSummary(
            gold_page_count=0,
            total_variants_evaluated=0,
            overall_cer=0.0,
            overall_wer=0.0,
            overall_clinical_accuracy=0.0,
            variant_metrics=(),
        )

    variant_results: dict[str, list[dict[str, float]]] = {}

    for gold in gold_pages:
        pdf_path = data_root / gold.source_path
        variants = render_scan_variants(pdf_path, page_number=gold.page_number, seed=713)
        for variant in variants:
            t0 = time.perf_counter()
            if use_mock_ocr:
                extracted_text = gold.native_text
            else:
                ocr_res = run_isolated_paddle_ocr(variant.png_bytes, isolated_python=isolated_python)
                extracted_text = ocr_res.text if ocr_res.available else ""
            elapsed = time.perf_counter() - t0

            cer = _calculate_cer(gold.native_text, extracted_text)
            wer = _calculate_wer(gold.native_text, extracted_text)
            field_matches = match_clinical_fields(gold.clinical_fields, extracted_text)

            accuracy = (
                sum(1 for m in field_matches if m.normalized_match) / len(field_matches)
                if field_matches
                else 1.0
            )
            decimal_misreads = sum(1 for m in field_matches if m.decimal_misread_risk)

            if variant.name not in variant_results:
                variant_results[variant.name] = []
            variant_results[variant.name].append(
                {
                    "cer": cer,
                    "wer": wer,
                    "accuracy": accuracy,
                    "decimal_misreads": decimal_misreads,
                    "latency": elapsed,
                }
            )

    variant_metrics: list[OcrVariantMetric] = []
    total_cer, total_wer, total_acc = 0.0, 0.0, 0.0
    count = 0

    for name, records in variant_results.items():
        n = len(records)
        avg_cer = sum(r["cer"] for r in records) / n
        avg_wer = sum(r["wer"] for r in records) / n
        avg_acc = sum(r["accuracy"] for r in records) / n
        dec_cnt = sum(int(r["decimal_misreads"]) for r in records)
        avg_lat = sum(r["latency"] for r in records) / n

        variant_metrics.append(
            OcrVariantMetric(
                variant_name=name,
                page_count=n,
                cer=avg_cer,
                wer=avg_wer,
                clinical_field_accuracy=avg_acc,
                decimal_misread_count=dec_cnt,
                mean_latency_seconds=avg_lat,
            )
        )
        total_cer += avg_cer
        total_wer += avg_wer
        total_acc += avg_acc
        count += 1

    return OcrEvaluationSummary(
        gold_page_count=len(gold_pages),
        total_variants_evaluated=len(variant_metrics),
        overall_cer=total_cer / max(count, 1),
        overall_wer=total_wer / max(count, 1),
        overall_clinical_accuracy=total_acc / max(count, 1),
        variant_metrics=tuple(variant_metrics),
    )


def export_ocr_evaluation_markdown(summary: OcrEvaluationSummary, output_path: Path) -> None:
    """Generate official benchmark report in Markdown format."""
    lines = [
        "# OCR Evaluation Harness Summary",
        "",
        f"- **Gold Pages Evaluated:** {summary.gold_page_count}",
        f"- **Total Scan Variants:** {summary.total_variants_evaluated}",
        f"- **Overall CER:** {summary.overall_cer:.4f}",
        f"- **Overall WER:** {summary.overall_wer:.4f}",
        f"- **Overall Clinical Accuracy:** {summary.overall_clinical_accuracy * 100:.2f}%",
        "",
        "## Performance & Field Accuracy Breakdown by Image Variant",
        "",
        "| Variant | Pages | CER | WER | Clinical Accuracy | Decimal Misreads | Mean Latency (s) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for m in summary.variant_metrics:
        lines.append(
            f"| `{m.variant_name}` | {m.page_count} | {m.cer:.4f} | {m.wer:.4f} | {m.clinical_field_accuracy * 100:.1f}% | {m.decimal_misread_count} | {m.mean_latency_seconds:.3f} |"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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


