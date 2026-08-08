import uuid
from typing import Final

from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.db.models import User
from hospital_ai.services.audit import AuditService
from hospital_ai.services.permissions import PATIENT_READ_SCOPES, PATIENT_UPLOAD_SCOPES, PermissionService

ROLE_CAPABILITIES: Final[dict[str, frozenset[str]]] = {
    "doctor": frozenset({"document_revision.view_raw", "document_revision.edit"}),
    "records_staff": frozenset(
        {
            "document_revision.view_raw",
            "document_revision.edit",
            "document_revision.reject",
            "document_revision.restore",
            "superseded_evidence.read",
        }
    ),
    "admin": frozenset(
        {
            "document_revision.reject",
            "document_revision.approve",
            "document_revision.restore",
            "ocr_engine.override",
            "superseded_evidence.read",
        }
    ),
    "nurse": frozenset({"document_revision.view_raw"}),
    "pharmacist": frozenset({"document_revision.view_raw"}),
    "lab_staff": frozenset({"document_revision.view_raw"}),
    "security": frozenset(),
}

AUTHORING_PATIENT_SCOPES = frozenset(set(PATIENT_READ_SCOPES) | set(PATIENT_UPLOAD_SCOPES))
CAPABILITY_PATIENT_SCOPES: Final[dict[str, frozenset[str]]] = {
    "document_revision.view_raw": AUTHORING_PATIENT_SCOPES,
    "document_revision.edit": AUTHORING_PATIENT_SCOPES,
    "document_revision.reject": AUTHORING_PATIENT_SCOPES,
    "document_revision.approve": AUTHORING_PATIENT_SCOPES,
    "document_revision.restore": AUTHORING_PATIENT_SCOPES,
    "ocr_engine.override": AUTHORING_PATIENT_SCOPES,
    "superseded_evidence.read": frozenset(PATIENT_READ_SCOPES),
}


def role_has_capability(role: str, capability: str) -> bool:
    return capability in ROLE_CAPABILITIES.get(role, frozenset())


class CapabilityService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _deny(
        self,
        user: User,
        patient_id: uuid.UUID,
        capability: str,
        action: str,
        trace_id: str,
        object_id: uuid.UUID | None,
    ) -> None:
        audit_service = AuditService(self.session)
        await audit_service.record(
            trace_id=trace_id,
            action=action,
            actor_user_id=user.id,
            patient_id=patient_id,
            object_id=object_id,
            object_type="document",
            outcome="denied",
            metadata={"capability": capability, "role": user.role},
        )
        raise PermissionDeniedError(f"User role {user.role} missing capability {capability}")

    async def require(
        self,
        *,
        user: User,
        patient_id: uuid.UUID,
        capability: str,
        action: str,
        trace_id: str,
        object_id: uuid.UUID | None = None,
    ) -> None:
        if not role_has_capability(user.role, capability):
            await self._deny(user, patient_id, capability, action, trace_id, object_id)
        accepted_scopes = CAPABILITY_PATIENT_SCOPES[capability]
        await PermissionService(self.session).require_patient_scope(
            user=user,
            patient_id=patient_id,
            accepted_scopes=accepted_scopes,
            action=action,
            trace_id=trace_id,
            object_type="document",
            object_id=object_id,
        )
