from __future__ import annotations
import httpx
import pytest

from hospital_ai.core.config import Settings
from hospital_ai.main import create_app


@pytest.mark.asyncio
async def test_cors_preflight_allows_configured_local_frontend_origin():
    app = create_app(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins="http://localhost:3000",
        )
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.options(
            "/api/v1/chat-threads",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "authorization" in response.headers["access-control-allow-headers"].lower()
