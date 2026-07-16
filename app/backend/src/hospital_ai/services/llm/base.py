"""Base LLM interface.
Giao diện trừu tượng cơ sở cho các nhà cung cấp mô hình ngôn ngữ lớn (LLM Provider Interface).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field


@dataclass
class LLMMessage:
    """A single message in a chat conversation.
    Cấu trúc dữ liệu biểu diễn một tin nhắn trong cuộc hội thoại.
    """

    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM completion.
    Cấu trúc dữ liệu biểu diễn kết quả trả về từ mô hình LLM.
    """

    text: str
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""


class BaseLLM(ABC):
    """Abstract base class for LLM providers.
    Lớp trừu tượng cơ sở định nghĩa chuẩn kết nối và sinh văn bản cho mọi nhà cung cấp LLM.
    """

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate a chat completion.
        Tạo sinh câu trả lời hoàn chỉnh từ danh sách tin nhắn hội thoại.

        Args:
            messages: List of conversation messages (Danh sách các tin nhắn hội thoại).
            temperature: Sampling temperature (Nhiệt độ lấy mẫu, 0.0 là xác định tuyệt đối).
            max_tokens: Maximum tokens to generate (Số token tối đa cho phép sinh ra).

        Returns:
            LLMResponse with the generated text (Đối tượng LLMResponse chứa văn bản kết quả).
        """

    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Stream a chat completion token by token.
        Tạo sinh câu trả lời dạng luồng (streaming), trả về từng token một.

        Args:
            messages: List of conversation messages (Danh sách tin nhắn).
            temperature: Sampling temperature (Nhiệt độ lấy mẫu).
            max_tokens: Maximum tokens to generate (Số token tối đa).

        Yields:
            Individual tokens as strings (Từng chuỗi token được sinh ra liên tục).
        """

    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider (e.g. 'openai', 'ollama').
        Trả về tên nhà cung cấp (ví dụ: 'openai', 'ollama', 'gemini').
        """

    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier.
        Trả về tên định danh của mô hình (ví dụ: 'gpt-4o-mini', 'gemini-1.5-pro').
        """
