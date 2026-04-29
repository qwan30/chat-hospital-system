"""Re-ranking service for improving retrieval quality.

Inspired by kotaemon's rerankings module — applies a second-pass scoring
to the candidate chunks returned by the initial vector/full-text retrieval.
"""

from typing import List

from hospital_ai.services.retrieval import RetrievedChunk


class RerankerService:
    """Lightweight keyword-overlap re-ranker for MVP.

    Production upgrade: plug in a cross-encoder model (e.g. bge-reranker-v2,
    Cohere rerank, or a local ONNX model).
    """

    def rerank(self, query: str, chunks: List[RetrievedChunk], *, top_k: int = 5) -> List[RetrievedChunk]:
        if not chunks:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return chunks[:top_k]

        scored: List[tuple[float, RetrievedChunk]] = []
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


def _tokenize(text: str) -> set[str]:
    import re
    return set(re.findall(r"[a-z0-9]+", text.lower()))
