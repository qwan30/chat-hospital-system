"""Re-ranking service for improving retrieval quality.

Inspired by kotaemon's rerankings module — applies a second-pass scoring
to the candidate chunks returned by the initial vector/full-text retrieval.

Supports multiple backends via a strategy pattern:
- keyword:       Lightweight token-overlap reranker (zero dependencies, MVP default)
- cross_encoder: Local sentence-transformers cross-encoder model
- tei:           HuggingFace Text Embeddings Inference API
- cohere:        Cohere Rerank API
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from typing import Optional

from hospital_ai.core.config import Settings
from hospital_ai.services.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


# ── Abstract base ────────────────────────────────────────────────────────


class BaseReranker(ABC):
    """Base class for all reranker backends."""

    @abstractmethod
    def rerank(self, query: str, chunks: list[RetrievedChunk], *, top_k: int = 5) -> list[RetrievedChunk]:
        """Re-score and re-order chunks by relevance to the query.

        Args:
            query: The user question.
            chunks: Candidate chunks from initial retrieval.
            top_k: Maximum number of chunks to return.

        Returns:
            Re-ordered list of chunks with updated scores.
        """


# ── Keyword reranker (MVP default) ───────────────────────────────────────


class KeywordReranker(BaseReranker):
    """Lightweight keyword-overlap re-ranker.

    Blends the original vector score with a keyword overlap score.
    Zero external dependencies — suitable as a fallback.
    """

    def rerank(self, query: str, chunks: list[RetrievedChunk], *, top_k: int = 5) -> list[RetrievedChunk]:
        if not chunks:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return chunks[:top_k]

        scored: list[tuple[float, RetrievedChunk]] = []
        for chunk in chunks:
            chunk_tokens = _tokenize(chunk.content)
            if not chunk_tokens:
                scored.append((chunk.score, chunk))
                continue

            overlap = query_tokens & chunk_tokens
            keyword_boost = len(overlap) / max(len(query_tokens), 1)

            # Blend the original vector score with the keyword overlap score.
            # Weights: 60% original vector score, 40% keyword relevance.
            blended = 0.6 * chunk.score + 0.4 * keyword_boost
            scored.append((blended, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)

        return [
            RetrievedChunk(
                evidence_id=chunk.evidence_id,
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                page=chunk.page,
                chunk_id=chunk.chunk_id,
                score=round(rerank_score, 4),
                content=chunk.content,
                metadata={**chunk.metadata, "rerank_original_score": chunk.score},
            )
            for rerank_score, chunk in scored[:top_k]
        ]


# ── Cross-encoder reranker (local model) ─────────────────────────────────


class CrossEncoderReranker(BaseReranker):
    """Neural cross-encoder reranker using sentence-transformers.

    Uses models like BAAI/bge-reranker-v2-m3 or cross-encoder/ms-marco-MiniLM-L-6-v2
    to produce a relevance score for each (query, chunk) pair.

    Falls back to KeywordReranker if sentence-transformers is not installed.
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3") -> None:
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        """Lazy-load the cross-encoder model."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder

                self._model = CrossEncoder(self.model_name)
                logger.info("Loaded cross-encoder model: %s", self.model_name)
            except ImportError:
                logger.warning("sentence-transformers not installed. Install with: pip install sentence-transformers")
                return None
            except Exception as exc:
                logger.error("Failed to load cross-encoder model %s: %s", self.model_name, exc)
                return None
        return self._model

    def rerank(self, query: str, chunks: list[RetrievedChunk], *, top_k: int = 5) -> list[RetrievedChunk]:
        if not chunks:
            return []

        model = self._get_model()
        if model is None:
            logger.warning("Cross-encoder unavailable, falling back to keyword reranker")
            return KeywordReranker().rerank(query, chunks, top_k=top_k)

        # Prepare (query, passage) pairs for the cross-encoder
        pairs = [(query, chunk.content) for chunk in chunks]

        try:
            scores = model.predict(pairs)
        except Exception as exc:
            logger.error("Cross-encoder prediction failed: %s", exc)
            return KeywordReranker().rerank(query, chunks, top_k=top_k)

        # Normalize scores to [0, 1] range using sigmoid if needed
        normalized = _normalize_scores([float(s) for s in scores])

        scored = list(zip(normalized, chunks, strict=False))
        scored.sort(key=lambda item: item[0], reverse=True)

        return [
            RetrievedChunk(
                evidence_id=chunk.evidence_id,
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                page=chunk.page,
                chunk_id=chunk.chunk_id,
                score=round(rerank_score, 4),
                content=chunk.content,
                metadata={
                    **chunk.metadata,
                    "rerank_original_score": chunk.score,
                    "rerank_method": "cross_encoder",
                    "rerank_model": self.model_name,
                },
            )
            for rerank_score, chunk in scored[:top_k]
        ]


# ── TEI reranker (HuggingFace Text Embeddings Inference) ─────────────────


class TeiReranker(BaseReranker):
    """Reranker using HuggingFace Text Embeddings Inference (TEI) API.

    Requires a running TEI server with a reranking model.
    See: https://huggingface.co/docs/text-embeddings-inference
    """

    def __init__(self, endpoint_url: str, max_tokens: int = 512) -> None:
        self.endpoint_url = endpoint_url.rstrip("/")
        self.max_tokens = max_tokens

    def rerank(self, query: str, chunks: list[RetrievedChunk], *, top_k: int = 5) -> list[RetrievedChunk]:
        if not chunks or not self.endpoint_url:
            return chunks[:top_k] if chunks else []

        import httpx

        texts = [chunk.content[: self.max_tokens] for chunk in chunks]

        # Process in batches of 6 (TEI recommendation)
        batch_size = 6
        all_scores: list[tuple[int, float]] = []

        for batch_start in range(0, len(texts), batch_size):
            batch_texts = texts[batch_start : batch_start + batch_size]
            batch_indices = list(range(batch_start, batch_start + len(batch_texts)))

            try:
                response = httpx.post(
                    f"{self.endpoint_url}/rerank",
                    json={"query": query, "texts": batch_texts},
                    timeout=30.0,
                )
                response.raise_for_status()
                results = response.json()

                for item in results:
                    original_index = batch_indices[item["index"]]
                    all_scores.append((original_index, float(item["score"])))
            except Exception as exc:
                logger.error("TEI reranking request failed: %s", exc)
                # Fall back to original scores for this batch
                for idx in batch_indices:
                    all_scores.append((idx, chunks[idx].score))

        # Sort by score descending
        all_scores.sort(key=lambda item: item[1], reverse=True)

        return [
            RetrievedChunk(
                evidence_id=chunks[idx].evidence_id,
                document_id=chunks[idx].document_id,
                document_title=chunks[idx].document_title,
                page=chunks[idx].page,
                chunk_id=chunks[idx].chunk_id,
                score=round(score, 4),
                content=chunks[idx].content,
                metadata={
                    **chunks[idx].metadata,
                    "rerank_original_score": chunks[idx].score,
                    "rerank_method": "tei",
                },
            )
            for idx, score in all_scores[:top_k]
        ]


# ── Cohere reranker ──────────────────────────────────────────────────────


class CohereReranker(BaseReranker):
    """Reranker using the Cohere Rerank API.

    Requires a Cohere API key. Uses the rerank-v4.0-fast model by default.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "rerank-v4.0-fast",
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name

    def rerank(self, query: str, chunks: list[RetrievedChunk], *, top_k: int = 5) -> list[RetrievedChunk]:
        if not chunks:
            return []

        if not self.api_key:
            logger.warning("Cohere API key not set, falling back to keyword reranker")
            return KeywordReranker().rerank(query, chunks, top_k=top_k)

        try:
            import cohere
        except ImportError:
            logger.warning("cohere package not installed, falling back to keyword reranker")
            return KeywordReranker().rerank(query, chunks, top_k=top_k)

        try:
            client = cohere.Client(self.api_key)
            docs = [chunk.content for chunk in chunks]
            response = client.rerank(
                model=self.model_name,
                query=query,
                documents=docs,
                top_n=top_k,
            )

            result = []
            for item in response.results:
                chunk = chunks[item.index]
                result.append(
                    RetrievedChunk(
                        evidence_id=chunk.evidence_id,
                        document_id=chunk.document_id,
                        document_title=chunk.document_title,
                        page=chunk.page,
                        chunk_id=chunk.chunk_id,
                        score=round(float(item.relevance_score), 4),
                        content=chunk.content,
                        metadata={
                            **chunk.metadata,
                            "rerank_original_score": chunk.score,
                            "rerank_method": "cohere",
                            "rerank_model": self.model_name,
                        },
                    )
                )
            return result

        except Exception as exc:
            logger.error("Cohere reranking failed: %s", exc)
            return KeywordReranker().rerank(query, chunks, top_k=top_k)


# ── Factory ──────────────────────────────────────────────────────────────


_reranker_cache: dict[str, BaseReranker] = {}


class RerankerService:
    """Factory that selects and caches the appropriate reranker backend.

    Usage:
        service = RerankerService(settings)
        reranked = service.rerank(query, chunks, top_k=5)

    For backward compatibility, instantiating without settings uses
    the keyword reranker (MVP behavior).
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings
        self._backend: Optional[BaseReranker] = None

    def _get_backend(self) -> BaseReranker:
        if self._backend is not None:
            return self._backend

        if self.settings is None:
            self._backend = KeywordReranker()
            return self._backend

        provider = self.settings.reranker_provider

        # Check cache for expensive models
        if provider in _reranker_cache:
            self._backend = _reranker_cache[provider]
            return self._backend

        if provider == "cross_encoder":
            backend = CrossEncoderReranker(model_name=self.settings.reranker_model)
            _reranker_cache[provider] = backend
        elif provider == "tei":
            backend = TeiReranker(
                endpoint_url=self.settings.reranker_tei_url,
            )
        elif provider == "cohere":
            backend = CohereReranker(
                api_key=self.settings.cohere_api_key,
            )
        else:
            # Default to keyword reranker
            backend = KeywordReranker()

        self._backend = backend
        return self._backend

    def rerank(self, query: str, chunks: list[RetrievedChunk], *, top_k: int = 5) -> list[RetrievedChunk]:
        """Re-rank chunks using the configured backend."""
        backend = self._get_backend()
        effective_top_k = top_k
        if self.settings is not None and hasattr(self.settings, "reranker_top_k"):
            effective_top_k = self.settings.reranker_top_k
        return backend.rerank(query, chunks, top_k=effective_top_k)


# ── Utilities ────────────────────────────────────────────────────────────


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _normalize_scores(scores: list[float]) -> list[float]:
    """Normalize scores to [0, 1] using min-max normalization.

    If all scores are the same, returns 1.0 for all.
    """
    if not scores:
        return []
    min_score = min(scores)
    max_score = max(scores)
    if max_score == min_score:
        return [1.0] * len(scores)
    return [(s - min_score) / (max_score - min_score) for s in scores]
