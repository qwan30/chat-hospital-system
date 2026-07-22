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
    aliases: tuple[str, ...] = ()


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
    return any(_claims_match(claim, candidate) for candidate in _association_claims(text))


def extract_atomic_claims(answer: str) -> tuple[AtomicClaim, ...]:
    """Extract explicit ``field is/was/: value [citation]`` claims."""
    return _association_claims(answer)


def _segments(text: str) -> tuple[str, ...]:
    boundary = r"(?<!\d)\.(?!\d)|[;\r\n]+|\band\s+(?=[A-Z][A-Za-z0-9 _/-]{0,40}(?:\s+(?:is|was)|\s*:))"
    return tuple(item.strip() for item in re.split(boundary, text) if item.strip())


def _association_claims(text: str) -> tuple[AtomicClaim, ...]:
    claims: list[AtomicClaim] = []
    relation = re.compile(
        r"^(?:on\s+(?P<prefix_date>\d{4}-\d{2}-\d{2}),?\s*)?"
        r"(?P<field>[A-Za-z][A-Za-z0-9 _/-]{0,40}?)(?:\s+(?:is|was)|\s*:)\s*(?P<value>.+)$",
        re.IGNORECASE,
    )
    for segment in _segments(text):
        labels = tuple(re.findall(r"\[(E[0-9]+)\]", segment, re.IGNORECASE))
        without_labels = re.sub(r"\[E[0-9]+\]", "", segment, flags=re.IGNORECASE).strip()
        match = relation.fullmatch(without_labels)
        if not match:
            continue
        value, unit, suffix_date = _parse_value(match.group("value").strip())
        claims.append(
            AtomicClaim(
                field=match.group("field").strip(),
                value=value,
                unit=unit,
                observed_at=match.group("prefix_date") or suffix_date,
                citation_labels=labels,
            )
        )
    return tuple(claims)


def _claims_match(expected: AtomicClaim, actual: AtomicClaim) -> bool:
    allowed_values = (expected.value, *expected.aliases)
    value_matches = any(normalize_text(value) == normalize_text(actual.value) for value in allowed_values)
    return (
        normalize_text(expected.field) == normalize_text(actual.field)
        and value_matches
        and (not expected.unit or normalize_text(expected.unit) == normalize_text(actual.unit or ""))
        and (not expected.observed_at or expected.observed_at == actual.observed_at)
    )


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
