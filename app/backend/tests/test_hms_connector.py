from __future__ import annotations

import pytest

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.services.hms_connector import HmsApiClient


def _client() -> HmsApiClient:
    return HmsApiClient(Settings(hms_base_url="https://hms.example.test/api"))


def test_hms_url_builder_preserves_configured_origin() -> None:
    assert _client()._build_url("/ai/patients") == "https://hms.example.test/api/ai/patients"


@pytest.mark.parametrize(
    "path",
    [
        "https://attacker.example/steal",
        "//attacker.example/steal",
        "/ai/patients/../admin",
        "/ai/patients/%2e%2e/admin",
        "/ai/patients/unsafe\\segment",
        "/ai/patients?next=https://attacker.example",
    ],
)
def test_hms_url_builder_rejects_untrusted_path_shapes(path: str) -> None:
    with pytest.raises(ExternalServiceError):
        _client()._build_url(path)
