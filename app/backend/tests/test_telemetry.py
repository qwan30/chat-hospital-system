from __future__ import annotations
import httpx
import pytest

from hospital_ai.core.config import Settings
from hospital_ai.core.telemetry import CHAT_REQUESTS
from hospital_ai.main import create_app


@pytest.fixture
def app():
    settings = Settings(
        environment="test",
        chat_provider="stub",
        embedding_provider="ollama",
        retrieval_mode="hybrid",
        reranker_provider="keyword",
    )
    return create_app(settings)


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus_format(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/api/v1/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        assert "llm_request_duration_seconds" in response.text
        assert "hospital_ai_info" in response.text


@pytest.mark.asyncio
async def test_app_info_metric_set(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/api/v1/metrics")
        assert response.status_code == 200
        assert "hospital_ai_info{" in response.text
        assert 'environment="test"' in response.text
        assert 'chat_provider="stub"' in response.text


@pytest.mark.asyncio
async def test_chat_request_counter_increments(app):
    CHAT_REQUESTS.labels(scope="general", status="success").inc()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/api/v1/metrics")
        assert "chat_request_total" in response.text
