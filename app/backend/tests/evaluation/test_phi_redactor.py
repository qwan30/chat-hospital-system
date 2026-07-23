from hospital_ai.evaluation.phi_redactor import redact_patient_phi


def test_redact_patient_phi_names_and_mrn():
    raw = "Patient John Doe (MRN: EVAL-998877) was admitted on 2026-01-15."
    redacted = redact_patient_phi(raw)
    assert "John Doe" not in redacted
    assert "EVAL-998877" not in redacted
    assert "Patient [PATIENT_NAME]" in redacted or "[PATIENT_NAME]" in redacted
    assert "[MRN_MASKED]" in redacted


def test_redact_patient_phi_mrn_formats():
    raw_1 = "MRN: 12345 is pending lab results."
    raw_2 = "Subject EVAL-998877 details attached."

    redacted_1 = redact_patient_phi(raw_1)
    redacted_2 = redact_patient_phi(raw_2)

    assert "12345" not in redacted_1
    assert "[MRN_MASKED]" in redacted_1
    assert "EVAL-998877" not in redacted_2
    assert "[MRN_MASKED]" in redacted_2


def test_redact_patient_phi_dob_and_ssn():
    raw = "Patient Jane Smith, DOB: 1990-04-12, SSN: 123-45-6789."
    redacted = redact_patient_phi(raw)

    assert "Jane Smith" not in redacted
    assert "1990-04-12" not in redacted
    assert "123-45-6789" not in redacted
    assert "[PATIENT_NAME]" in redacted
    assert "[DATE_MASKED]" in redacted or "[PHI_MASKED]" in redacted
    assert "[ID_MASKED]" in redacted or "[PHI_MASKED]" in redacted
