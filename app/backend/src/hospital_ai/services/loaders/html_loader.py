"""HTML document loader using BeautifulSoup."""
from __future__ import annotations


from pathlib import Path

from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.services.loaders.base import BaseDocumentLoader, LoadedPage


class HtmlLoader(BaseDocumentLoader):
    """Extract readable text from HTML files.

    Strips tags and extracts meaningful text content.
    """

    def supported_extensions(self) -> set[str]:
        return {".html", ".htm", ".mhtml"}

    def load(self, file_path: Path, mime_type: str = "") -> list[LoadedPage]:
        if not file_path.exists():
            raise ExternalServiceError(f"HTML file not found: {file_path}")

        raw = file_path.read_text(encoding="utf-8", errors="replace")

        try:
            from bs4 import BeautifulSoup  # type: ignore[import-untyped]

            soup = BeautifulSoup(raw, "html.parser")
            # Remove script and style elements
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
        except ImportError:
            # Fallback: basic regex-based tag stripping
            import re

            text = re.sub(r"<script[^>]*>.*?</script>", "", raw, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<[^>]+>", "\n", text)
            text = re.sub(r"\n{3,}", "\n\n", text).strip()

        if not text.strip():
            raise ExternalServiceError("HTML file contains no extractable text.")

        title = ""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(raw, "html.parser")
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)
        except ImportError:
            pass

        metadata = {"title": title} if title else {}
        return [LoadedPage(page_number=1, text=text, confidence=1.0, metadata=metadata)]
