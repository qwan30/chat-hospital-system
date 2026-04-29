"""LLM Manager — registry and factory for LLM providers.

Inspired by kotaemon's ktem.llms.manager pattern.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict, Optional

from hospital_ai.core.config import Settings, get_settings
from hospital_ai.services.llm.base import BaseLLM

logger = logging.getLogger(__name__)


class LLMManager:
    """Registry for LLM provider instances.

    Supports runtime switching between providers while maintaining
    a singleton instance per provider configuration.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._providers: Dict[str, BaseLLM] = {}
        self._default_provider: Optional[str] = None

    def get(self, provider_name: Optional[str] = None) -> BaseLLM:
        """Get an LLM provider instance.

        Args:
            provider_name: Provider to use. Defaults to settings.chat_provider.

        Returns:
            Configured BaseLLM instance.
        """
        name = provider_name or self._default_provider or self.settings.chat_provider

        if name in self._providers:
            return self._providers[name]

        llm = self._create_provider(name)
        self._providers[name] = llm
        logger.info("Initialized LLM provider: %s (model: %s)", name, llm.model_name())
        return llm

    def register(self, name: str, llm: BaseLLM) -> None:
        """Register a custom LLM provider instance."""
        self._providers[name] = llm

    def set_default(self, provider_name: str) -> None:
        """Set the default provider name."""
        self._default_provider = provider_name

    def list_providers(self) -> list:
        """List available provider names."""
        return ["stub", "ollama", "openai"] + list(self._providers.keys())

    def _create_provider(self, name: str) -> BaseLLM:
        """Factory method — creates a provider from settings."""
        if name == "stub":
            from hospital_ai.services.llm.stub_provider import StubLLM
            return StubLLM()

        if name == "ollama":
            from hospital_ai.services.llm.ollama_provider import OllamaLLM
            return OllamaLLM(
                base_url=self.settings.ollama_base_url,
                model=self.settings.chat_model,
            )

        if name == "openai":
            from hospital_ai.services.llm.openai_provider import OpenAILLM
            return OpenAILLM(
                api_key=getattr(self.settings, "openai_api_key", ""),
                base_url=getattr(self.settings, "openai_base_url", "https://api.openai.com/v1"),
                model=getattr(self.settings, "openai_chat_model", "gpt-4o-mini"),
            )

        if name in self._providers:
            return self._providers[name]

        raise ValueError(
            f"Unknown LLM provider: '{name}'. "
            f"Available: {', '.join(self.list_providers())}"
        )


@lru_cache(maxsize=1)
def get_llm_manager(settings: Optional[Settings] = None) -> LLMManager:
    """Get the singleton LLM manager instance."""
    return LLMManager(settings or get_settings())
