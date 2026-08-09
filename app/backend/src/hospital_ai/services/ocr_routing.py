from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OcrSpanResult:
    text: str
    start_offset: int
    end_offset: int
    polygon: tuple[tuple[float, float], ...]
    confidence: float
    reading_order: int
    engine_family: str
    engine_model: str
    engine_revision: str


@dataclass(frozen=True)
class OcrPageResult:
    page_number: int
    raw_text: str
    confidence: float
    route: str
    spans: tuple[OcrSpanResult, ...]
    latency_ms: int
    peak_rss_mb: int


@dataclass(frozen=True)
class PagePreflight:
    native_credible: bool
    handwriting_probability: float
    mixed_regions: tuple[Any, ...] = ()


@dataclass(frozen=True)
class RouteDecision:
    engine_family: str
    confidence: float


class OcrRouter:
    def __init__(self, handwriting_threshold: float = 0.72) -> None:
        self.handwriting_threshold = handwriting_threshold

    def route(self, preflight: PagePreflight) -> RouteDecision:
        if preflight.native_credible:
            return RouteDecision("native", 1.0)
        if preflight.handwriting_probability >= self.handwriting_threshold:
            return RouteDecision("vietocr_handwritten", preflight.handwriting_probability)
        return RouteDecision("paddle_printed", 1.0)
