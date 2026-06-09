"""OpenAI-compatible LLM provider.

Works with OpenAI API, Azure OpenAI, and any OpenAI-compatible endpoint
(Groq, Together, Mistral, etc.)
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx

from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.services.llm.base import BaseLLM, LLMMessage, LLMResponse


class OpenAILLM(BaseLLM):
    """OpenAI-compatible chat completion provider."""

    def __init__(
        self,
        *,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: int = 120,
        default_system_prompt: str = "",
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._default_system_prompt = default_system_prompt

    def provider_name(self) -> str:
        return "openai"

    def model_name(self) -> str:
        return self._model

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        url = f"{self._base_url}/chat/completions"
        payload = self._build_payload(messages, temperature, max_tokens, stream=False)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=payload, headers=self._headers())
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"OpenAI chat request failed: {exc}") from exc

        data = response.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})

        return LLMResponse(
            text=message.get("content", ""),
            model=data.get("model", self._model),
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason", ""),
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        url = f"{self._base_url}/chat/completions"
        payload = self._build_payload(messages, temperature, max_tokens, stream=True)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream("POST", url, json=payload, headers=self._headers()) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        import json

                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"OpenAI streaming request failed: {exc}") from exc

    def _build_payload(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int | None,
        stream: bool,
    ) -> dict:
        payload: dict = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": stream,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        return payload
