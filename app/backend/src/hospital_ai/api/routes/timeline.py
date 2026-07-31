from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import asyncio

from hospital_ai.db.session import get_session as get_db
from hospital_ai.api.deps import get_current_user
from hospital_ai.db.models import User, PatientPermission, ChatThread, Document, AuditLog
from hospital_ai.schemas.timeline import GlobalTimelineResponse, TimelineEventBase

router = APIRouter(prefix="/timeline", tags=["Timeline"])

@router.get("", response_model=GlobalTimelineResponse)
async def get_global_timeline(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Get permitted patient IDs
    perm_stmt = select(PatientPermission.patient_id).where(PatientPermission.user_id == current_user.id)
    perm_result = await db.execute(perm_stmt)
    allowed_patients = [row[0] for row in perm_result.all()]

    if not allowed_patients:
        # User has no assigned patients, return empty or just personal audit logs
        return GlobalTimelineResponse(events=[], total_count=0)

    # 2. Scatter gather
    chat_stmt = select(ChatThread).where(ChatThread.patient_id.in_(allowed_patients)).order_by(desc(ChatThread.created_at)).limit(limit)
    doc_stmt = select(Document).where(Document.patient_id.in_(allowed_patients)).order_by(desc(Document.created_at)).limit(limit)
    audit_stmt = select(AuditLog).where(AuditLog.user_id == current_user.id).order_by(desc(AuditLog.created_at)).limit(limit)

    chat_res, doc_res, audit_res = await asyncio.gather(
        db.execute(chat_stmt),
        db.execute(doc_stmt),
        db.execute(audit_stmt)
    )

    events = []
    for chat in chat_res.scalars().all():
        events.append(TimelineEventBase(
            event_id=f"chat-{chat.id}",
            timestamp=chat.created_at,
            type="chat",
            title="AI consult started",
            body=chat.title or "New consultation",
            patient_id=chat.patient_id,
            metadata={}
        ))
        
    for doc in doc_res.scalars().all():
        events.append(TimelineEventBase(
            event_id=f"doc-{doc.id}",
            timestamp=doc.created_at,
            type="document",
            title="Document uploaded",
            body=f"{doc.filename} added to patient record",
            patient_id=doc.patient_id,
            metadata={}
        ))
        
    for audit in audit_res.scalars().all():
        events.append(TimelineEventBase(
            event_id=f"audit-{audit.id}",
            timestamp=audit.created_at,
            type="audit",
            title=audit.action,
            body=audit.details.get("reason", "Action logged"),
            patient_id=None,
            metadata={}
        ))

    # 3. Sort and paginate
    events.sort(key=lambda x: x.timestamp, reverse=True)
    paginated_events = events[offset:offset+limit]

    return GlobalTimelineResponse(events=paginated_events, total_count=len(events))
