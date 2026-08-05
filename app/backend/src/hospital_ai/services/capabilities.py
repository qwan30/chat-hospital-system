from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Final, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.errors import NotFoundError, PermissionDeniedError
from hospital_ai.db.clinical_documents import (
    DocumentIndexGeneration,
    DocumentPageRevision,
    DocumentRevisionPage,
    DocumentRevisionSet,
)
from hospital_ai.db.models import Document, User
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


@dataclass(frozen=True)
class DocumentRevisionAggregate:
    document: Document
    revision_set: Optional[DocumentRevisionSet] = None
    page_revision: Optional[DocumentPageRevision] = None
    revision_page: Optional[DocumentRevisionPage] = None


@dataclass(frozen=True)
class DocumentGenerationAggregate:
    document: Document
    generation: DocumentIndexGeneration
    revision_set: DocumentRevisionSet


async def _raise_aggregate_not_found(
    session: AsyncSession,
    *,
    document: Optional[Document],
    actor: Optional[User],
    action: str,
    object_id: Optional[uuid.UUID],
    trace_id: str,
    reason: str,
) -> None:
    if actor is not None:
        await AuditService(session).record(
            actor_user_id=actor.id,
            action=action,
            object_type="document",
            object_id=object_id,
            patient_id=document.patient_id if document else None,
            outcome="denied",
            trace_id=trace_id,
            metadata={"reason": reason},
        )
        await session.commit()
    raise NotFoundError("Requested document resource was not found.")


async def load_document_revision_aggregate(
    session: AsyncSession,
    *,
    document_id: uuid.UUID,
    revision_set_id: Optional[uuid.UUID] = None,
    page_number: Optional[int] = None,
    page_revision_id: Optional[uuid.UUID] = None,
    actor: Optional[User] = None,
    action: str = "document_revision.resource.read",
    trace_id: str = "0",
) -> DocumentRevisionAggregate:
    document = await session.get(Document, document_id)
    if document is None:
        await _raise_aggregate_not_found(
            session,
            document=None,
            actor=actor,
            action=action,
            object_id=document_id,
            trace_id=trace_id,
            reason="document_not_found",
        )

    revision_set = None
    if revision_set_id is not None:
        revision_set = await session.get(DocumentRevisionSet, revision_set_id)
        if revision_set is None or revision_set.document_id != document.id:
            await _raise_aggregate_not_found(
                session,
                document=document,
                actor=actor,
                action=action,
                object_id=revision_set_id,
                trace_id=trace_id,
                reason="revision_set_document_mismatch",
            )

    revision_page = None
    if page_number is not None:
        if revision_set is None:
            await _raise_aggregate_not_found(
                session,
                document=document,
                actor=actor,
                action=action,
                object_id=document.id,
                trace_id=trace_id,
                reason="revision_set_required_for_page",
            )
        revision_page = await session.scalar(
            select(DocumentRevisionPage).where(
                DocumentRevisionPage.revision_set_id == revision_set.id,
                DocumentRevisionPage.page_number == page_number,
            )
        )
        if revision_page is None:
            await _raise_aggregate_not_found(
                session,
                document=document,
                actor=actor,
                action=action,
                object_id=revision_set.id,
                trace_id=trace_id,
                reason="revision_page_not_found",
            )
        page_revision_id = revision_page.page_revision_id

    page_revision = None
    if page_revision_id is not None:
        page_revision = await session.get(DocumentPageRevision, page_revision_id)
        if page_revision is None or page_revision.document_id != document.id:
            await _raise_aggregate_not_found(
                session,
                document=document,
                actor=actor,
                action=action,
                object_id=page_revision_id,
                trace_id=trace_id,
                reason="page_revision_document_mismatch",
            )

    return DocumentRevisionAggregate(
        document=document,
        revision_set=revision_set,
        page_revision=page_revision,
        revision_page=revision_page,
    )


async def load_document_generation_aggregate(
    session: AsyncSession,
    *,
    document_id: uuid.UUID,
    generation_id: uuid.UUID,
    actor: Optional[User] = None,
    action: str = "document_generation.resource.read",
    trace_id: str = "0",
) -> DocumentGenerationAggregate:
    document = await session.get(Document, document_id)
    if document is None:
        await _raise_aggregate_not_found(
            session,
            document=None,
            actor=actor,
            action=action,
            object_id=document_id,
            trace_id=trace_id,
            reason="document_not_found",
        )

    generation = await session.get(DocumentIndexGeneration, generation_id)
    if generation is None or generation.document_id != document.id:
        await _raise_aggregate_not_found(
            session,
            document=document,
            actor=actor,
            action=action,
            object_id=generation_id,
            trace_id=trace_id,
            reason="generation_document_mismatch",
        )

    revision_set = await session.get(DocumentRevisionSet, generation.revision_set_id)
    if revision_set is None or revision_set.document_id != document.id:
        await _raise_aggregate_not_found(
            session,
            document=document,
            actor=actor,
            action=action,
            object_id=generation_id,
            trace_id=trace_id,
            reason="generation_revision_set_mismatch",
        )

    return DocumentGenerationAggregate(document=document, generation=generation, revision_set=revision_set)


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
        object_id: Optional[uuid.UUID],
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
        object_id: Optional[uuid.UUID] = None,
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
