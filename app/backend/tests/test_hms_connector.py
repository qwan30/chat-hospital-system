"""Security contracts for the HMS HTTP client."""

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
