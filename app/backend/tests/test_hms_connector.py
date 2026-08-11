"""Security contracts for the HMS HTTP client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.services.hms_connector import HmsApiClient


@pytest.fixture
def hms_client() -> HmsApiClient:
    return HmsApiClient(Settings(hms_base_url="https://hms.example.test/api/v1"))


@pytest.mark.parametrize(
    "path",
    [
        "https://attacker.example/steal",
        "//attacker.example/steal",
        "/ai/patients/../admin",
        "/ai/patients/p-001?redirect=https://attacker.example",
        "/ai/patients/p-001#fragment",
    ],
)
def test_hms_client_rejects_untrusted_path_shapes(hms_client: HmsApiClient, path: str) -> None:
    with pytest.raises(ExternalServiceError, match="Invalid HMS request path"):
        hms_client._build_url(path)


def test_hms_client_builds_only_same_origin_endpoint_urls(hms_client: HmsApiClient) -> None:
    assert hms_client._build_url("/ai/patients") == "https://hms.example.test/api/v1/ai/patients"


@pytest.mark.asyncio
async def test_hms_client_builds_safe_dynamic_endpoint_url(hms_client: HmsApiClient) -> None:
    response = MagicMock()
    response.json.return_value = {"data": {}}
    response.raise_for_status.return_value = None

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = response
        await hms_client.get_patient_snapshot("123e4567-e89b-12d3-a456-426614174000")

    assert mock_get.call_args.args[0] == (
        "https://hms.example.test/api/v1/ai/patients/123e4567-e89b-12d3-a456-426614174000/snapshot"
    )


@pytest.mark.asyncio
async def test_hms_client_rejects_unsafe_dynamic_path_segment(hms_client: HmsApiClient) -> None:
    with pytest.raises(ExternalServiceError, match="Invalid HMS request path segment"):
        await hms_client._get("/appointments", path_segment="../admin")
