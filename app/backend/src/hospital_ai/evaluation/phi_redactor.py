from __future__ import annotations

import re

# Regular expressions for HIPAA PHI patterns
_MRN_REGEX = re.compile(
    r"\bEVAL-[0-9a-fA-F]{6,32}\b|\bMRN:\s*\w+|\bMRN\s*#?\s*\w+",
    re.IGNORECASE,
)
_PATIENT_NAME_REGEX = re.compile(
    r"\bPatient\s+([A-Z][a-z]+\s+[A-Z][a-z]+)",
)
_DOB_REGEX = re.compile(
    r"(?:DOB|Date of Birth):\s*(?:\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)
_SSN_REGEX = re.compile(
    r"(?:SSN:\s*)?\b\d{3}-\d{2}-\d{4}\b",
    re.IGNORECASE,
)


def redact_patient_phi(text: str) -> str:
    """Redact HIPAA Protected Health Information (PHI) from patient records/queries.

    Redacts:
    - MRN / Medical Record Numbers (e.g. EVAL-998877, MRN: 12345) -> [MRN_MASKED]
    - Patient Names (e.g. Patient John Doe) -> Patient [PATIENT_NAME]
    - Dates of Birth / Dates (e.g. DOB: 1990-04-12) -> DOB: [DATE_MASKED]
    - Social Security / Personal ID Numbers (e.g. SSN: 123-45-6789) -> [ID_MASKED]
    """
    if not text:
        return text

    redacted = _MRN_REGEX.sub("[MRN_MASKED]", text)
    redacted = _PATIENT_NAME_REGEX.sub("Patient [PATIENT_NAME]", redacted)
    redacted = _DOB_REGEX.sub("DOB: [DATE_MASKED]", redacted)
    redacted = _SSN_REGEX.sub("SSN: [ID_MASKED]", redacted)

    return redacted
