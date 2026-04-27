from uuid import uuid4


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
