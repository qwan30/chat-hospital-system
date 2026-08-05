from __future__ import annotations
from uuid import UUID

from hospital_ai.evaluation.citation_parser import extract_cited_chunk_ids


def test_extract_cited_chunk_ids_markdown_and_explicit():
    chunk_1 = UUID("11111111-1111-1111-1111-111111111111")
    chunk_2 = UUID("22222222-2222-2222-2222-222222222222")
    chunk_3 = UUID("33333333-3333-3333-3333-333333333333")
    chunk_4 = UUID("44444444-4444-4444-4444-444444444444")

    available = {
        "E1": chunk_1,
        "1": chunk_3,
        str(chunk_2): chunk_2,
        str(chunk_4): chunk_4,
    }

    text = (
        "Patient has high Glucose [E1] and HbA1c 6.8% [Blood Report](chunk_id=22222222-2222-2222-2222-222222222222).\n"
        "Refer to section [1] and standalone UUID 44444444-4444-4444-4444-444444444444."
    )

    cited = extract_cited_chunk_ids(text, available)
    assert cited == {chunk_1, chunk_2, chunk_3, chunk_4}


def test_extract_cited_chunk_ids_unmatched_and_empty():
    chunk_1 = UUID("11111111-1111-1111-1111-111111111111")
    available = {"E1": chunk_1}

    # Text with unknown tag [E99] and random text
    text = "No matching citations here [E99] and empty search."
    cited = extract_cited_chunk_ids(text, available)
    assert cited == set()

    # Empty text
    assert extract_cited_chunk_ids("", available) == set()
