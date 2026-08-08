from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

import pytest

from hospital_ai.core.config import Settings
from hospital_ai.services.storage import get_storage_service, parse_r2_uri


def test_settings_load_r2_environment_names(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSPITAL_AI_STORAGE_BACKEND", "r2")
    monkeypatch.setenv("HOSPITAL_AI_R2_ENDPOINT", "https://account.r2.cloudflarestorage.com")
    monkeypatch.setenv("HOSPITAL_AI_R2_BUCKET", "hospital-documents")
    monkeypatch.setenv("HOSPITAL_AI_R2_REGION", "auto")
    monkeypatch.setenv("HOSPITAL_AI_R2_ACCESS_KEY_ID", "test-access")
    monkeypatch.setenv("HOSPITAL_AI_R2_SECRET_ACCESS_KEY", "test-secret")

    settings = Settings()

    assert settings.storage_backend == "r2"
    endpoint = urlsplit(settings.r2_endpoint)
    assert endpoint.scheme == "https"
    assert endpoint.hostname == "account.r2.cloudflarestorage.com"
    assert settings.r2_bucket == "hospital-documents"
    assert settings.r2_region == "auto"
    assert settings.r2_access_key_id == "test-access"
    assert settings.r2_secret_access_key == "test-secret"
    assert "test-secret" not in repr(settings)


def test_factory_rejects_unknown_backend() -> None:
    with pytest.raises(ValueError, match="storage backend"):
        get_storage_service(Settings(storage_backend="gcs"))


def test_r2_uri_parser_returns_object_key_for_valid_uri() -> None:
    assert parse_r2_uri("r2://patients/documents/report.txt") == "patients/documents/report.txt"


@pytest.mark.parametrize(
    "uri",
    [
        "r2://",
        "r2://patients/../secrets.txt",
        "r2://patients/./secret.txt",
        "r2:///absolute.txt",
        "r2://patients\\secret.txt",
        "r2://patients/file.txt?download=1",
        "r2://patients/file.txt#fragment",
        "file://patients/file.txt",
    ],
)
def test_r2_uri_parser_rejects_unsafe_or_wrong_scheme(uri: str) -> None:
    with pytest.raises(ValueError):
        parse_r2_uri(uri)


@pytest.mark.parametrize("uri", ["r2://patients//secret.txt", "r2://patients/a\x00.txt"])
def test_r2_uri_parser_rejects_empty_segments_and_control_characters(uri: str) -> None:
    with pytest.raises(ValueError):
        parse_r2_uri(uri)


def test_frontend_source_contains_no_r2_credentials() -> None:
    frontend_src = Path(__file__).resolve().parents[2] / "frontend" / "src"
    source = "\n".join(path.read_text(encoding="utf-8") for path in frontend_src.rglob("*.ts*"))

    assert "HOSPITAL_AI_R2_ACCESS_KEY_ID" not in source
    assert "HOSPITAL_AI_R2_SECRET_ACCESS_KEY" not in source
