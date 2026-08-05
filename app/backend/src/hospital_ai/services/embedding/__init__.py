"""Embedding provider abstraction layer.

Provider-agnostic interface for text embedding with swappable backends.
"""
from __future__ import annotations

from hospital_ai.services.embedding.base import BaseEmbedding
from hospital_ai.services.embedding.manager import EmbeddingManager, get_embedding_manager

__all__ = ["BaseEmbedding", "EmbeddingManager", "get_embedding_manager"]
