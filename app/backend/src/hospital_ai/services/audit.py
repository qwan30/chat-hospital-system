import uuid
from typing import Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.db.models import AuditLog


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        actor_user_id: uuid.Optional[UUID],
        action: str,
        object_type: str,
        outcome: str,
        trace_id: str,
        object_id: uuid.Optional[UUID] = None,
        patient_id: uuid.Optional[UUID] = None,
        ip_address: Optional[str] = None,
        metadata: dict[str, Optional[Any]] = None,
    ) -> AuditLog:
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
