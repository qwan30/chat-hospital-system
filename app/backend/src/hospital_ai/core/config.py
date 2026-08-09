from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://hospital_ai:hospital_ai@localhost:5432/hospital_ai"
    redis_url: str = "redis://localhost:6379/0"
    storage_root: Path = Path(".local_storage")
    storage_backend: str = "local"
    r2_endpoint: str = ""
    r2_bucket: str = ""
    r2_region: str = "auto"
    r2_access_key_id: str = Field(default="", repr=False)
    r2_secret_access_key: str = Field(default="", repr=False)
    worker_inline: bool = False
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:8082,http://127.0.0.1:8082"
    dev_auto_grant_access: bool = False
    enable_break_glass: bool = False
    demo_mode: bool = True
    allow_self_approval_for_synthetic_data: bool = False
    disable_guardrails: bool = False
    cdi_v2_dual_read: bool = Field(default=False)
    cdi_v2_active_generation_reads: bool = Field(default=False)
    cdi_v2_authoring_enabled: bool = Field(default=False)
    # Seconds allowed for an llm-guard scan before the guardrail fails closed.
    # The prompt-injection model takes ~4s per scan on CPU, so the previous
    # hardcoded 3.0 timed out on every request and refused safe questions as
    # "security policy violations". Raise this on slow hardware rather than
    # disabling guardrails outright.
    guardrail_timeout_seconds: float = 15.0

    otel_enabled: bool = False
    otel_exporter_otlp_endpoint: str = "http://localhost:4318"
    prometheus_enabled: bool = True
    log_format: str = "text"

    # Default tokens are convenience shortcuts for `environment == "local"` only.
    # `token_user_map` refuses to surface them in any other environment unless
    # the operator explicitly overrides via HOSPITAL_AI_DEV_BEARER_TOKENS, so a
    # forgotten env-var in production cannot silently grant high-privilege
    # access via the seeded dev users.  See audit finding F-SEC-001.
    dev_bearer_tokens: str = (
        "dev-doctor:doctor@example.test,"
        "dev-nurse:nurse@example.test,"
        "dev-pharmacist:pharmacist@example.test,"
        "dev-records:records@example.test,"
        "dev-security:security@example.test,"
        "dev-admin:admin@example.test,"
        "dev-frontdesk:frontdesk@example.test"
    )

    embedding_provider: str = "ollama"
    chat_provider: str = "stub"
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "bge-m3"
    chat_model: str = "qwen2.5:7b"
    embedding_dimensions: int = 1024
    retrieval_top_k: int = 5
    evidence_threshold: float = 0.2
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    ocr_memory_budget_mb: int = Field(default=4096, ge=512)
    ocr_idle_unload_seconds: float = Field(default=300.0, ge=0)
    ocr_models_path: Path = Path(".models")

    # OpenAI / OpenAI-compatible provider
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # Google Gemini provider
    gemini_api_key: str = ""
    gemini_chat_model: str = "gemini-2.0-flash"

    # RAG tuning
    chunk_size: int = Field(default=512, ge=64, le=4096)
    chunk_overlap: int = Field(default=64, ge=0, le=512)
    system_prompt: str = (
        "You are a hospital knowledge assistant. Answer only from the evidence. "
        "Cite every factual claim using evidence IDs like [E1]."
    )
    streaming_enabled: bool = True
    prometheus_enabled: bool = True

    # Reranker settings
    reranker_provider: str = "keyword"  # keyword | cross_encoder | tei | cohere
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    reranker_top_k: int = 5
    reranker_tei_url: str = ""
    cohere_api_key: str = ""

    # Hybrid search settings
    retrieval_mode: str = "vector"  # vector | bm25 | hybrid
    bm25_weight: float = 0.4
    vector_weight: float = 0.6
    enable_hyde: bool = False
    ab_test_retrieval: bool = False

    # HMS integration
    hms_base_url: str = "http://localhost:8080/api/v1"
    hms_api_key: str = ""
    hms_sync_enabled: bool = False
    hms_sync_timeout_seconds: int = 30

    # JWT / OIDC authentication (see docs/04-architecture/security-architecture.md)
    # When jwt_issuer is empty, JWT validation is skipped and static tokens are used.
    # For HS256: set jwt_hmac_secret and jwt_algorithm="HS256"
    # For RS256: set jwks_url and install optional jwt-rs256 extras (cryptography)
    jwt_issuer: str = ""
    jwt_audience: str = ""
    jwks_url: str = ""
    jwt_hmac_secret: str = ""
    jwt_algorithm: str = "RS256"

    @validator("api_v1_prefix")
    def normalize_api_prefix(cls, value: str) -> str:
        if not value.startswith("/"):
            value = "/" + value
        return value.rstrip("/") or "/api/v1"

    @property
    def token_user_map(self) -> dict[str, str]:
        # F-SEC-001: refuse the committed default in any non-local
        # environment unless the operator explicitly overrode the value.
        # If the operator sets dev_bearer_tokens to anything (including the
        # default value verbatim) via the env-var, the value is treated as
        # an explicit acknowledgment and accepted.
        if (
            self.environment != "local"
            and self.dev_bearer_tokens == self.__class__.__fields__["dev_bearer_tokens"].default
        ):
            return {}

        mapping: dict[str, str] = {}
        for item in self.dev_bearer_tokens.split(","):
            token_pair = item.strip()
            if not token_pair:
                continue
            token, sep, email = token_pair.partition(":")
            if sep and token.strip() and email.strip():
                mapping[token.strip()] = email.strip().lower()
        return mapping

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]

    class Config:
        env_prefix = "HOSPITAL_AI_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
