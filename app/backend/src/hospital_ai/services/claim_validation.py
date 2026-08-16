"""Deterministic validation for evidence-cited clinical claims.

The validator is intentionally conservative.  An auxiliary judge may reject a
claim that passed deterministic checks, but it can never turn a deterministic
safety failure into a pass.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Optional

from hospital_ai.schemas.claim_validation import ClaimResult, SentenceValidation


@dataclass
class Claim:
    text: str
    evidence_ids: list[str]


class ValidationContext:
    """Request-scoped context reserved for future policy-specific checks."""


_CITATION_PATTERN = re.compile(r"\[([^\[\]]+)\]")
_DATE_PATTERN = re.compile(
    r"\b(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|"
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
    r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|"
    r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:,|\s)\s*\d{4})\b",
    re.IGNORECASE,
)
_NUMBER_PATTERN = re.compile(
    r"(?<![\w-])(?P<value>\d+(?:,\d{3})*(?:\.\d+)?)"
    r"\s*(?P<unit>mcg|mg|kg|ml|years?|g|l|%)?\b",
    re.IGNORECASE,
)
_TOKEN_PATTERN = re.compile(r"[a-z][a-z0-9'-]*", re.IGNORECASE)
_NEGATION_PATTERN = re.compile(
    r"\b(?:no|not|without|denies|denied|negative|none|never)\b|\bno\s+known\b",
    re.IGNORECASE,
)

_UNIT_FACTORS: dict[str, tuple[str, float]] = {
    "mcg": ("mass", 0.001),
    "mg": ("mass", 1.0),
    "g": ("mass", 1000.0),
    "kg": ("mass", 1_000_000.0),
    "ml": ("volume", 1.0),
    "l": ("volume", 1000.0),
    "%": ("percent", 1.0),
    "year": ("age", 1.0),
    "years": ("age", 1.0),
}
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "based",
    "by",
    "collected",
    "condition",
    "contains",
    "daily",
    "for",
    "has",
    "have",
    "is",
    "it",
    "of",
    "on",
    "patient",
    "record",
    "shows",
    "signs",
    "the",
    "to",
    "was",
    "with",
}


def _normalize_number(value: str) -> float:
    return float(value.replace(",", ""))


def _extract_numbers(text: str) -> list[tuple[float, Optional[str]]]:
    without_dates = _DATE_PATTERN.sub(" ", text)
    return [
        (_normalize_number(match.group("value")), (match.group("unit") or "").lower() or None)
        for match in _NUMBER_PATTERN.finditer(without_dates)
    ]


def _normalize_date_match(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.strip().lower().replace("/", "-"))
    try:
        year, month, day = (int(part) for part in normalized.split("-"))
        return date(year, month, day).isoformat()
    except (ValueError, TypeError):
        return normalized


def _extract_dates(text: str) -> set[str]:
    return {_normalize_date_match(match.group(0)) for match in _DATE_PATTERN.finditer(text)}


def _stem(token: str) -> str:
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("ing") and len(token) > 5:
        return token[:-3]
    if token.endswith("ed") and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and len(token) > 4:
        return token[:-1]
    if token == "recovery":
        return "recover"
    return token


def _meaningful_tokens(text: str) -> set[str]:
    without_citations = _CITATION_PATTERN.sub(" ", text.lower())
    return {
        _stem(token)
        for token in _TOKEN_PATTERN.findall(without_citations)
        if token not in _STOP_WORDS and not token.isdigit()
    }


def _has_negation(text: str) -> bool:
    return bool(_NEGATION_PATTERN.search(text))


def _numbers_match(
    claim_numbers: list[tuple[float, Optional[str]]],
    evidence_numbers: list[tuple[float, Optional[str]]],
) -> bool:
    if not claim_numbers:
        return True
    if not evidence_numbers:
        return False

    for claim_value, claim_unit in claim_numbers:
        for evidence_value, evidence_unit in evidence_numbers:
            if claim_unit is None:
                if abs(claim_value - evidence_value) < 1e-9:
                    break
                continue
            if evidence_unit is None:
                continue
            claim_dimension, claim_factor = _UNIT_FACTORS.get(claim_unit, (claim_unit, 1.0))
            evidence_dimension, evidence_factor = _UNIT_FACTORS.get(evidence_unit, (evidence_unit, 1.0))
            if (
                claim_dimension == evidence_dimension
                and abs(claim_value * claim_factor - evidence_value * evidence_factor) < 1e-9
            ):
                break
        else:
            return False
    return True


def _deterministic_failure(claim: Claim, reason: str) -> ClaimResult:
    return ClaimResult.failed(claim, reason)


class ClaimParser:
    def parse(self, sentence: str) -> list[Claim]:
        evidence_ids = list(dict.fromkeys(_CITATION_PATTERN.findall(sentence)))
        return [Claim(text=sentence, evidence_ids=evidence_ids)]


def combine(evidence_texts: Mapping[str, str] | list[str] | tuple[str, ...]) -> str:
    return " ".join(evidence_texts)


def deterministic_entailment(claim: Claim, evidence: str, strict_fields: set[str]) -> ClaimResult:
    """Run deterministic field checks and a conservative lexical support check."""
    claim_text = claim.text

    if "number" in strict_fields and not _numbers_match(_extract_numbers(claim_text), _extract_numbers(evidence)):
        return _deterministic_failure(claim, "NUMBER_MISMATCH")

    claim_dates = _extract_dates(claim_text)
    evidence_dates = _extract_dates(evidence)
    if "date" in strict_fields and claim_dates:
        if len(evidence_dates) != 1:
            return _deterministic_failure(claim, "DATE_AMBIGUOUS")
        if not claim_dates <= evidence_dates:
            return _deterministic_failure(claim, "DATE_MISMATCH")

    if "negation" in strict_fields:
        claim_is_negated = _has_negation(claim_text)
        evidence_is_negated = _has_negation(evidence)
        claim_mentions_allergy = "allerg" in claim_text.lower()
        evidence_mentions_allergy = "allerg" in evidence.lower()
        shared_topics = _meaningful_tokens(claim_text) & _meaningful_tokens(evidence)
        if (
            claim_mentions_allergy or evidence_mentions_allergy or shared_topics
        ) and claim_is_negated != evidence_is_negated:
            return _deterministic_failure(claim, "NEGATION_CONFLICT")

    claim_tokens = _meaningful_tokens(claim_text)
    evidence_tokens = _meaningful_tokens(evidence)
    supported_by_field = bool(claim_dates and claim_dates <= evidence_dates) or bool(
        _extract_numbers(claim_text) and _numbers_match(_extract_numbers(claim_text), _extract_numbers(evidence))
    )
    if not (claim_tokens & evidence_tokens) and not supported_by_field:
        return _deterministic_failure(claim, "UNSUPPORTED_CLAIM")

    return ClaimResult(claim=claim, passed=True)


class ClaimValidator:
    def __init__(self, auxiliary_judge: Optional[Callable[..., bool]] = None) -> None:
        self.claim_parser = ClaimParser()
        self.auxiliary_judge = auxiliary_judge

    def validate_sentence(
        self,
        sentence: str,
        evidence_by_id: Mapping[str, str],
        context: ValidationContext,
    ) -> SentenceValidation:
        claims = self.claim_parser.parse(sentence)
        results = tuple(self._validate_claim(claim, evidence_by_id, context) for claim in claims)
        passed = all(result.passed for result in results)
        return SentenceValidation(sentence=sentence, claims=list(results), passed=passed)

    def _validate_claim(
        self,
        claim: Claim,
        evidence_by_id: Mapping[str, str],
        context: ValidationContext,
    ) -> ClaimResult:
        del context
        if not claim.evidence_ids or not set(claim.evidence_ids) <= set(evidence_by_id):
            return _deterministic_failure(claim, "AUTHORIZED_EVIDENCE_REQUIRED")

        evidence = combine(evidence_by_id[evidence_id] for evidence_id in claim.evidence_ids)
        result = deterministic_entailment(claim, evidence, strict_fields={"number", "unit", "date", "negation"})
        if not result.passed:
            return result
        if self.auxiliary_judge is not None and not self.auxiliary_judge(claim, evidence):
            return _deterministic_failure(claim, "AUXILIARY_JUDGE_REJECTED")
        return result
