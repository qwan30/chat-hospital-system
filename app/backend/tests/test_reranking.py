"""Tests for the reranking service — strategy pattern and all backends."""

from __future__ import annotations

import uuid
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from hospital_ai.core.config import Settings
from hospital_ai.services.reranking import (
    BaseReranker,
    CohereReranker,
    CrossEncoderReranker,
    KeywordReranker,
    RerankerService,
    TeiReranker,
    _normalize_scores,
    _tokenize,
)
from hospital_ai.services.retrieval import RetrievedChunk


# ── Fixtures ─────────────────────────────────────────────────────────────


def _make_chunk(content: str, score: float = 0.5, eid: str = "") -> RetrievedChunk:
    return RetrievedChunk(
        evidence_id=eid or f"E{uuid.uuid4().hex[:4]}",
        document_id=uuid.uuid4(),
        document_title="test_doc.pdf",
        page=1,
        chunk_id=uuid.uuid4(),
        score=score,
        content=content,
        metadata={},
    )


SAMPLE_CHUNKS = [
    _make_chunk("Metformin is a first-line treatment for type 2 diabetes", 0.8, "E1"),
    _make_chunk("Aspirin is commonly used as an antiplatelet agent", 0.6, "E2"),
    _make_chunk("Patient was diagnosed with hypertension ICD-10 I10", 0.7, "E3"),
    _make_chunk("Hospital visiting hours are from 9am to 5pm", 0.5, "E4"),
    _make_chunk("Metformin dosage should be titrated based on HbA1c levels", 0.65, "E5"),
]


# ── Utility tests ────────────────────────────────────────────────────────


class TestTokenize:
    def test_basic(self):
        tokens = _tokenize("Metformin 500mg daily")
        assert "metformin" in tokens
        assert "500mg" in tokens

    def test_empty(self):
        assert _tokenize("") == set()

    def test_special_chars(self):
        tokens = _tokenize("ICD-10: I10 (hypertension)")
        assert "icd" in tokens
        assert "10" in tokens
        assert "i10" in tokens


class TestNormalizeScores:
    def test_range(self):
        result = _normalize_scores([1.0, 2.0, 3.0])
        assert result == [0.0, 0.5, 1.0]

    def test_same_values(self):
        result = _normalize_scores([5.0, 5.0, 5.0])
        assert result == [1.0, 1.0, 1.0]

    def test_empty(self):
        assert _normalize_scores([]) == []


# ── KeywordReranker tests ────────────────────────────────────────────────


class TestKeywordReranker:
    def test_basic_reranking(self):
        reranker = KeywordReranker()
        result = reranker.rerank("Metformin diabetes treatment", SAMPLE_CHUNKS, top_k=3)
        assert len(result) == 3
        # The Metformin chunks should rank higher due to keyword overlap
        contents = [r.content for r in result]
        assert any("Metformin" in c for c in contents[:2])

    def test_preserves_metadata(self):
        reranker = KeywordReranker()
        result = reranker.rerank("Metformin", SAMPLE_CHUNKS, top_k=2)
        for chunk in result:
            assert "rerank_original_score" in chunk.metadata

    def test_empty_input(self):
        reranker = KeywordReranker()
        result = reranker.rerank("anything", [], top_k=5)
        assert result == []

    def test_empty_query(self):
        reranker = KeywordReranker()
        result = reranker.rerank("", SAMPLE_CHUNKS, top_k=3)
        assert len(result) == 3

    def test_top_k_limiting(self):
        reranker = KeywordReranker()
        result = reranker.rerank("test", SAMPLE_CHUNKS, top_k=2)
        assert len(result) == 2


# ── CrossEncoderReranker tests ───────────────────────────────────────────


class TestCrossEncoderReranker:
    def test_fallback_when_no_model(self):
        """When sentence-transformers isn't installed, falls back to keyword."""
        with patch(
            "hospital_ai.services.reranking.CrossEncoderReranker._get_model",
            return_value=None,
        ):
            reranker = CrossEncoderReranker(model_name="test-model")
            result = reranker.rerank("Metformin", SAMPLE_CHUNKS, top_k=3)
            # Should still return results via keyword fallback
            assert len(result) == 3

    def test_with_mock_model(self):
        """Simulate a working cross-encoder model."""
        mock_model = MagicMock()
        # Return descending scores — last chunk gets the highest
        mock_model.predict.return_value = [0.9, 0.1, 0.7, 0.05, 0.85]

        reranker = CrossEncoderReranker(model_name="test-model")
        reranker._model = mock_model

        result = reranker.rerank("Metformin diabetes", SAMPLE_CHUNKS, top_k=3)

        mock_model.predict.assert_called_once()
        assert len(result) == 3
        # Highest score chunk should be first
        assert result[0].content == SAMPLE_CHUNKS[0].content  # score 0.9
        assert "rerank_method" in result[0].metadata
        assert result[0].metadata["rerank_method"] == "cross_encoder"

    def test_model_error_fallback(self):
        """If model.predict() throws, should fall back to keyword."""
        mock_model = MagicMock()
        mock_model.predict.side_effect = RuntimeError("CUDA OOM")

        reranker = CrossEncoderReranker(model_name="test-model")
        reranker._model = mock_model

        result = reranker.rerank("test", SAMPLE_CHUNKS, top_k=3)
        assert len(result) == 3  # Should still work via fallback

    def test_empty_input(self):
        reranker = CrossEncoderReranker(model_name="test-model")
        result = reranker.rerank("test", [], top_k=5)
        assert result == []


# ── TeiReranker tests ────────────────────────────────────────────────────


class TestTeiReranker:
    def test_no_endpoint_returns_original(self):
        reranker = TeiReranker(endpoint_url="", max_tokens=512)
        result = reranker.rerank("test", SAMPLE_CHUNKS, top_k=3)
        assert len(result) == 3

    @patch("httpx.post")
    def test_successful_reranking(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"index": 0, "score": 0.95},
            {"index": 1, "score": 0.3},
            {"index": 2, "score": 0.8},
        ]
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        reranker = TeiReranker(
            endpoint_url="http://localhost:8080",
            max_tokens=512,
        )

        # Use just 3 chunks to fit in one batch
        chunks = SAMPLE_CHUNKS[:3]
        result = reranker.rerank("Metformin", chunks, top_k=2)

        assert len(result) == 2
        assert result[0].score == 0.95  # Highest scored chunk first
        assert "rerank_method" in result[0].metadata

    def test_empty_input(self):
        reranker = TeiReranker(endpoint_url="http://localhost:8080")
        result = reranker.rerank("test", [], top_k=5)
        assert result == []


# ── CohereReranker tests ────────────────────────────────────────────────


class TestCohereReranker:
    def test_no_api_key_fallback(self):
        reranker = CohereReranker(api_key="")
        result = reranker.rerank("Metformin", SAMPLE_CHUNKS, top_k=3)
        # Should fall back to keyword reranker
        assert len(result) == 3

    def test_no_cohere_package_fallback(self):
        reranker = CohereReranker(api_key="test-key")
        with patch.dict("sys.modules", {"cohere": None}):
            result = reranker.rerank("Metformin", SAMPLE_CHUNKS, top_k=3)
            assert len(result) == 3

    def test_empty_input(self):
        reranker = CohereReranker(api_key="test-key")
        result = reranker.rerank("test", [], top_k=5)
        assert result == []


# ── RerankerService factory tests ────────────────────────────────────────


class TestRerankerServiceFactory:
    def test_default_uses_keyword(self):
        service = RerankerService()
        backend = service._get_backend()
        assert isinstance(backend, KeywordReranker)

    def test_keyword_provider(self):
        settings = Settings(reranker_provider="keyword")
        service = RerankerService(settings)
        backend = service._get_backend()
        assert isinstance(backend, KeywordReranker)

    def test_cross_encoder_provider(self):
        settings = Settings(reranker_provider="cross_encoder")
        service = RerankerService(settings)
        backend = service._get_backend()
        assert isinstance(backend, CrossEncoderReranker)

    def test_tei_provider(self):
        settings = Settings(
            reranker_provider="tei",
            reranker_tei_url="http://localhost:8080",
        )
        service = RerankerService(settings)
        backend = service._get_backend()
        assert isinstance(backend, TeiReranker)

    def test_cohere_provider(self):
        settings = Settings(
            reranker_provider="cohere",
            cohere_api_key="test-key",
        )
        service = RerankerService(settings)
        backend = service._get_backend()
        assert isinstance(backend, CohereReranker)

    def test_unknown_provider_defaults_to_keyword(self):
        settings = Settings(reranker_provider="unknown_backend")
        service = RerankerService(settings)
        backend = service._get_backend()
        assert isinstance(backend, KeywordReranker)

    def test_uses_settings_top_k(self):
        """Factory should use reranker_top_k from settings."""
        settings = Settings(reranker_provider="keyword", reranker_top_k=2)
        service = RerankerService(settings)
        result = service.rerank("Metformin", SAMPLE_CHUNKS)
        assert len(result) == 2

    def test_backward_compatible_no_settings(self):
        """Instantiating without settings should work (MVP behavior)."""
        service = RerankerService()
        result = service.rerank("Metformin", SAMPLE_CHUNKS, top_k=3)
        assert len(result) == 3
