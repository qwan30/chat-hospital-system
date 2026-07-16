import json
import logging

import httpx
import pytest

from hospital_ai.core.config import Settings
from hospital_ai.core.logging import OTelJsonFormatter
from hospital_ai.main import create_app


def test_otel_json_formatter_text():
    formatter = OTelJsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message with %s",
        args=("params",),
        exc_info=None,
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["level"] == "INFO"
    assert data["logger"] == "test_logger"
    assert data["message"] == "Test message with params"
    assert "timestamp" in data
    assert "trace_id" not in data


@pytest.mark.asyncio
async def test_metrics_endpoint_when_enabled():
    app = create_app(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            prometheus_enabled=True,
        )
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/metrics")

    assert response.status_code == 200
    assert (
        "process_cpu_seconds_total" in response.text
        or "http_requests_total" in response.text
        or "hospital_ai_info" in response.text
    )


@pytest.mark.asyncio
async def test_metrics_endpoint_when_disabled():
    app = create_app(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            prometheus_enabled=False,
        )
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/metrics")

    assert response.status_code == 404
