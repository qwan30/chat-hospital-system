from __future__ import annotations

import pytest


# Mock classes for testing
class ValidationContext:
    pass


def validation_context():
    return ValidationContext()


@pytest.mark.parametrize(
    ("sentence", "evidence_by_id", "expected_passed", "expected_reason"),
    [
        # Exact and conflicting numeric values
        ("Metformin dose is 500 mg [E1].", {"E1": "Metformin 500 mg twice daily"}, True, None),
        ("Metformin dose is 5,000 mg [E1].", {"E1": "Metformin 500 mg twice daily"}, False, "NUMBER_MISMATCH"),
        # Unit conversion policy
        ("Metformin dose is 1 g [E1].", {"E1": "Metformin dose is 1000 mg"}, True, None),
        ("Metformin dose is 1 g [E1].", {"E1": "Metformin dose is 500 mg"}, False, "NUMBER_MISMATCH"),
        # Date ambiguity
        ("HbA1c was 7.1% on 2026-08-01 [E1].", {"E1": "HbA1c 7.1% collected 2026-08-01"}, True, None),
        (
            "HbA1c was 7.1% on 2026-08-01 [E1].",
            {"E1": "HbA1c 7.1% collected 2026-08-01 and repeated 2026-08-02"},
            False,
            "DATE_AMBIGUOUS",
        ),
        # Negation/allergy contradiction
        ("The patient has no allergy [E1].", {"E1": "Allergy: penicillin"}, False, "NEGATION_CONFLICT"),
        ("The patient has an allergy to penicillin [E1].", {"E1": "No known allergies"}, False, "NEGATION_CONFLICT"),
        ("The patient has diabetes [E1].", {"E1": "The patient has no diabetes"}, False, "NEGATION_CONFLICT"),
        # Unknown evidence ID
        ("The patient is stable [E99].", {"E1": "The patient is stable"}, False, "AUTHORIZED_EVIDENCE_REQUIRED"),
        # Wrong-patient evidence ID
        (
            "The patient is stable [WRONG_PATIENT_1].",
            {"E1": "The patient is stable"},
            False,
            "AUTHORIZED_EVIDENCE_REQUIRED",
        ),
        # Superseded evidence ID
        (
            "The patient is stable [SUPERSEDED_E2].",
            {"E1": "The patient is stable"},
            False,
            "AUTHORIZED_EVIDENCE_REQUIRED",
        ),
        # Unsupported claim
        ("The patient is stable [E1].", {"E1": "The medication dose is 500 mg"}, False, "UNSUPPORTED_CLAIM"),
    ],
)
def test_claim_validation_scenarios(sentence, evidence_by_id, expected_passed, expected_reason) -> None:
    from hospital_ai.services.claim_validation import ClaimValidator

    result = ClaimValidator().validate_sentence(sentence, evidence_by_id, validation_context())
    assert result.passed is expected_passed
    if not expected_passed:
        assert result.claims[0].reason == expected_reason


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
