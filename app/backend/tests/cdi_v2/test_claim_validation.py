from __future__ import annotations

import pytest


# Mock classes for testing
class ValidationContext:
    pass


def validation_context():
    return ValidationContext()


@pytest.mark.parametrize(
    ("sentence", "evidence", "expected"),
    [
        ("Metformin dose is 500 mg [E1].", "Metformin 500 mg twice daily", True),
        ("Metformin dose is 5,000 mg [E1].", "Metformin 500 mg twice daily", False),
        ("Metformin dose is 1 g [E1].", "Metformin dose is 1000 mg", True),
        ("Metformin dose is 1 g [E1].", "Metformin dose is 500 mg", False),
        ("The patient has no allergy [E1].", "Allergy: penicillin", False),
        ("The patient has an allergy to penicillin [E1].", "No known allergies", False),
        ("HbA1c was 7.1% on 2026-08-01 [E1].", "HbA1c 7.1% collected 2026-08-01", True),
        (
            "HbA1c was 7.1% on 2026-08-01 [E1].",
            "HbA1c collected 2026-08-01 and repeated 2026-08-02",
            False,
        ),
        ("The patient has diabetes [E1].", "The patient has no diabetes", False),
        ("The patient is stable [E1].", "The medication dose is 500 mg", False),
    ],
)
def test_numeric_unit_date_and_negation_validation(sentence, evidence, expected) -> None:
    from hospital_ai.services.claim_validation import ClaimValidator

    result = ClaimValidator().validate_sentence(sentence, {"E1": evidence}, validation_context())
    assert result.passed is expected


@pytest.mark.parametrize("citation_id", ["E1", "E99"])
def test_only_authorized_evidence_ids_can_support_a_claim(citation_id: str) -> None:
    from hospital_ai.services.claim_validation import ClaimValidator

    result = ClaimValidator().validate_sentence(
        f"The patient is stable [{citation_id}].",
        {"E2": "The patient is stable"},
        validation_context(),
    )

    assert result.passed is False
    assert result.claims[0].reason == "AUTHORIZED_EVIDENCE_REQUIRED"


def test_auxiliary_judge_cannot_override_deterministic_failure() -> None:
    from hospital_ai.services.claim_validation import ClaimValidator

    validator = ClaimValidator(auxiliary_judge=lambda *_args: True)
    result = validator.validate_sentence(
        "Metformin dose is 5000 mg [E1].",
        {"E1": "Metformin dose is 500 mg"},
        validation_context(),
    )

    assert result.passed is False
    assert result.claims[0].reason == "NUMBER_MISMATCH"
