import hashlib
import math
import re
from typing import Dict, Iterable, List, Tuple

import httpx

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import ExternalServiceError


class EmbeddingService:
    """Embedding service with batch support, text normalization, and in-memory cache."""

    _cache: Dict[str, List[float]] = {}
    _cache_max_size: int = 2048

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def embed(self, text: str) -> List[float]:
        normalized = _normalize_text(text)
        cache_key = _cache_key(normalized, self.settings.embedding_provider)
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.settings.embedding_provider == "ollama":
            result = await self._embed_ollama(normalized)
        else:
            result = deterministic_embedding(normalized, self.settings.embedding_dimensions)

        self._put_cache(cache_key, result)
        return result

    async def embed_many(self, texts: Iterable[str]) -> List[List[float]]:
        """Batch embed with cache awareness and text normalization.

        For deterministic/stub providers, processes sequentially.
        For Ollama, batches texts that aren't cached.
        """
        text_list = [_normalize_text(t) for t in texts]
        if not text_list:
            return []

        results: List[Tuple[int, List[float]]] = []
        uncached: List[Tuple[int, str]] = []

        for i, text in enumerate(text_list):
            cache_key = _cache_key(text, self.settings.embedding_provider)
            if cache_key in self._cache:
                results.append((i, self._cache[cache_key]))
            else:
                uncached.append((i, text))

        if uncached:
            if self.settings.embedding_provider == "ollama":
                # Batch request to Ollama
                uncached_texts = [text for _, text in uncached]
                embeddings = await self._embed_ollama_batch(uncached_texts)
                for (idx, text), embedding in zip(uncached, embeddings):
                    cache_key = _cache_key(text, self.settings.embedding_provider)
                    self._put_cache(cache_key, embedding)
                    results.append((idx, embedding))
            else:
                for idx, text in uncached:
                    embedding = deterministic_embedding(text, self.settings.embedding_dimensions)
                    cache_key = _cache_key(text, self.settings.embedding_provider)
                    self._put_cache(cache_key, embedding)
                    results.append((idx, embedding))

        results.sort(key=lambda x: x[0])
        return [embedding for _, embedding in results]

    def _put_cache(self, key: str, value: List[float]) -> None:
        """Add to cache, evicting oldest entries if over size."""
        if len(self._cache) >= self._cache_max_size:
            # Evict oldest 25% of entries
            evict_count = self._cache_max_size // 4
            keys_to_remove = list(self._cache.keys())[:evict_count]
            for k in keys_to_remove:
                del self._cache[k]
        self._cache[key] = value

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

    async def _embed_ollama_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embed using Ollama's multi-input support."""
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/embed"
        payload = {"model": self.settings.embedding_model, "input": texts}
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExternalServiceError("Local Ollama batch embedding request failed.") from exc

        data = response.json()
        embeddings = data.get("embeddings")
        if not embeddings or len(embeddings) != len(texts):
            raise ExternalServiceError(
                f"Ollama batch embedding returned {len(embeddings or [])} results for {len(texts)} inputs."
            )
        return [[float(v) for v in vec] for vec in embeddings]


def _cache_key(text: str, provider: str) -> str:
    """Create a stable cache key from text and provider."""
    return hashlib.sha256(f"{provider}:{text}".encode("utf-8")).hexdigest()


_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_text(text: str) -> str:
    """Normalize text before embedding for improved retrieval consistency.

    Strips leading/trailing whitespace, collapses interior whitespace runs,
    and removes zero-width characters.
    """
    text = text.strip()
    text = text.replace("\u200b", "").replace("\ufeff", "")
    text = _WHITESPACE_RE.sub(" ", text)
    return text


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
