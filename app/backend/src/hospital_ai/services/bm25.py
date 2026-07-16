from typing import Optional
"""BM25 / full-text search service for hybrid retrieval.

Provides keyword-based search using PostgreSQL tsvector/GIN indexes
or a portable Python-side BM25 scoring fallback for SQLite tests.
"""

from __future__ import annotations

import logging
import math
import re

from hospital_ai.services.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


# ── Portable BM25 scorer (for SQLite tests and fallback) ─────────────────


class BM25Scorer:
    """Okapi BM25 scorer that works purely in Python.

    Used when PostgreSQL tsvector is unavailable (e.g., SQLite test DBs).
    Not intended for production — prefer the SQL tsvector path.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b

    def score(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        *,
        top_k: int = 10,
    ) -> list[RetrievedChunk]:
        """Score chunks against a query using BM25.

        Returns chunks sorted by BM25 score (descending), limited to top_k.
        """
        if not chunks or not query.strip():
            return chunks[:top_k]

        query_terms = _tokenize(query)
        if not query_terms:
            return chunks[:top_k]

        # Build document frequency table
        doc_count = len(chunks)
        doc_freq: dict[str, int] = {}
        doc_lengths: list[int] = []
        doc_term_freqs: list[dict[str, int]] = []

        for chunk in chunks:
            terms = _tokenize(chunk.content)
            doc_lengths.append(len(terms))

            term_freq: dict[str, int] = {}
            for term in terms:
                term_freq[term] = term_freq.get(term, 0) + 1
            doc_term_freqs.append(term_freq)

            # Count unique terms per document for DF
            for unique_term in set(terms):
                doc_freq[unique_term] = doc_freq.get(unique_term, 0) + 1

        avg_dl = sum(doc_lengths) / max(doc_count, 1)

        scored: list[tuple[float, int]] = []
        for idx, _chunk in enumerate(chunks):
            bm25_score = 0.0
            dl = doc_lengths[idx]

            for term in query_terms:
                if term not in doc_freq:
                    continue

                df = doc_freq[term]
                tf = doc_term_freqs[idx].get(term, 0)

                # IDF component (with smoothing to avoid negative values)
                idf = math.log(1 + (doc_count - df + 0.5) / (df + 0.5))

                # TF component with length normalization
                tf_norm = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * dl / max(avg_dl, 1)))

                bm25_score += idf * tf_norm

            scored.append((bm25_score, idx))

        # Sort by BM25 score descending
        scored.sort(key=lambda item: item[0], reverse=True)

        # Normalize to [0, 1]
        max_score = scored[0][0] if scored else 1.0
        if max_score == 0:
            max_score = 1.0

        result: list[RetrievedChunk] = []
        for bm25_score, idx in scored[:top_k]:
            chunk = chunks[idx]
            normalized_score = bm25_score / max_score
            result.append(
                RetrievedChunk(
                    evidence_id=chunk.evidence_id,
                    document_id=chunk.document_id,
                    document_title=chunk.document_title,
                    page=chunk.page,
                    chunk_id=chunk.chunk_id,
                    score=round(normalized_score, 4),
                    content=chunk.content,
                    metadata={
                        **chunk.metadata,
                        "retrieval_method": "bm25",
                        "bm25_raw_score": round(bm25_score, 4),
                    },
                )
            )

        return result


# ── Reciprocal Rank Fusion (RRF) ─────────────────────────────────────────


def reciprocal_rank_fusion(
    *ranked_lists: list[RetrievedChunk],
    k: int = 60,
    top_k: int = 10,
) -> list[RetrievedChunk]:
    """Merge multiple ranked lists using Reciprocal Rank Fusion.

    RRF is a simple and effective method for combining results from
    multiple retrieval systems. For each document d:

        RRF_score(d) = Σ 1 / (k + rank_in_list_i)

    where k is a constant (default 60, per the original paper).

    Args:
        *ranked_lists: One or more ranked lists of chunks.
        k: RRF constant (higher = more weight to lower-ranked items).
        top_k: Maximum number of results to return.

    Returns:
        Merged and de-duplicated list of chunks sorted by RRF score.
    """
    # Track RRF scores by chunk_id
    rrf_scores: dict[str, float] = {}
    chunk_map: dict[str, RetrievedChunk] = {}
    original_scores: dict[str, dict[str, float]] = {}

    for list_idx, ranked_list in enumerate(ranked_lists):
        list_name = f"list_{list_idx}"
        for rank, chunk in enumerate(ranked_list):
            key = str(chunk.chunk_id)
            rrf_score = 1.0 / (k + rank + 1)  # rank is 0-indexed, formula uses 1-indexed
            rrf_scores[key] = rrf_scores.get(key, 0.0) + rrf_score

            # Keep the chunk with the highest original score
            if key not in chunk_map or chunk.score > chunk_map[key].score:
                chunk_map[key] = chunk

            if key not in original_scores:
                original_scores[key] = {}
            original_scores[key][list_name] = chunk.score

    # Sort by RRF score
    sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)

    result: list[RetrievedChunk] = []
    for key in sorted_keys[:top_k]:
        chunk = chunk_map[key]
        result.append(
            RetrievedChunk(
                evidence_id=chunk.evidence_id,
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                page=chunk.page,
                chunk_id=chunk.chunk_id,
                score=round(rrf_scores[key], 6),
                content=chunk.content,
                metadata={
                    **chunk.metadata,
                    "retrieval_method": "hybrid_rrf",
                    "rrf_score": round(rrf_scores[key], 6),
                    **{f"score_{k}": v for k, v in original_scores.get(key, {}).items()},
                },
            )
        )

    return result


# ── PostgreSQL tsvector helpers ──────────────────────────────────────────


def text_to_tsvector_sql(text: str) -> str:
    """Generate a tsvector string for PostgreSQL insertion.

    This returns raw text that PostgreSQL's to_tsvector() will process.
    The actual tsvector conversion happens in SQL.
    """
    # Clean text for tsvector — remove excessive whitespace
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned


async def bm25_search_postgres(
    session,
    query: str,
    *,
    top_k: int = 10,
    scope_filter: Optional[str] = None,
) -> list[RetrievedChunk]:
    """Execute a BM25 full-text search against PostgreSQL tsvector index.

    Uses ts_rank_cd() for relevance scoring with the GIN index.
    Falls back gracefully if the search_vector column doesn't exist.

    Args:
        session: AsyncSession from SQLAlchemy.
        query: The search query text.
        top_k: Number of results to return.
        scope_filter: Optional SQL filter for access control.

    Returns:
        List of RetrievedChunks sorted by BM25 relevance.
    """
    from sqlalchemy import text as sql_text

    # Build the plainto_tsquery from the user's query
    sql = sql_text("""
        SELECT
            dc.id AS chunk_id,
            dc.document_id,
            dc.content,
            dc.page_number,
            dc.metadata,
            d.title AS document_title,
            ts_rank_cd(dc.search_vector, plainto_tsquery('english', :query)) AS rank
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE dc.search_vector @@ plainto_tsquery('english', :query)
        ORDER BY rank DESC
        LIMIT :top_k
    """)

    try:
        result = await session.execute(sql, {"query": query, "top_k": top_k})
        rows = result.fetchall()
    except Exception as exc:
        logger.warning("BM25 PostgreSQL search failed (tsvector may not exist): %s", exc)
        return []

    chunks: list[RetrievedChunk] = []
    for row in rows:
        # Normalize rank to [0, 1]
        max_rank = rows[0].rank if rows else 1.0
        normalized = row.rank / max(max_rank, 0.001)

        chunks.append(
            RetrievedChunk(
                evidence_id=f"E{row.chunk_id.hex[:4]}",
                document_id=row.document_id,
                document_title=row.document_title or "Untitled",
                page=row.page_number or 1,
                chunk_id=row.chunk_id,
                score=round(float(normalized), 4),
                content=row.content,
                metadata={
                    "retrieval_method": "bm25",
                    "bm25_raw_rank": round(float(row.rank), 6),
                },
            )
        )

    return chunks


# ── Utilities ────────────────────────────────────────────────────────────


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    return re.findall(r"[a-z0-9]+", text.lower())
