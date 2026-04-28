from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://hospital_ai:hospital_ai@localhost:5432/hospital_ai"
    redis_url: str = "redis://localhost:6379/0"
    storage_root: Path = Path(".local_storage")
    worker_inline: bool = False
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:3001,http://127.0.0.1:3001"
    )

    dev_bearer_tokens: str = (
        "dev-doctor:doctor@example.test,"
        "dev-records:records@example.test,"
        "dev-security:security@example.test,"
        "dev-admin:admin@example.test"
    )

    embedding_provider: str = "deterministic"
    chat_provider: str = "stub"
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "bge-m3"
    chat_model: str = "qwen2.5:7b"
    embedding_dimensions: int = 1024
    retrieval_top_k: int = 5
    evidence_threshold: float = 0.2
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, ge=1)

    @validator("api_v1_prefix")
    def normalize_api_prefix(cls, value: str) -> str:
        if not value.startswith("/"):
            value = "/" + value
        return value.rstrip("/") or "/api/v1"

    @property
    def token_user_map(self) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        for item in self.dev_bearer_tokens.split(","):
            token_pair = item.strip()
            if not token_pair:
                continue
            token, sep, email = token_pair.partition(":")
            if sep and token.strip() and email.strip():
                mapping[token.strip()] = email.strip().lower()
        return mapping

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]

    class Config:
        env_prefix = "HOSPITAL_AI_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
