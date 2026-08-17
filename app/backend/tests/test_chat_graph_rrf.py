"""Tests for GraphRAG RRF fusion and prompt citation extraction robustness."""

from __future__ import annotations

import uuid

from hospital_ai.services.bm25 import reciprocal_rank_fusion
from hospital_ai.services.chat_utils import (
    build_grounded_prompt,
    extract_citation_ids,
    parse_prompt_evidence,
)
from hospital_ai.services.claim_validation import ClaimParser
from hospital_ai.services.retrieval import RetrievedChunk


def _make_chunk(
    evidence_id: str,
    chunk_id: uuid.UUID,
    doc_id: uuid.UUID,
    content: str,
    score: float = 0.9,
    method: str = "vector",
) -> RetrievedChunk:
    return RetrievedChunk(
        evidence_id=evidence_id,
        document_id=doc_id,
        document_title="Clinical Doc",
        page=1,
        chunk_id=chunk_id,
        score=score,
        content=content,
        metadata={"retrieval_method": method},
    )


def test_reciprocal_rank_fusion_with_graph():
    """Verify that chunks present in both vector and graph lists get boosted via RRF."""
    doc_id = uuid.uuid4()
    c1 = uuid.uuid4()
    c2 = uuid.uuid4()
    c3 = uuid.uuid4()

    vector_list = [
        _make_chunk("E1", c1, doc_id, "Patient has chest pain", score=0.85, method="vector"),
        _make_chunk("E2", c2, doc_id, "Patient is taking aspirin", score=0.75, method="vector"),
    ]
    graph_list = [
        _make_chunk("E1", c2, doc_id, "Patient is taking aspirin", score=0.90, method="graph"),
        _make_chunk("E2", c3, doc_id, "Patient diagnosed with CAD", score=0.80, method="graph"),
    ]

    fused = reciprocal_rank_fusion(vector_list, graph_list, top_k=3)

    assert len(fused) == 3
    # c2 was in both lists (rank 1 in vector, rank 0 in graph) -> should have highest combined RRF score
    assert fused[0].chunk_id == c2
    assert fused[0].evidence_id == "E1"
    assert fused[1].evidence_id == "E2"
    assert fused[2].evidence_id == "E3"
    assert fused[0].metadata["retrieval_method"] == "hybrid_rrf"


def test_extract_citation_ids_multi_and_whitespace():
    """Verify robust citation extraction with multiple citations and whitespace."""
    text1 = "Bệnh nhân có tiền sử suy tim [E1] và tăng huyết áp [E2]."
    assert extract_citation_ids(text1) == {"E1", "E2"}

    text2 = "Sử dụng phác đồ chuẩn [E1, E2] kết hợp theo dõi [G1]."
    assert extract_citation_ids(text2) == {"E1", "E2", "G1"}

    text3 = "Liều dùng khuyến nghị [E 1][E2]."
    assert extract_citation_ids(text3) == {"E1", "E2"}


def test_claim_parser_multi_citations():
    """Verify that ClaimParser splits bracketed multi-citations into individual IDs."""
    parser = ClaimParser()
    claims = parser.parse("Liều dùng apixaban là 5mg [E1, E2].")
    assert len(claims) == 1
    assert claims[0].evidence_ids == ["E1", "E2"]


def test_build_grounded_prompt_and_parse():
    """Verify prompt formatting and evidence round-trip parsing."""
    doc_id = uuid.uuid4()
    c1 = uuid.uuid4()
    evidence = [
        _make_chunk("E1", c1, doc_id, "Blood pressure: 120/80 mmHg", score=0.9),
    ]
    prompt = build_grounded_prompt("What is BP?", evidence)

    assert "[E1] Document: Clinical Doc; page: 1" in prompt
    assert "Blood pressure: 120/80 mmHg" in prompt
    assert "Instructions:" in prompt

    parsed = parse_prompt_evidence(prompt)
    assert len(parsed) == 1
    assert parsed[0][0] == "E1"
    assert "Blood pressure: 120/80 mmHg" in parsed[0][1]
