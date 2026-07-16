"""Embedding Manager — registry and factory for embedding providers."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

from hospital_ai.core.config import Settings, get_settings
from hospital_ai.services.embedding.base import BaseEmbedding

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Registry for embedding provider instances."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._providers: dict[str, BaseEmbedding] = {}

    def get(self, provider_name: Optional[str] = None) -> BaseEmbedding:
        """Get an embedding provider instance."""
        name = provider_name or self.settings.embedding_provider

        if name in self._providers:
            return self._providers[name]

        provider = self._create_provider(name)
        self._providers[name] = provider
        logger.info("Initialized embedding provider: %s (model: %s)", name, provider.model_name())
        return provider

    def register(self, name: str, provider: BaseEmbedding) -> None:
        """Register a custom embedding provider."""
        self._providers[name] = provider

    def list_providers(self) -> list:
        """List available provider names."""
        return ["deterministic", "ollama", "openai"] + list(self._providers.keys())

    def _create_provider(self, name: str) -> BaseEmbedding:
        if name == "deterministic":
            from hospital_ai.services.embedding.deterministic_provider import DeterministicEmbedding

            return DeterministicEmbedding(dims=self.settings.embedding_dimensions)

        if name == "ollama":
            from hospital_ai.services.embedding.ollama_provider import OllamaEmbedding

            return OllamaEmbedding(
                base_url=self.settings.ollama_base_url,
                model=self.settings.embedding_model,
                dims=self.settings.embedding_dimensions,
            )

        if name == "openai":
            from hospital_ai.services.embedding.openai_provider import OpenAIEmbedding

            return OpenAIEmbedding(
                api_key=getattr(self.settings, "openai_api_key", ""),
                base_url=getattr(self.settings, "openai_base_url", "https://api.openai.com/v1"),
                model=getattr(self.settings, "openai_embedding_model", "text-embedding-3-small"),
                dims=self.settings.embedding_dimensions,
            )

        raise ValueError(f"Unknown embedding provider: '{name}'. Available: {', '.join(self.list_providers())}")


@lru_cache(maxsize=1)
def get_embedding_manager(settings: Optional[Settings] = None) -> EmbeddingManager:
    """Get the singleton embedding manager instance."""
    return EmbeddingManager(settings or get_settings())
