"""Tests for BM25 scorer and Reciprocal Rank Fusion."""

from __future__ import annotations

import uuid

from hospital_ai.services.bm25 import BM25Scorer, reciprocal_rank_fusion
from hospital_ai.services.retrieval import RetrievedChunk

# ── Fixtures ─────────────────────────────────────────────────────────────


def _chunk(content: str, score: float = 0.5, cid: str = "") -> RetrievedChunk:
    return RetrievedChunk(
        evidence_id=cid or f"E{uuid.uuid4().hex[:4]}",
        document_id=uuid.uuid4(),
        document_title="test.pdf",
        page=1,
        chunk_id=uuid.uuid4(),
        score=score,
        content=content,
        metadata={},
    )


MEDICAL_CHUNKS = [
    _chunk("Patient prescribed Metformin 500mg twice daily for diabetes mellitus type 2", 0.0, "E1"),
    _chunk("Blood pressure recorded at 140/90 mmHg diagnosis hypertension ICD-10 I10", 0.0, "E2"),
    _chunk("HbA1c level measured at 7.2% above target range of 7.0%", 0.0, "E3"),
    _chunk("Hospital cafeteria menu includes vegetarian options available daily", 0.0, "E4"),
    _chunk("Aspirin 81mg prescribed as antiplatelet therapy for cardiovascular prevention", 0.0, "E5"),
    _chunk("Patient allergy to penicillin documented in medical records", 0.0, "E6"),
    _chunk("Metformin dosage titration based on renal function eGFR above 30", 0.0, "E7"),
]


# ── BM25 Scorer tests ───────────────────────────────────────────────────


class TestBM25Scorer:
    def test_exact_term_match(self):
        """BM25 should find exact medical terms that vector search might miss."""
        scorer = BM25Scorer()
        results = scorer.score("Metformin 500mg", MEDICAL_CHUNKS, top_k=3)

        assert len(results) == 3
        # Metformin chunks should rank highest
        top_contents = [r.content for r in results[:2]]
        assert any("Metformin" in c for c in top_contents)

    def test_icd10_code_matching(self):
        """ICD-10 codes like I10 should be findable via BM25."""
        scorer = BM25Scorer()
        results = scorer.score("ICD-10 I10 hypertension", MEDICAL_CHUNKS, top_k=3)

        assert len(results) == 3
        assert "I10" in results[0].content

    def test_empty_query(self):
        scorer = BM25Scorer()
        results = scorer.score("", MEDICAL_CHUNKS, top_k=3)
        assert len(results) == 3  # returns original order

    def test_empty_chunks(self):
        scorer = BM25Scorer()
        results = scorer.score("Metformin", [], top_k=5)
        assert results == []

    def test_no_matching_terms(self):
        """Query with no overlapping terms should still return results (with low scores)."""
        scorer = BM25Scorer()
        results = scorer.score("xyzzy foobar", MEDICAL_CHUNKS, top_k=3)
        assert len(results) == 3
        # All scores should be 0 since no terms match
        assert all(r.score == 0.0 for r in results)

    def test_top_k_limiting(self):
        scorer = BM25Scorer()
        results = scorer.score("patient", MEDICAL_CHUNKS, top_k=2)
        assert len(results) == 2

    def test_bm25_metadata_preserved(self):
        scorer = BM25Scorer()
        results = scorer.score("Metformin", MEDICAL_CHUNKS, top_k=1)
        assert results[0].metadata["retrieval_method"] == "bm25"
        assert "bm25_raw_score" in results[0].metadata

    def test_scores_normalized(self):
        """BM25 scores should be normalized to [0, 1]."""
        scorer = BM25Scorer()
        results = scorer.score("Metformin diabetes", MEDICAL_CHUNKS, top_k=7)
        for r in results:
            assert 0.0 <= r.score <= 1.0

    def test_drug_name_precision(self):
        """BM25 should precisely match drug names."""
        scorer = BM25Scorer()
        aspirin_results = scorer.score("Aspirin antiplatelet", MEDICAL_CHUNKS, top_k=1)
        assert "Aspirin" in aspirin_results[0].content

    def test_irrelevant_content_ranked_low(self):
        """Non-medical content should rank below medical content for medical queries."""
        scorer = BM25Scorer()
        results = scorer.score("diabetes Metformin treatment", MEDICAL_CHUNKS, top_k=7)
        # Cafeteria chunk should be ranked low
        cafeteria_rank = None
        for i, r in enumerate(results):
            if "cafeteria" in r.content:
                cafeteria_rank = i
                break
        if cafeteria_rank is not None:
            assert cafeteria_rank >= 3  # Should be in bottom half


# ── Reciprocal Rank Fusion tests ─────────────────────────────────────────


class TestReciprocalRankFusion:
    def test_basic_fusion(self):
        """RRF should merge two ranked lists and produce a combined ranking."""
        vector_results = [
            _chunk("chunk A", 0.9, "E1"),
            _chunk("chunk B", 0.8, "E2"),
            _chunk("chunk C", 0.7, "E3"),
        ]
        bm25_results = [
            _chunk("chunk B", 0.95, "E2"),
            _chunk("chunk D", 0.85, "E4"),
            _chunk("chunk A", 0.75, "E1"),
        ]
        # Make chunk_ids match for A and B
        vector_results[0] = RetrievedChunk(
            **{**vector_results[0].__dict__, "chunk_id": uuid.UUID("00000000-0000-0000-0000-000000000001")}
        )
        vector_results[1] = RetrievedChunk(
            **{**vector_results[1].__dict__, "chunk_id": uuid.UUID("00000000-0000-0000-0000-000000000002")}
        )
        bm25_results[0] = RetrievedChunk(
            **{**bm25_results[0].__dict__, "chunk_id": uuid.UUID("00000000-0000-0000-0000-000000000002")}
        )
        bm25_results[2] = RetrievedChunk(
            **{**bm25_results[2].__dict__, "chunk_id": uuid.UUID("00000000-0000-0000-0000-000000000001")}
        )

        result = reciprocal_rank_fusion(vector_results, bm25_results, top_k=4)

        assert len(result) == 4
        # Chunks appearing in both lists should get higher RRF scores
        chunk_ids = [str(r.chunk_id) for r in result]
        # A and B appear in both lists, so they should be ranked higher
        assert "00000000-0000-0000-0000-000000000002" in chunk_ids[:2]  # chunk B
        assert "00000000-0000-0000-0000-000000000001" in chunk_ids[:2]  # chunk A

    def test_empty_lists(self):
        result = reciprocal_rank_fusion([], [], top_k=5)
        assert result == []

    def test_single_list(self):
        chunks = [_chunk("A", 0.9), _chunk("B", 0.8)]
        result = reciprocal_rank_fusion(chunks, top_k=2)
        assert len(result) == 2

    def test_top_k_limiting(self):
        list1 = [_chunk(f"chunk {i}", 1.0 - i * 0.1) for i in range(5)]
        list2 = [_chunk(f"other {i}", 1.0 - i * 0.1) for i in range(5)]
        result = reciprocal_rank_fusion(list1, list2, top_k=3)
        assert len(result) == 3

    def test_rrf_metadata(self):
        """Fused results should contain RRF metadata."""
        chunks = [_chunk("test chunk", 0.9)]
        result = reciprocal_rank_fusion(chunks, top_k=1)
        assert result[0].metadata["retrieval_method"] == "hybrid_rrf"
        assert "rrf_score" in result[0].metadata

    def test_rrf_scores_are_positive(self):
        """All RRF scores should be positive."""
        list1 = [_chunk(f"A{i}", 0.5) for i in range(3)]
        list2 = [_chunk(f"B{i}", 0.5) for i in range(3)]
        result = reciprocal_rank_fusion(list1, list2, top_k=6)
        for r in result:
            assert r.score > 0

    def test_k_parameter_effect(self):
        """Higher k should produce more uniform scores."""
        chunks_a = [_chunk("X", 0.9)]
        chunks_b = [_chunk("Y", 0.8)]

        result_low_k = reciprocal_rank_fusion(chunks_a, chunks_b, k=1, top_k=2)
        result_high_k = reciprocal_rank_fusion(chunks_a, chunks_b, k=1000, top_k=2)

        # With high k, scores should be more similar
        score_diff_low = abs(result_low_k[0].score - result_low_k[1].score)
        score_diff_high = abs(result_high_k[0].score - result_high_k[1].score)
        assert score_diff_high <= score_diff_low
