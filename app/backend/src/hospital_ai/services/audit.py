"""Security and access audit logging service.
Dịch vụ ghi nhật ký kiểm tra bảo mật và truy cập hệ thống (audit log) để tuân thủ quy định y tế (HIPAA/Bảo mật).
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.db.models import AuditLog


class AuditService:
    """Service to record security and access audit logs into the database.
    Dịch vụ ghi lại nhật ký kiểm kê bảo mật và truy cập vào cơ sở dữ liệu.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Khởi tạo AuditService kèm AsyncSession."""
        self.session = session

    async def record(
        self,
        *,
        actor_user_id: uuid.UUID | None,
        action: str,
        object_type: str,
        outcome: str,
        trace_id: str,
        object_id: uuid.UUID | None = None,
        patient_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Create and flush an audit log entry tracking user actions on patient data.
        Tạo và lưu tạm (flush) một bản ghi nhật ký kiểm kê theo dõi các hành động
        của người dùng đối với dữ liệu bệnh nhân.
        """
        log = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            patient_id=patient_id,
            outcome=outcome,
            trace_id=trace_id,
            ip_address=ip_address,
            meta=metadata or {},
        )
        self.session.add(log)
        await self.session.flush()
        return log
