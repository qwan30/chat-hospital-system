"""Document loaders — provider-agnostic file ingestion pipeline.

Inspired by kotaemon's loader architecture with composite fallback chain.
"""

from hospital_ai.services.loaders.base import BaseDocumentLoader, LoadedPage
from hospital_ai.services.loaders.composite import CompositeLoader

__all__ = ["BaseDocumentLoader", "LoadedPage", "CompositeLoader"]
