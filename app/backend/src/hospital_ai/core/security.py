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
    "doctor",
    "nurse",
    "pharmacist",
    "lab_staff",
    "records_staff",
    "security",
    "admin",
}

PATIENT_READ_SCOPES = {"read", "summary", "medication", "admin"}
PATIENT_UPLOAD_SCOPES = {"upload", "admin"}
PATIENT_SUMMARY_SCOPES = {"summary", "admin"}


def new_trace_id() -> str:
    return str(uuid4())
