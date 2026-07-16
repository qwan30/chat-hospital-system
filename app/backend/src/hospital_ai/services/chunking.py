"""Chunking service with table-aware splitting.
Dịch vụ Phân mảnh văn bản thông minh nhận diện bảng biểu (Table-aware Chunking Service).

Splits document pages into chunks while respecting table boundaries,
ensuring that markdown tables are never split across chunks.
Chia nhỏ các trang tài liệu thành các chunk nhưng bảo toàn tính toàn vẹn của bảng biểu markdown,
đảm bảo một bảng không bao giờ bị cắt vụn qua hai chunk khác nhau.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from hospital_ai.services.ocr import OcrPage


@dataclass
class TextChunk:
    """Cấu trúc dữ liệu biểu diễn một phân đoạn văn bản (chunk) sau khi cắt từ trang tài liệu OCR."""
    chunk_index: int
    page_number: int
    content: str
    token_count: int
    start_offset: int
    end_offset: int
    chunk_type: str = "text"  # "text" | "table" | "mixed"


class ChunkingService:
    """Dịch vụ thực hiện chia nhỏ văn bản (Chunking) theo ngữ nghĩa và giữ nguyên cấu trúc bảng biểu."""
    def __init__(self, max_chars: int = 1200, overlap_chars: int = 150) -> None:
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk_pages(self, pages: Iterable[OcrPage]) -> list[TextChunk]:
        """Thực hiện chia nhỏ danh sách các trang OCR thành các đoạn TextChunk hoàn chỉnh."""
        chunks: list[TextChunk] = []
        next_index = 0
        for page in pages:
            text = page.text.strip()
            if not text:
                continue

            # Split text into segments respecting table boundaries
            segments = _split_preserving_tables(text)

            for segment in segments:
                content = segment["content"].strip()
                seg_type = segment["type"]

                if not content:
                    continue

                if seg_type == "table":
                    # Tables are atomic — never split across chunks
                    if len(content) <= self.max_chars:
                        chunks.append(
                            TextChunk(
                                chunk_index=next_index,
                                page_number=page.page_number,
                                content=content,
                                token_count=len(content.split()),
                                start_offset=segment["start"],
                                end_offset=segment["end"],
                                chunk_type="table",
                            )
                        )
                        next_index += 1
                    else:
                        # Table exceeds max_chars — keep as single oversized chunk
                        chunks.append(
                            TextChunk(
                                chunk_index=next_index,
                                page_number=page.page_number,
                                content=content,
                                token_count=len(content.split()),
                                start_offset=segment["start"],
                                end_offset=segment["end"],
                                chunk_type="table",
                            )
                        )
                        next_index += 1
                else:
                    # Semantic chunking - respect sentence/paragraph boundaries
                    start = 0
                    while start < len(content):
                        max_end = min(start + self.max_chars, len(content))

                        # Find semantic split point
                        end = max_end
                        if max_end < len(content):
                            best_pos = -1
                            for sep in ("\n\n", "\n", ". ", "? ", "! "):
                                pos = content.rfind(sep, start, max_end)
                                if pos != -1 and pos > start + self.max_chars * 0.5:
                                    best_pos = pos + len(sep.rstrip())
                                    break

                            if best_pos != -1:
                                end = best_pos
                            else:
                                # Fallback to word boundary
                                pos = content.rfind(" ", start, max_end)
                                if pos != -1 and pos > start:
                                    end = pos

                        chunk_content = content[start:end].strip()
                        if chunk_content:
                            chunks.append(
                                TextChunk(
                                    chunk_index=next_index,
                                    page_number=page.page_number,
                                    content=chunk_content,
                                    token_count=len(chunk_content.split()),
                                    start_offset=segment["start"] + start,
                                    end_offset=segment["start"] + end,
                                    chunk_type="text",
                                )
                            )
                            next_index += 1

                        if end >= len(content):
                            break

                        # Find semantic overlap start
                        overlap_target = max(0, end - self.overlap_chars)
                        start = overlap_target
                        if overlap_target > 0:
                            pos = content.find(". ", overlap_target, end)
                            if pos != -1:
                                start = pos + 2
                            else:
                                pos = content.find(" ", overlap_target, end)
                                if pos != -1:
                                    start = pos + 1

        return chunks


def _split_preserving_tables(text: str) -> list[dict]:
    """Split text into segments, keeping markdown tables as atomic units.
    Phân tách văn bản thành các phân đoạn, giữ nguyên các bảng biểu markdown như một khối nguyên tử không thể chia nhỏ.

    Returns a list of dicts with keys: content, type ("text" or "table"),
    start (offset in original text), end (offset in original text).
    Trả về danh sách từ điển gồm các khóa: content, type ("text" hoặc "table"), start, end.
    """
    from hospital_ai.services.loaders.table_parser import detect_table_boundaries

    boundaries = detect_table_boundaries(text)
    if not boundaries:
        return [{"content": text, "type": "text", "start": 0, "end": len(text)}]

    segments: list[dict] = []
    prev_end = 0

    for table_start, table_end in boundaries:
        # Add text before the table
        if table_start > prev_end:
            pre_text = text[prev_end:table_start]
            if pre_text.strip():
                segments.append(
                    {
                        "content": pre_text,
                        "type": "text",
                        "start": prev_end,
                        "end": table_start,
                    }
                )

        # Add the table as an atomic segment
        table_text = text[table_start:table_end]
        if table_text.strip():
            segments.append(
                {
                    "content": table_text,
                    "type": "table",
                    "start": table_start,
                    "end": table_end,
                }
            )

        prev_end = table_end

    # Add remaining text after the last table
    if prev_end < len(text):
        remaining = text[prev_end:]
        if remaining.strip():
            segments.append(
                {
                    "content": remaining,
                    "type": "text",
                    "start": prev_end,
                    "end": len(text),
                }
            )

    return segments if segments else [{"content": text, "type": "text", "start": 0, "end": len(text)}]
