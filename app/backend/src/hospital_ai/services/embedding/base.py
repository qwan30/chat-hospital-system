from __future__ import annotations
"""Base embedding interface."""


from abc import ABC, abstractmethod


class BaseEmbedding(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Embed a single text string."""

    @abstractmethod
    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts (batch)."""

    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""

    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier."""

    @abstractmethod
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
