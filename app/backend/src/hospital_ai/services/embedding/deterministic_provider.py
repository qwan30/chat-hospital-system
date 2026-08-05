"""Deterministic embedding provider for testing.

Wraps the existing deterministic_embedding function from embeddings.py.
"""
from __future__ import annotations


from hospital_ai.services.embedding.base import BaseEmbedding
from hospital_ai.services.embeddings import deterministic_embedding


class DeterministicEmbedding(BaseEmbedding):
    """Deterministic (hash-based) embedding for testing without external services."""

    def __init__(self, dims: int = 1024) -> None:
        self._dims = dims

    def provider_name(self) -> str:
        return "deterministic"

    def model_name(self) -> str:
        return "deterministic-hash"

    def dimensions(self) -> int:
        return self._dims

    async def embed(self, text: str) -> list[float]:
        return deterministic_embedding(text, self._dims)

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [deterministic_embedding(t, self._dims) for t in texts]
