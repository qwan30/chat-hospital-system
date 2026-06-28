import uuid
from typing import List, Optional, Sequence
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.security import PATIENT_READ_SCOPES
from hospital_ai.db.models import Patient
from hospital_ai.services.permissions import active_patient_permission_exists


class PatientRepository:
    """Repository layer encapsulating database access patterns for Patient entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search_accessible_patients(
        self, user_id: uuid.UUID, query: Optional[str] = None, limit: int = 20
    ) -> Sequence[Patient]:
        permission_exists = active_patient_permission_exists(
            user_id=user_id,
            patient_id=Patient.id,
            accepted_scopes=PATIENT_READ_SCOPES,
        )
        stmt = select(Patient).where(Patient.deleted_at.is_(None), permission_exists).order_by(Patient.full_name)
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(or_(Patient.full_name.ilike(pattern), Patient.mrn.ilike(pattern)))
        result = await self.session.execute(stmt.limit(limit))
        return result.scalars().all()

    async def get_by_id(self, patient_id: uuid.UUID) -> Optional[Patient]:
        stmt = select(Patient).where(Patient.id == patient_id, Patient.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
