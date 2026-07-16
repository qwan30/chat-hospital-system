"""Stub LLM provider for testing without external dependencies.
Nhà cung cấp giả lập (Stub LLM Provider) phục vụ kiểm thử đơn vị và chạy thử mà không cần gọi API mạng bên ngoài.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from hospital_ai.services.chat_utils import build_stub_answer
from hospital_ai.services.llm.base import BaseLLM, LLMMessage, LLMResponse


class StubLLM(BaseLLM):
    """Deterministic stub LLM for testing.
    Mô hình giả lập tất định (deterministic) dùng cho kiểm thử.

    Reuses the existing build_stub_answer logic for backward compatibility.
    Tái sử dụng logic trả lời giả lập từ `build_stub_answer` để đảm bảo tương thích ngược với các test case hiện có.
    """

    def __init__(self, model: str = "stub") -> None:
        self._model = model

    def provider_name(self) -> str:
        return "stub"

    def model_name(self) -> str:
        return self._model

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Lấy tin nhắn người dùng cuối cùng trong chuỗi hội thoại, sinh câu trả lời giả lập từ `build_stub_answer`."""
        # Use last user message as the prompt
        prompt = ""
        for msg in reversed(messages):
            if msg.role == "user":
                prompt = msg.content
                break
        # If the prompt is a grounded prompt, extract the question
        question_for_check = prompt
        if "Question: " in prompt:
            question_for_check = prompt.split("Question: ")[-1].split("\n")[0].strip()

        from hospital_ai.services.chat_utils import is_chitchat_query
        
        is_chit = is_chitchat_query(question_for_check)
        if is_chit:
            import unicodedata
            lower_q = unicodedata.normalize("NFC", question_for_check.lower())
            if "xin chào" in lower_q or "chào" in lower_q or "hello" in lower_q or "hi" in lower_q:
                text = "Xin chào! Tôi là trợ lý ảo HMS AI Copilot. Tôi có thể giúp gì cho bạn hôm nay?"
            elif "cảm ơn" in lower_q or "cám ơn" in lower_q or "thank" in lower_q or "thanks" in lower_q:
                text = "Không có gì! Nếu bạn cần thêm thông tin gì khác, cứ hỏi tôi nhé."
            else:
                text = "Tôi là HMS AI Copilot, trợ lý thông tin bệnh viện của bạn. Tôi có thể giúp gì cho bạn?"
        else:
            text = build_stub_answer(prompt)
        return LLMResponse(text=text, model=self._model, finish_reason="stop")

    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Giả lập trả về luồng streaming bằng cách cắt nhỏ câu trả lời ra từng từ (word by word)."""
        response = await self.generate(messages, temperature=temperature, max_tokens=max_tokens)
        # Simulate streaming by yielding word by word
        words = response.text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
