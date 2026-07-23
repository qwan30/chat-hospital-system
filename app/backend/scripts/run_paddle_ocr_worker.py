"""Isolated PaddleOCR 3.x worker for evaluation scan variants.

Run this script with a Python environment containing PaddleOCR 3.x and
PaddlePaddle 3.2+.  It prints exactly one JSON object to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


def _payload_from_result(result: object) -> Mapping[str, Any]:
    json_value = getattr(result, "json", None)
    if callable(json_value):
        json_value = json_value()
    if isinstance(json_value, str):
        json_value = json.loads(json_value)
    if not isinstance(json_value, Mapping):
        raise ValueError("PaddleOCR OCRResult.json must be an object")
    return json_value


def _extract_prediction(result: object) -> tuple[str, list[float]]:
    payload = _payload_from_result(result)
    response = payload.get("res")
    if not isinstance(response, Mapping):
        raise ValueError("PaddleOCR OCRResult.json['res'] must be an object")
    texts = response.get("rec_texts")
    scores = response.get("rec_scores")
    if isinstance(texts, (str, bytes)) or not isinstance(texts, Sequence):
        raise ValueError("PaddleOCR OCRResult.json['res']['rec_texts'] must be a sequence")
    if isinstance(scores, (str, bytes)) or not isinstance(scores, Sequence):
        raise ValueError("PaddleOCR OCRResult.json['res']['rec_scores'] must be a sequence")
    if len(texts) != len(scores) or not all(isinstance(item, str) for item in texts):
        raise ValueError("PaddleOCR recognition texts and scores must have matching valid values")
    if not all(isinstance(score, (int, float)) and not isinstance(score, bool) for score in scores):
        raise ValueError("PaddleOCR recognition scores must be numeric")
    return "\n".join(texts), [float(score) for score in scores]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, type=Path)
    arguments = parser.parse_args(argv)
    if not arguments.image.is_file() or arguments.image.suffix.lower() != ".png":
        print(json.dumps({"status": "execution_failed", "reason": "image must be an existing PNG file"}))
        return 2
    try:
        from paddleocr import PaddleOCR

        engine = PaddleOCR(
            device="cpu",
            cpu_threads=2,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
        texts: list[str] = []
        scores: list[float] = []
        for result in engine.predict(str(arguments.image)):
            page_text, page_scores = _extract_prediction(result)
            if page_text:
                texts.append(page_text)
            scores.extend(page_scores)
        print(json.dumps({"status": "executed", "text": "\n".join(texts), "rec_scores": scores}))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "execution_failed", "reason": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
