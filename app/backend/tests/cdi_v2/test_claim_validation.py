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
        ("The patient has no allergy [E1].", "Allergy: penicillin", False),
        ("HbA1c was 7.1% on 2026-08-01 [E1].", "HbA1c 7.1% collected 2026-08-01", True),
    ],
)
def test_numeric_unit_date_and_negation_validation(sentence, evidence, expected) -> None:
    from hospital_ai.services.claim_validation import ClaimValidator
    result = ClaimValidator().validate_sentence(sentence, {"E1": evidence}, validation_context())
    assert result.passed is expected
