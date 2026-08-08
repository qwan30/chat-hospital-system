"""Base document loader interface.

All loaders must implement the `load` method which returns a list of
LoadedPage objects, each representing a page/section of the document.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LoadedPage:
    """A single page/section extracted from a document."""

    page_number: int
    text: str
    confidence: float = 1.0
    metadata: dict[str, str] = field(default_factory=dict)


class BaseDocumentLoader(ABC):
    """Abstract base class for document loaders."""

    @abstractmethod
    def supported_extensions(self) -> set[str]:
        """Return set of file extensions this loader handles (e.g. {'.pdf', '.PDF'})."""

    @abstractmethod
    def load(self, file_path: Path, mime_type: str = "") -> list[LoadedPage]:
        """Extract pages/sections from the given file.

        Args:
            file_path: Path to the file on disk.
            mime_type: Optional MIME type hint.

        Returns:
            List of LoadedPage objects.

        Raises:
            ExternalServiceError: If extraction fails.
        """

    def can_handle(self, file_path: Path, mime_type: str = "") -> bool:
        """Check whether this loader can process the given file."""
        return file_path.suffix.lower() in self.supported_extensions()
