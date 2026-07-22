from uuid import uuid4

from hospital_ai.evaluation.claims import (
    AtomicClaim,
    CitedChunk,
    evaluate_claim_support,
    extract_atomic_claims,
)


def test_claim_requires_textual_support_not_only_valid_evidence_id() -> None:
    evidence_id = uuid4()
    claim = AtomicClaim(field="HbA1c", value="4.2", unit="%")
    chunk = CitedChunk(
        evidence_id=evidence_id,
        text="HbA1c: 7.2 %",
        citation_label="E1",
    )

    verdict = evaluate_claim_support(claim, (chunk,))

    assert verdict.supported is False
    assert verdict.supporting_evidence_ids == ()


def test_claim_support_is_exact_for_value_unit_and_date() -> None:
    evidence_id = uuid4()
    claim = AtomicClaim(field="HbA1c", value="7.2", unit="%", observed_at="2026-01-02")
    chunk = CitedChunk(
        evidence_id=evidence_id,
        text="On 2026-01-02, HbA1c was 7.2 %.",
        citation_label="E1",
    )

    verdict = evaluate_claim_support(claim, (chunk,))

    assert verdict.supported is True
    assert verdict.supporting_evidence_ids == (evidence_id,)


def test_claim_does_not_accept_substring_numeric_match() -> None:
    claim = AtomicClaim(field="Glucose", value="10", unit="mg/dL")
    chunk = CitedChunk(evidence_id=uuid4(), text="Glucose: 110 mg/dL", citation_label="E1")

    assert evaluate_claim_support(claim, (chunk,)).supported is False


def test_claim_support_cannot_combine_unrelated_records() -> None:
    claim = AtomicClaim(field="Glucose", value="10", unit="mg/dL")
    chunk = CitedChunk(
        evidence_id=uuid4(),
        text="Glucose: 110 mg/dL. Sodium: 10 mg/dL.",
        citation_label="E1",
    )

    assert evaluate_claim_support(claim, (chunk,)).supported is False


def test_claim_support_cannot_combine_conjoined_records() -> None:
    claim = AtomicClaim(field="Glucose", value="10", unit="mg/dL")
    chunk = CitedChunk(
        evidence_id=uuid4(),
        text="Glucose: 110 mg/dL and Sodium: 10 mg/dL.",
        citation_label="E1",
    )

    assert evaluate_claim_support(claim, (chunk,)).supported is False


def test_extracts_unexpected_textual_claim_fail_closed() -> None:
    claims = extract_atomic_claims("Sodium is critically low [E9].")

    assert claims == (AtomicClaim(field="Sodium", value="critically low", citation_labels=("E9",)),)


def test_extracts_uncited_and_colon_claims() -> None:
    assert extract_atomic_claims("Sodium is critically low.") == (AtomicClaim(field="Sodium", value="critically low"),)
    assert extract_atomic_claims("HbA1c: 7.2 % [E1].") == (
        AtomicClaim(field="HbA1c", value="7.2", unit="%", citation_labels=("E1",)),
    )


def test_factual_looking_unparsed_segment_fails_closed() -> None:
    claims = extract_atomic_claims("Patient stable and sodium: critically low.")

    assert len(claims) == 1
    assert claims[0].field.casefold() == "sodium"
