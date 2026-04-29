"""Base embedding interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class BaseEmbedding(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Embed a single text string."""

    @abstractmethod
    async def embed_many(self, texts: List[str]) -> List[List[float]]:
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
