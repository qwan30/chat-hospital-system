import hashlib
import math
from typing import Iterable, List

import httpx

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import ExternalServiceError


class EmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def embed(self, text: str) -> List[float]:
        if self.settings.embedding_provider == "ollama":
            return await self._embed_ollama(text)
        return deterministic_embedding(text, self.settings.embedding_dimensions)

    async def embed_many(self, texts: Iterable[str]) -> List[List[float]]:
        return [await self.embed(text) for text in texts]

    async def _embed_ollama(self, text: str) -> List[float]:
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/embed"
        payload = {"model": self.settings.embedding_model, "input": text}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExternalServiceError("Local Ollama embedding request failed.") from exc

        data = response.json()
        embeddings = data.get("embeddings")
        if not embeddings:
            raise ExternalServiceError("Ollama embedding response did not include embeddings.")
        vector = embeddings[0]
        return [float(value) for value in vector]


def deterministic_embedding(text: str, dimensions: int = 1024) -> List[float]:
    vector = [0.0] * dimensions
    words = text.lower().split()
    if not words:
        return vector
    for word in words:
        digest = hashlib.sha256(word.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
