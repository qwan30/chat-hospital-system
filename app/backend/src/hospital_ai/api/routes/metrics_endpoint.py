"""Prometheus metrics export route.
Endpoint API xuất các chỉ số giám sát hiệu năng theo định dạng Prometheus (dùng cho Grafana / monitoring scrapers).
"""

from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["Metrics"])


@router.get("/metrics")
def get_metrics() -> Response:
    """Return Prometheus metrics.
    Trả về dữ liệu các chỉ số Prometheus hiện tại.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
