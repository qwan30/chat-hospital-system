from dataclasses import dataclass
from typing import Iterable, List

from hospital_ai.services.ocr import OcrPage


@dataclass
class TextChunk:
    chunk_index: int
    page_number: int
    content: str
    token_count: int
    start_offset: int
    end_offset: int


class ChunkingService:
    def __init__(self, max_chars: int = 1200, overlap_chars: int = 150) -> None:
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk_pages(self, pages: Iterable[OcrPage]) -> List[TextChunk]:
        chunks: List[TextChunk] = []
        next_index = 0
        for page in pages:
            text = page.text.strip()
            if not text:
                continue
            start = 0
            while start < len(text):
                end = min(start + self.max_chars, len(text))
                content = text[start:end].strip()
                if content:
                    chunks.append(
                        TextChunk(
                            chunk_index=next_index,
                            page_number=page.page_number,
                            content=content,
                            token_count=len(content.split()),
                            start_offset=start,
                            end_offset=end,
                        )
                    )
                    next_index += 1
                if end >= len(text):
                    break
                start = max(0, end - self.overlap_chars)
        return chunks
