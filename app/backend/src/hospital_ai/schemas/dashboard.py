"""Schemas cho Bảng điều khiển tổng quan (Dashboard Summary API).

Định nghĩa cấu trúc dữ liệu tóm tắt cho trang chủ (bệnh nhân gần đây,
thống kê tài liệu, hiệu quả AI, sức khỏe hệ thống).
"""

from datetime import datetime
from uuid import UUID

from hospital_ai.schemas.common import ApiSchema


class RecentPatient(ApiSchema):
    """Schema thông tin bệnh nhân vừa được truy cập/thao tác gần đây."""
    id: UUID
    full_name: str
    mrn: str
    last_accessed: datetime | None = None


class DocumentStats(ApiSchema):
    """Schema thống kê trạng thái xử lý tài liệu (đã lập chỉ mục, đang xử lý, thất bại)."""
    indexed: int
    processing: int
    failed: int


class DashboardMetrics(ApiSchema):
    """Schema chỉ số hiệu quả do AI mang lại (số giờ tiết kiệm được và chi phí ước tính tiết kiệm bằng USD)."""
    hours_saved: float
    cost_saved_usd: float


class SystemsHealth(ApiSchema):
    """Schema trạng thái kết nối và sức khỏe các hệ thống thành phần (HMS API và Ollama Inference)."""
    hms_api: str
    ollama_inference: str


class DashboardSummaryResponse(ApiSchema):
    """Schema tổng hợp toàn bộ dữ liệu hiển thị trên Dashboard trang chủ."""
    recent_patients: list[RecentPatient]
    document_stats: DocumentStats
    metrics: DashboardMetrics
    systems_health: SystemsHealth

