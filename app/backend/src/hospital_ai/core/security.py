"""Các định nghĩa bảo mật, phân quyền theo vai trò (RBAC), và tiện ích làm sạch dữ liệu kiểm toán.

Quản lý danh sách các vai trò hợp lệ (ALLOWED_ROLES) trong bệnh viện và cấu hình phạm vi truy cập
(ROLE_PERMISSIONS) bảo đảm tuân thủ HIPAA và an toàn dữ liệu lâm sàng (PHI).
"""

from uuid import uuid4


def sanitize_audit_query(q: str | None) -> dict:
    """Return non-PHI query metadata for audit logging.
    Làm sạch nội dung câu hỏi truy vấn trước khi ghi vào nhật ký kiểm toán (audit log).

    Stores only length and a short prefix so raw query text (which may
    contain patient identifiers) does not leak into the audit trail.
    Chỉ lưu độ dài câu hỏi và 20 ký tự đầu tiên để tránh để lộ thông tin định danh
    bệnh nhân (PHI) vào log kiểm toán.
    """
    if q is None or not q.strip():
        return {"q_len": 0}
    return {"q_len": len(q), "q_prefix": q.strip()[:20]}



# Danh sách các vai trò (roles) hợp lệ trong hệ thống bệnh viện
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
# Các phạm vi truy cập dữ liệu y tế (PHI) và lâm sàng chi tiết
PATIENT_READ_SCOPES = {"read", "summary", "medication", "admin"}
PATIENT_UPLOAD_SCOPES = {"upload", "admin"}
PATIENT_SUMMARY_SCOPES = {"summary", "admin"}

# Defines the specific data scopes each role can access when they have permission for a patient
# Định nghĩa cụ thể các phạm vi dữ liệu (scopes) mà mỗi vai trò được phép đọc khi đã có quyền truy cập bệnh nhân
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
    "lab_staff": {
        "allowed_scopes": {"labs", "read"},
        "can_access_full_notes": False,
    },
    "records_staff": {
        "allowed_scopes": {"read", "audit"},
        "can_access_full_notes": False,
    },
    "security": {
        "allowed_scopes": {"audit", "access_requests"},
        "can_access_full_notes": False,
    },
}


def new_trace_id() -> str:
    """Tạo mới một ID định danh dấu vết (trace ID) ngẫu nhiên dạng UUID cho request/telemetry."""
    return str(uuid4())
