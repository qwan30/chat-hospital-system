from __future__ import annotations

import hashlib
from pathlib import Path

import fitz

from hospital_ai.evaluation.corpus_manifest import build_corpus_manifest
from hospital_ai.evaluation.ocr_evaluation import (
    build_ocr_gold_pages,
    probe_image_ocr_engine,
    render_scan_variants,
)

BACKEND_ROOT = Path(__file__).parents[2]
DATA_ROOT = BACKEND_ROOT / "data"


def _write_fixture_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=300, height=200)
    page.insert_text((24, 50), "Metformin 500 mg on 2026-07-22")
    document.save(path)
    document.close()


def test_gold_pages_are_bound_to_pdf_hash_page_and_native_text() -> None:
    manifest = build_corpus_manifest(DATA_ROOT)
    pages = build_ocr_gold_pages(manifest, DATA_ROOT, limit=2)

    assert len(pages) == 2
    for gold in pages:
        source = DATA_ROOT / gold.source_path
        assert gold.source_sha256 == hashlib.sha256(source.read_bytes()).hexdigest()
        assert gold.page_number >= 1
        assert gold.native_text.strip()
    assert any(gold.clinical_fields for gold in pages)


def test_scan_variants_are_reproducible_and_seeded(tmp_path: Path) -> None:
    pdf_path = tmp_path / "fixture.pdf"
    _write_fixture_pdf(pdf_path)

    first = render_scan_variants(pdf_path, page_number=1, seed=713)
    second = render_scan_variants(pdf_path, page_number=1, seed=713)
    changed_seed = render_scan_variants(pdf_path, page_number=1, seed=714)

    assert tuple(variant.name for variant in first) == ("low_dpi", "skew", "blur", "noise")
    assert tuple(variant.sha256 for variant in first) == tuple(variant.sha256 for variant in second)
    assert (
        next(item for item in first if item.name == "noise").sha256
        != next(item for item in changed_seed if item.name == "noise").sha256
    )
    assert all(variant.png_bytes.startswith(b"\x89PNG") for variant in first)


def test_missing_paddle_dependencies_are_explicitly_unavailable() -> None:
    status = probe_image_ocr_engine(find_spec=lambda _name: None)

    assert status.status == "engine_unavailable"
    assert not status.available
    assert "paddleocr" in status.reason
    assert "paddlepaddle" in status.reason


def test_available_paddle_dependencies_do_not_claim_an_ocr_run() -> None:
    status = probe_image_ocr_engine(find_spec=lambda _name: object())

    assert status.status == "engine_available_not_run"
    assert status.available
    assert "not executed" in status.reason
