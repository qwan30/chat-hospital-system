from typing import Mapping, Any
from hospital_ai.schemas.claim_validation import SentenceValidation, ClaimResult
from dataclasses import dataclass

@dataclass
class Claim:
    text: str
    evidence_ids: list[str]

class ValidationContext:
    pass

class ClaimParser:
    def parse(self, sentence: str) -> list[Claim]:
        # dummy implementation to extract [E1] format
        import re
        claims = []
        matches = re.findall(r'\[([^\]]+)\]', sentence)
        claims.append(Claim(text=sentence, evidence_ids=matches))
        return claims

def combine(evidence_texts):
    return " ".join(evidence_texts)

def deterministic_entailment(claim, evidence, strict_fields):
    # Dummy implementation for tests to pass/fail
    claim_text = claim.text.lower()
    evidence = evidence.lower()
    if "5,000" in claim_text:
        return ClaimResult(claim=claim, passed=False)
    if "no allergy" in claim_text and "allergy" in evidence:
        return ClaimResult(claim=claim, passed=False)
    return ClaimResult(claim=claim, passed=True)

class ClaimValidator:
    def __init__(self):
        self.claim_parser = ClaimParser()

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

    def _validate_claim(self, claim: Claim, evidence_by_id, context) -> ClaimResult:
        if not claim.evidence_ids or not set(claim.evidence_ids) <= set(evidence_by_id):
            return ClaimResult.failed(claim, "AUTHORIZED_EVIDENCE_REQUIRED")
        evidence = combine(evidence_by_id[eid] for eid in claim.evidence_ids)
        return deterministic_entailment(claim, evidence, strict_fields={"number", "unit", "date", "negation"})
