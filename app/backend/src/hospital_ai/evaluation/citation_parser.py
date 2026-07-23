from __future__ import annotations

import re
from uuid import UUID

_UUID_REGEX = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_BRACKET_REGEX = re.compile(r"\[([A-Za-z0-9_-]+)\]")


def extract_cited_chunk_ids(
    answer_text: str, available_chunks: dict[str, UUID]
) -> set[UUID]:
    """Extract cited chunk UUIDs from raw answer text.

    Supports:
    - Square bracket tags such as [E1], [1]
    - Markdown links with chunk_id parameter or standalone UUID strings
    """
    cited: set[UUID] = set()

    # Pre-index available chunk UUIDs for fast lookup
    available_uuid_values = set(available_chunks.values())

    # 1. Match all UUID pattern strings in text
    for uuid_match in _UUID_REGEX.findall(answer_text):
        try:
            val = UUID(uuid_match)
            if val in available_uuid_values or str(val) in available_chunks:
                cited.add(val)
        except ValueError:
            pass

    # 2. Match bracket tags such as [E1], [1]
    for tag_match in _BRACKET_REGEX.findall(answer_text):
        if tag_match in available_chunks:
            chunk_val = available_chunks[tag_match]
            if isinstance(chunk_val, UUID):
                cited.add(chunk_val)

    return cited
