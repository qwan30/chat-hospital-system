"""Deterministic atomic-claim support checks for certification."""

from __future__ import annotations

import re
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class _FrozenModel(BaseModel):
    class Config:
        allow_mutation = False
        extra = "forbid"


class AtomicClaim(_FrozenModel):
    field: str
    value: str
    unit: Optional[str] = None
    observed_at: Optional[str] = None
    critical: bool = True


class CitedChunk(_FrozenModel):
    evidence_id: UUID
    text: str
    citation_label: str


class SupportVerdict(_FrozenModel):
    supported: bool
    supporting_evidence_ids: tuple[UUID, ...]
    reason: str


def normalize_text(value: str) -> str:
    """Normalize bounded formatting differences without fuzzy clinical matching."""
    return " ".join(value.casefold().replace("−", "-").split())


def evaluate_claim_support(claim: AtomicClaim, cited_chunks: tuple[CitedChunk, ...]) -> SupportVerdict:
    """Require one cited source to contain the complete typed atomic claim."""
    supporting = tuple(chunk.evidence_id for chunk in cited_chunks if _chunk_supports_claim(claim, chunk.text))
    return SupportVerdict(
        supported=bool(supporting),
        supporting_evidence_ids=supporting,
        reason="exact_atomic_support" if supporting else "no_cited_chunk_supports_atomic_claim",
    )


def _chunk_supports_claim(claim: AtomicClaim, text: str) -> bool:
    normalized = normalize_text(text)
    if normalize_text(claim.field) not in normalized:
        return False
    if not _bounded_token(claim.value, normalized):
        return False
    if claim.unit and normalize_text(claim.unit) not in normalized:
        return False
    return not claim.observed_at or normalize_text(claim.observed_at) in normalized


def _bounded_token(value: str, normalized_text: str) -> bool:
    escaped = re.escape(normalize_text(value))
    return re.search(rf"(?<![\w.]){escaped}(?![\w.])", normalized_text) is not None
