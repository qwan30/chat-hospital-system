from __future__ import annotations
from typing import Optional
"""Stub LLM provider for testing without external dependencies."""


from collections.abc import AsyncIterator

from hospital_ai.services.chat_utils import build_stub_answer
from hospital_ai.services.llm.base import BaseLLM, LLMMessage, LLMResponse


class StubLLM(BaseLLM):
    """Deterministic stub LLM for testing.

    Reuses the existing build_stub_answer logic for backward compatibility.
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
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        # Use last user message as the prompt
        prompt = ""
        for msg in reversed(messages):
            if msg.role == "user":
                prompt = msg.content
                break
        text = build_stub_answer(prompt)
        return LLMResponse(text=text, model=self._model, finish_reason="stop")

    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        response = await self.generate(messages, temperature=temperature, max_tokens=max_tokens)
        # Simulate streaming by yielding word by word
        words = response.text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
