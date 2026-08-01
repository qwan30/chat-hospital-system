import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user
from hospital_ai.core.security import PATIENT_READ_SCOPES
from hospital_ai.db.models import AuditLog, ChatThread, Document, PatientPermission, User
from hospital_ai.db.session import get_session as get_db
from hospital_ai.schemas.timeline import GlobalTimelineResponse, TimelineEventBase

router = APIRouter(prefix="/timeline", tags=["Timeline"])


@router.get("", response_model=GlobalTimelineResponse)
async def get_global_timeline(
    limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    now = datetime.now(UTC)
    # 1. Get permitted patient IDs with proper scope and expiration checks
    perm_stmt = select(PatientPermission.patient_id).where(
        PatientPermission.user_id == current_user.id,
        PatientPermission.scope.in_(PATIENT_READ_SCOPES),
        PatientPermission.deleted_at.is_(None),
        or_(PatientPermission.expires_at.is_(None), PatientPermission.expires_at > now),
    )
    perm_result = await db.execute(perm_stmt)
    allowed_patients = [row[0] for row in perm_result.all()]

    if not allowed_patients:
        # User has no assigned patients, return personal audit logs not linked to patients
        audit_stmt = (
            select(AuditLog)
            .where(
                AuditLog.actor_user_id == current_user.id,
                AuditLog.patient_id.is_(None),
                ~AuditLog.action.like("%.read%"),
            )
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )

        audit_res = await db.execute(audit_stmt)
        events = []
        for audit in audit_res.scalars().all():
            events.append(
                TimelineEventBase(
                    event_id=f"audit-{audit.id}",
                    timestamp=audit.created_at,
                    type="audit",
                    title=audit.action,
                    body=audit.meta.get("reason", "Action logged") if audit.meta else "Action logged",
                    patient_id=audit.patient_id,
                    metadata={},
                )
            )
        events.sort(key=lambda x: x.timestamp, reverse=True)
        paginated_events = events[offset : offset + limit]
        return GlobalTimelineResponse(events=paginated_events, total_count=len(events))

    # 2. Scatter gather with proper soft-delete and RBAC filters
    chat_stmt = (
        select(ChatThread)
        .where(ChatThread.patient_id.in_(allowed_patients), ChatThread.deleted_at.is_(None))
        .order_by(desc(ChatThread.created_at))
        .limit(limit)
    )

    doc_stmt = (
        select(Document)
        .where(Document.patient_id.in_(allowed_patients), Document.deleted_at.is_(None))
        .order_by(desc(Document.created_at))
        .limit(limit)
    )

    audit_stmt = (
        select(AuditLog)
        .where(
            or_(
                AuditLog.patient_id.in_(allowed_patients),
                and_(AuditLog.patient_id.is_(None), AuditLog.actor_user_id == current_user.id),
            ),
            ~AuditLog.action.like("%.read%"),
        )
        .order_by(desc(AuditLog.created_at))
        .limit(limit)
    )

    chat_res, doc_res, audit_res = await asyncio.gather(
        db.execute(chat_stmt), db.execute(doc_stmt), db.execute(audit_stmt)
    )

    events = []
    for chat in chat_res.scalars().all():
        events.append(
            TimelineEventBase(
                event_id=f"chat-{chat.id}",
                timestamp=chat.created_at,
                type="chat",
                title="AI consult started",
                body=chat.title or "New consultation",
                patient_id=chat.patient_id,
                metadata={},
            )
        )

    for doc in doc_res.scalars().all():
        events.append(
            TimelineEventBase(
                event_id=f"doc-{doc.id}",
                timestamp=doc.created_at,
                type="document",
                title="Document uploaded",
                body=f"{doc.filename} added to patient record",
                patient_id=doc.patient_id,
                metadata={},
            )
        )

    for audit in audit_res.scalars().all():
        events.append(
            TimelineEventBase(
                event_id=f"audit-{audit.id}",
                timestamp=audit.created_at,
                type="audit",
                title=audit.action,
                body=audit.meta.get("reason", "Action logged") if audit.meta else "Action logged",
                patient_id=audit.patient_id,
                metadata={},
            )
        )

    # 3. Sort and paginate
    events.sort(key=lambda x: x.timestamp, reverse=True)
    paginated_events = events[offset : offset + limit]

    return GlobalTimelineResponse(events=paginated_events, total_count=len(events))
