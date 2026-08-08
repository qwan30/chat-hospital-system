from __future__ import annotations

import pytest

from hospital_ai.services.ocr_routing import OcrPageResult, OcrRouter, OcrSpanResult, PagePreflight


def test_router_selects_handwriting_only_above_qualified_threshold() -> None:
    decision = OcrRouter(handwriting_threshold=0.72).route(
        PagePreflight(native_credible=False, handwriting_probability=0.81, mixed_regions=())
    )
    assert decision.engine_family == "vietocr_handwritten"
    assert decision.confidence == pytest.approx(0.81)


def test_router_selects_native_when_credible() -> None:
    decision = OcrRouter(handwriting_threshold=0.72).route(
        PagePreflight(native_credible=True, handwriting_probability=0.1, mixed_regions=())
    )
    assert decision.engine_family == "native"
    assert decision.confidence == pytest.approx(1.0)


def test_router_selects_printed_when_low_handwriting() -> None:
    decision = OcrRouter(handwriting_threshold=0.72).route(
        PagePreflight(native_credible=False, handwriting_probability=0.3, mixed_regions=())
    )
    assert decision.engine_family == "paddle_printed"


def test_ocr_result_types_geometry_and_immutability() -> None:
    span = OcrSpanResult(
        text="Sample text",
        start_offset=0,
        end_offset=11,
        polygon=((0.0, 0.0), (10.0, 0.0), (10.0, 5.0), (0.0, 5.0)),
        confidence=0.98,
        reading_order=1,
        engine_family="paddle_printed",
        engine_model="v4",
        engine_revision="r1",
    )
    page = OcrPageResult(
        page_number=1,
        raw_text="Sample text",
        confidence=0.98,
        route="paddle_printed",
        spans=(span,),
        latency_ms=150,
        peak_rss_mb=250,
    )
    assert page.page_number == 1
    assert page.spans[0].text == "Sample text"

    with pytest.raises(AttributeError):
        page.raw_text = "Mutated text"  # type: ignore[misc]
