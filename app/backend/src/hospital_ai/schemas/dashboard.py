from datetime import datetime
from uuid import UUID

from hospital_ai.schemas.common import ApiSchema


class RecentPatient(ApiSchema):
    id: UUID
    full_name: str
    mrn: str
    last_accessed: datetime | None = None


class DocumentStats(ApiSchema):
    indexed: int
    processing: int
    failed: int


class DashboardMetrics(ApiSchema):
    hours_saved: float
    cost_saved_usd: float


class SystemsHealth(ApiSchema):
    hms_api: str
    ollama_inference: str


class DashboardSummaryResponse(ApiSchema):
    recent_patients: list[RecentPatient]
    document_stats: DocumentStats
    metrics: DashboardMetrics
    systems_health: SystemsHealth
