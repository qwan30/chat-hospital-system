from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.api.limiter import limiter
from hospital_ai.core.security import PATIENT_READ_SCOPES, new_trace_id, sanitize_audit_query
from hospital_ai.db.models import ChatThread, ChatThreadParticipant, Document, Patient, User
from hospital_ai.schemas.search import GlobalSearchResponse
from hospital_ai.services.audit import AuditService
from hospital_ai.services.permissions import active_patient_permission_exists

router = APIRouter()


@router.get("/global", response_model=GlobalSearchResponse)
@limiter.limit("20/minute")
async def global_search(
    request: Request,
    q: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> GlobalSearchResponse:
    trace_id = new_trace_id()

    if not q or not q.strip():
        return GlobalSearchResponse(patients=[], documents=[], threads=[])

    q_clean = q.strip()
    pattern = f"%{q_clean}%"

    # 1. Search Patients with active read scope
    patient_permission_exists = active_patient_permission_exists(
        user_id=current_user.id,
        patient_id=Patient.id,
        accepted_scopes=PATIENT_READ_SCOPES,
    )
    patient_stmt = (
        select(Patient)
        .where(
            Patient.deleted_at.is_(None),
            patient_permission_exists,
            or_(Patient.full_name.ilike(pattern), Patient.mrn.ilike(pattern))
        )
        .order_by(Patient.full_name)
    )
    patient_result = await session.execute(patient_stmt)
    patients = list(patient_result.scalars().all())

    # 2. Search Documents with active read scope on patient
    doc_permission_exists = active_patient_permission_exists(
        user_id=current_user.id,
        patient_id=Document.patient_id,
        accepted_scopes=PATIENT_READ_SCOPES,
    )
    doc_stmt = (
        select(Document)
        .where(
            Document.deleted_at.is_(None),
            doc_permission_exists,
            Document.title.ilike(pattern)
        )
        .order_by(Document.title)
    )
    doc_result = await session.execute(doc_stmt)
    documents = list(doc_result.scalars().all())

    # 3. Search ChatThreads with active permissions on patient or general scope
    thread_permission_exists = active_patient_permission_exists(
        user_id=current_user.id,
        patient_id=ChatThread.patient_id,
        accepted_scopes=PATIENT_READ_SCOPES,
    )
    thread_stmt = (
        select(ChatThread)
        .join(ChatThreadParticipant)
        .where(
            ChatThread.deleted_at.is_(None),
            ChatThread.status == "active",
            ChatThreadParticipant.deleted_at.is_(None),
            ChatThreadParticipant.user_id == current_user.id,
            or_(ChatThread.scope == "general", thread_permission_exists),
            ChatThread.title.ilike(pattern)
        )
        .order_by(ChatThread.updated_at.desc())
    )
    thread_result = await session.execute(thread_stmt)
    threads = list(thread_result.scalars().unique().all())

    # 4. Record Audit Log
    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="search.global",
        object_type="search",
        outcome="allowed",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
        metadata={
            **sanitize_audit_query(q_clean),
            "patient_matches": len(patients),
            "document_matches": len(documents),
            "thread_matches": len(threads),
        },
    )
    await session.commit()

    return GlobalSearchResponse(
        patients=patients,
        documents=documents,
        threads=threads,
    )
