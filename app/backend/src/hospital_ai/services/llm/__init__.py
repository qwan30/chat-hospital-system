"""LLM provider abstraction layer.
Tầng trừu tượng hóa nhà cung cấp mô hình ngôn ngữ lớn (LLM Provider Abstraction Layer).

Inspired by kotaemon's llms/ architecture — provider-agnostic interface
for chat completion with swappable backends.
Lấy cảm hứng từ kiến trúc llms/ của kotaemon — cung cấp giao diện chuẩn hóa cho các tác vụ tạo sinh văn bản
không phụ thuộc vào nhà cung cấp cụ thể, dễ dàng chuyển đổi/thay thế các backend (OpenAI, Gemini, Ollama...).
"""

from hospital_ai.services.llm.base import BaseLLM, LLMResponse
from hospital_ai.services.llm.manager import LLMManager, get_llm_manager

__all__ = ["BaseLLM", "LLMResponse", "LLMManager", "get_llm_manager"]
