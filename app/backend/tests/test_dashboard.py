from __future__ import annotations
from unittest.mock import AsyncMock, patch

import pytest
from starlette.requests import Request

from hospital_ai.api.routes.dashboard import get_dashboard_summary
from hospital_ai.db.migrations import DOCTOR_ID
from hospital_ai.db.models import User
from hospital_ai.services.hms_connector import HmsApiClient


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/dashboard/summary",
            "headers": [],
            "client": ("testclient", 50000),
        }
    )


@pytest.mark.asyncio
async def test_dashboard_summary_healthy_flow(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    # Mock health checks to return healthy
    with (
        patch.object(HmsApiClient, "health_check", return_value=True),
        patch("httpx.AsyncClient.get") as mock_httpx_get,
    ):
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_httpx_get.return_value = mock_response

        response = await get_dashboard_summary(
            request=_request(),
            session=session,
            current_user=doctor,
            settings=settings,
        )

        assert response.systems_health.hms_api == "healthy"
        assert response.systems_health.ollama_inference == "healthy"
        assert response.document_stats.indexed >= 0
        assert isinstance(response.recent_patients, list)
        assert response.metrics.hours_saved >= 0.0
        assert response.metrics.cost_saved_usd >= 0.0


@pytest.mark.asyncio
async def test_dashboard_summary_unreachable_flow(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    # Mock health checks to return unreachable
    with (
        patch.object(HmsApiClient, "health_check", return_value=False),
        patch("httpx.AsyncClient.get", side_effect=Exception("Connection refused")),
    ):
        response = await get_dashboard_summary(
            request=_request(),
            session=session,
            current_user=doctor,
            settings=settings,
        )

        assert response.systems_health.hms_api == "unreachable"
        assert response.systems_health.ollama_inference == "unreachable"
