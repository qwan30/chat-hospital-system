"""LLM Manager — registry and factory for LLM providers.
Bộ quản lý LLM (LLM Manager) — nơi đăng ký và khởi tạo (factory) các nhà cung cấp mô hình ngôn ngữ.

Inspired by kotaemon's ktem.llms.manager pattern.
Lấy cảm hứng từ mẫu thiết kế ktem.llms.manager của kotaemon.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from hospital_ai.core.config import Settings, get_settings
from hospital_ai.services.llm.base import BaseLLM
from hospital_ai.services.llm.instrumentation import InstrumentedLLM

logger = logging.getLogger(__name__)


class LLMManager:
    """Registry for LLM provider instances.
    Sổ đăng ký và quản lý các instance của nhà cung cấp LLM.

    Supports runtime switching between providers while maintaining
    a singleton instance per provider configuration.
    Hỗ trợ chuyển đổi linh hoạt ngay trong lúc chạy (runtime) giữa các provider khác nhau
    nhưng vẫn đảm bảo mỗi provider chỉ được khởi tạo một lần duy nhất (singleton instance).
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._providers: dict[str, BaseLLM] = {}
        self._default_provider: str | None = None

    def get(self, provider_name: str | None = None) -> BaseLLM:
        """Get an LLM provider instance.
        Lấy instance của LLM provider theo tên yêu cầu.

        Args:
            provider_name: Provider to use. Defaults to settings.chat_provider
                (Tên nhà cung cấp, mặc định theo cấu hình).

        Returns:
            Configured BaseLLM instance (Đối tượng LLM đã được cấu hình và bọc
            đo lường InstrumentedLLM).
        """
        name = provider_name or self._default_provider or self.settings.chat_provider

        if name in self._providers:
            return self._providers[name]

        llm = self._create_provider(name)
        llm = InstrumentedLLM(llm)
        self._providers[name] = llm
        logger.info("Initialized LLM provider: %s (model: %s)", name, llm.model_name())
        return llm

    def register(self, name: str, llm: BaseLLM) -> None:
        """Register a custom LLM provider instance.
        Đăng ký một instance LLM provider tùy chỉnh vào danh sách quản lý.
        """
        self._providers[name] = llm

    def set_default(self, provider_name: str) -> None:
        """Set the default provider name.
        Thiết lập tên nhà cung cấp mặc định.
        """
        self._default_provider = provider_name

    def list_providers(self) -> list:
        """List available provider names.
        Liệt kê danh sách các nhà cung cấp có sẵn (bao gồm mặc định và đã đăng ký).
        """
        return ["stub", "ollama", "openai", "gemini"] + list(self._providers.keys())

    def _create_provider(self, name: str) -> BaseLLM:
        """Factory method — creates a provider from settings.
        Phương thức factory — tự động khởi tạo instance LLM provider dựa theo cấu hình ứng dụng.
        """
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

        if name == "gemini":
            from hospital_ai.services.llm.gemini_provider import GeminiLLM

            return GeminiLLM(
                api_key=getattr(self.settings, "gemini_api_key", ""),
                model=getattr(self.settings, "gemini_chat_model", "gemini-2.0-flash"),
            )

        if name in self._providers:
            return self._providers[name]

        raise ValueError(f"Unknown LLM provider: '{name}'. Available: {', '.join(self.list_providers())}")


@lru_cache(maxsize=1)
def get_llm_manager(settings: Settings | None = None) -> LLMManager:
    """Get the singleton LLM manager instance.
    Trả về instance duy nhất (singleton) của LLMManager, được cache tự động bằng LRU.
    """
    return LLMManager(settings or get_settings())
