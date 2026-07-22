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
    citation_labels: tuple[str, ...] = ()


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
    eligible = tuple(
        chunk for chunk in cited_chunks if not claim.citation_labels or chunk.citation_label in claim.citation_labels
    )
    supporting = tuple(chunk.evidence_id for chunk in eligible if _chunk_supports_claim(claim, chunk.text))
    return SupportVerdict(
        supported=bool(supporting),
        supporting_evidence_ids=supporting,
        reason="exact_atomic_support" if supporting else "no_cited_chunk_supports_atomic_claim",
    )


def _chunk_supports_claim(claim: AtomicClaim, text: str) -> bool:
    return any(_segment_supports_claim(claim, segment) for segment in _segments(text))


def extract_atomic_claims(answer: str) -> tuple[AtomicClaim, ...]:
    """Extract explicit ``field is/was/: value [citation]`` claims."""
    claims: list[AtomicClaim] = []
    pattern = re.compile(
        r"(?P<field>[A-Za-z][A-Za-z0-9 _/-]{0,40}?)\s+(?:is|was|:)\s*"
        r"(?P<value>[^;\[]+?)\s*(?P<labels>(?:\[E[0-9]+\]\s*)+)(?:[.;]|$)",
        re.IGNORECASE,
    )
    for match in pattern.finditer(answer):
        value, unit, observed_at = _parse_value(match.group("value").strip())
        labels = tuple(re.findall(r"\[(E[0-9]+)\]", match.group("labels"), re.IGNORECASE))
        claims.append(
            AtomicClaim(
                field=match.group("field").strip(),
                value=value,
                unit=unit,
                observed_at=observed_at,
                citation_labels=labels,
            )
        )
    return tuple(claims)


def _segments(text: str) -> tuple[str, ...]:
    return tuple(normalize_text(item) for item in re.split(r"(?<!\d)\.(?!\d)|[;\r\n]+", text) if item.strip())


def _segment_supports_claim(claim: AtomicClaim, segment: str) -> bool:
    field = normalize_text(claim.field)
    field_at = segment.find(field)
    if field_at < 0:
        return False
    tail = segment[field_at + len(field) :]
    if not _bounded_token(claim.value, tail):
        return False
    if claim.unit and normalize_text(claim.unit) not in tail:
        return False
    return not claim.observed_at or normalize_text(claim.observed_at) in segment


def _parse_value(raw: str) -> tuple[str, Optional[str], Optional[str]]:
    date_match = re.search(r"\bon\s+(\d{4}-\d{2}-\d{2})\b", raw, re.IGNORECASE)
    observed_at = date_match.group(1) if date_match else None
    without_date = raw[: date_match.start()].strip() if date_match else raw.strip()
    numeric = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*(.*)", without_date)
    if not numeric:
        return without_date, None, observed_at
    return numeric.group(1), numeric.group(2) or None, observed_at


def _bounded_token(value: str, normalized_text: str) -> bool:
    escaped = re.escape(normalize_text(value))
    return re.search(rf"(?<![\w.]){escaped}(?![\w.])", normalized_text) is not None
