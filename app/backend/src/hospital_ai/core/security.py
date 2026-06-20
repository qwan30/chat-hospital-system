from typing import Optional
from uuid import uuid4


def sanitize_audit_query(q: Optional[str]) -> dict:
    """Return non-PHI query metadata for audit logging.

    Stores only length and a short prefix so raw query text (which may
    contain patient identifiers) does not leak into the audit trail.
    """
    if q is None or not q.strip():
        return {"q_len": 0}
    return {"q_len": len(q), "q_prefix": q.strip()[:20]}


ALLOWED_ROLES = {
    "doctor",  # Specifically mapped below if needed, acts as base for cardiologist, etc.
    "cardiologist",
    "nurse",
    "pharmacist",
    "lab_staff",
    "records_staff",
    "security",
    "admin",
    "compliance",
    "hospitalist",
}

# Granular PHI and clinical access scopes
PATIENT_READ_SCOPES = {"read", "summary", "medication", "admin"}
PATIENT_UPLOAD_SCOPES = {"upload", "admin"}
PATIENT_SUMMARY_SCOPES = {"summary", "admin"}

# Defines the specific data scopes each role can access when they have permission for a patient
ROLE_PERMISSIONS = {
    "pharmacist": {
        "allowed_scopes": {"medication", "allergies", "renal_labs", "medication_safety", "medication_chunks"},
        "can_access_full_notes": False,
    },
    "cardiologist": {
        "allowed_scopes": {"cardiology_guidelines", "labs", "imaging_summaries", "medications", "diagnoses", "read"},
        "can_access_full_notes": True,
    },
    "nurse": {"allowed_scopes": {"hospital_guidelines", "care_plan", "read"}, "can_access_full_notes": False},
    "admin": {
        "allowed_scopes": {"audit", "system_config", "access_request_metadata"},
        "can_access_full_notes": False,  # Must not access PHI by default
    },
    "compliance": {
        "allowed_scopes": {"audit_logs", "access_policy", "access_requests", "phi_justified"},
        "can_access_full_notes": False,  # Requires justification
    },
    "doctor": {  # Generic fallback for hospitalist or other doctors
        "allowed_scopes": {"read", "summary", "medication", "labs", "imaging", "diagnoses", "care_plan"},
        "can_access_full_notes": True,
    },
    "hospitalist": {
        "allowed_scopes": {"read", "summary", "medication", "labs", "imaging", "diagnoses", "care_plan"},
        "can_access_full_notes": True,
    },
}


def new_trace_id() -> str:
    return str(uuid4())
