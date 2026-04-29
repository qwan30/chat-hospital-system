"""OpenAI embedding provider."""

from __future__ import annotations

from typing import Dict, List

import httpx

from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.services.embedding.base import BaseEmbedding


class OpenAIEmbedding(BaseEmbedding):
    """OpenAI text-embedding-3 compatible provider."""

    def __init__(
        self,
        *,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        model: str = "text-embedding-3-small",
        dims: int = 1536,
        timeout: int = 60,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._dims = dims
        self._timeout = timeout

    def provider_name(self) -> str:
        return "openai"

    def model_name(self) -> str:
        return self._model

    def dimensions(self) -> int:
        return self._dims

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def embed(self, text: str) -> List[float]:
        results = await self.embed_many([text])
        return results[0]

    async def embed_many(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        url = f"{self._base_url}/embeddings"
        payload = {
            "model": self._model,
            "input": texts,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=payload, headers=self._headers())
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"OpenAI embedding request failed: {exc}") from exc

        data = response.json()
        embeddings = data.get("data", [])
        if len(embeddings) != len(texts):
            raise ExternalServiceError(
                f"OpenAI returned {len(embeddings)} embeddings for {len(texts)} inputs."
            )

        # Sort by index to maintain order
        embeddings.sort(key=lambda x: x.get("index", 0))
        return [item["embedding"] for item in embeddings]
