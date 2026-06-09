"""Ollama LLM provider — local models via Ollama API."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.services.llm.base import BaseLLM, LLMMessage, LLMResponse


class OllamaLLM(BaseLLM):
    """Local LLM via Ollama REST API."""

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b",
        timeout: int = 120,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def provider_name(self) -> str:
        return "ollama"

    def model_name(self) -> str:
        return self._model

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        url = f"{self._base_url}/api/chat"
        payload = self._build_payload(messages, temperature, max_tokens, stream=False)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Ollama chat request failed: {exc}") from exc

        data = response.json()
        message = data.get("message") or {}
        content = message.get("content")
        if not content:
            raise ExternalServiceError("Ollama chat response did not include message content.")

        return LLMResponse(
            text=str(content),
            model=data.get("model", self._model),
            finish_reason=data.get("done_reason", "stop"),
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        url = f"{self._base_url}/api/chat"
        payload = self._build_payload(messages, temperature, max_tokens, stream=True)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                            message = chunk.get("message", {})
                            content = message.get("content", "")
                            if content:
                                yield content
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Ollama streaming request failed: {exc}") from exc

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
            "stream": stream,
            "options": {"temperature": temperature},
        }
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens
        return payload
