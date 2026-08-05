"""Google Gemini LLM provider.

Uses the Gemini REST API (generativelanguage.googleapis.com).
API key is passed as a query parameter.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Optional

import httpx

from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.services.llm.base import BaseLLM, LLMMessage, LLMResponse


class GeminiLLM(BaseLLM):
    """Google Gemini chat completion provider via REST API."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gemini-2.0-flash",
        timeout: int = 120,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def provider_name(self) -> str:
        return "gemini"

    def model_name(self) -> str:
        return self._model

    def _base_url(self) -> str:
        return "https://generativelanguage.googleapis.com/v1beta"

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        url = f"{self._base_url()}/models/{self._model}:generateContent?key={self._api_key}"
        payload = self._build_payload(messages, temperature, max_tokens)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Gemini chat request failed: {exc}") from exc

        data = response.json()
        return self._parse_response(data)

    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        url = f"{self._base_url()}/models/{self._model}:streamGenerateContent?alt=sse&key={self._api_key}"
        payload = self._build_payload(messages, temperature, max_tokens)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if not data_str:
                            continue
                        try:
                            chunk = json.loads(data_str)
                            candidates = chunk.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for part in parts:
                                    text = part.get("text", "")
                                    if text:
                                        yield text
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Gemini streaming request failed: {exc}") from exc

    def _build_payload(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: Optional[int],
    ) -> dict:
        """Build Gemini API request payload from internal message format."""
        contents = []
        system_instruction = None

        for m in messages:
            if m.role == "system":
                system_instruction = {"parts": [{"text": m.content}]}
            else:
                role = "model" if m.role == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": m.content}]})

        if not contents:
            contents = [{"role": "user", "parts": [{"text": "Hello"}]}]

        payload: dict = {"contents": contents}
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        gen_config: dict = {"temperature": temperature}
        if max_tokens is not None:
            gen_config["maxOutputTokens"] = max_tokens
        payload["generationConfig"] = gen_config

        return payload

    def _parse_response(self, data: dict) -> LLMResponse:
        """Parse Gemini API response into LLMResponse."""
        candidates = data.get("candidates", [])
        text = ""
        finish_reason = ""

        if candidates:
            candidate = candidates[0]
            finish_reason = candidate.get("finishReason", "")
            parts = candidate.get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)

        usage = data.get("usageMetadata", {})

        return LLMResponse(
            text=text,
            model=self._model,
            usage={
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0),
                "total_tokens": usage.get("totalTokenCount", 0),
            },
            finish_reason=finish_reason,
        )
