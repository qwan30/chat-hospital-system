from __future__ import annotations
"""Ollama embedding provider — local embedding models."""


import httpx

from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.services.embedding.base import BaseEmbedding


class OllamaEmbedding(BaseEmbedding):
    """Local embedding via Ollama API."""

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        dims: int = 768,
        timeout: int = 60,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._dims = dims
        self._timeout = timeout

    def provider_name(self) -> str:
        return "ollama"

    def model_name(self) -> str:
        return self._model

    def dimensions(self) -> int:
        return self._dims

    async def embed(self, text: str) -> list[float]:
        results = await self.embed_many([text])
        return results[0]

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        url = f"{self._base_url}/api/embed"
        payload = {"model": self._model, "input": texts}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Ollama embedding request failed: {exc}") from exc

        data = response.json()
        embeddings = data.get("embeddings")
        if not embeddings or len(embeddings) != len(texts):
            raise ExternalServiceError(f"Ollama returned {len(embeddings or [])} embeddings for {len(texts)} inputs.")
        return [[float(v) for v in vec] for vec in embeddings]
