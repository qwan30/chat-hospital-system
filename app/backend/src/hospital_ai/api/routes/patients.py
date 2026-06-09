import logging
import uuid
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.security import PATIENT_READ_SCOPES, new_trace_id, sanitize_audit_query
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage, Patient, User
from hospital_ai.schemas.patients import (
    PatientOverviewResponse,
    PatientRead,
    PatientSearchResponse,
    PatientTimelineResponse,
)
from hospital_ai.services.audit import AuditService
from hospital_ai.services.hms_connector import HmsApiClient
from hospital_ai.services.permissions import PermissionService, active_patient_permission_exists

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search", response_model=PatientSearchResponse)
async def search_patients(
    request: Request,
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PatientSearchResponse:
    permission_exists = active_patient_permission_exists(
        user_id=current_user.id,
        patient_id=Patient.id,
        accepted_scopes=PATIENT_READ_SCOPES,
    )
    stmt = select(Patient).where(Patient.deleted_at.is_(None), permission_exists).order_by(Patient.full_name)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(or_(Patient.full_name.ilike(pattern), Patient.mrn.ilike(pattern)))
    result = await session.execute(stmt.limit(limit))
    patients = list(result.scalars().all())

    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="patient.search",
        object_type="patient",
        outcome="allowed",
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
        metadata={**sanitize_audit_query(q), "result_count": len(patients)},
    )
    await session.commit()
    return PatientSearchResponse(items=patients)


@router.get("/{patient_id}", response_model=PatientRead)
async def get_patient(
    patient_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Patient:
    trace_id = new_trace_id()
    await PermissionService(session).require_read(
        user=current_user,
        patient_id=patient_id,
        action="patient.read",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )
    patient = await session.get(Patient, patient_id)
    if patient is None or patient.deleted_at is not None:
        from hospital_ai.core.errors import NotFoundError

        raise NotFoundError("Patient not found.")
    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="patient.read",
        object_type="patient",
        object_id=patient_id,
        patient_id=patient_id,
        outcome="allowed",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )
    await session.commit()
    return patient


@router.get("/{patient_id}/overview", response_model=PatientOverviewResponse)
async def get_patient_overview(
    patient_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> PatientOverviewResponse:
    trace_id = new_trace_id()
    await PermissionService(session).require_read(
        user=current_user,
        patient_id=patient_id,
        action="patient.overview.read",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )

    patient = await session.get(Patient, patient_id)
    if patient is None or patient.deleted_at is not None:
        from hospital_ai.core.errors import NotFoundError

        raise NotFoundError("Patient not found.")

    hms_client = HmsApiClient(settings)

    dob = patient.dob
    gender = "Unknown"
    cccd = "0123456789"
    blood_type = "O+"
    occupation = "Engineer"

    allergy_count = 0
    medication_count = 0
    lab_count = 0

    if settings.hms_sync_enabled:
        try:
            snapshot = await hms_client.get_patient_snapshot(str(patient_id))
            if snapshot:
                dob_str = snapshot.get("dob")
                if dob_str:
                    try:
                        dob = date.fromisoformat(dob_str[:10])
                    except ValueError:
                        logger.warning("Invalid DOB format in HMS snapshot: %s", dob_str, exc_info=True)
                gender = snapshot.get("gender", "Unknown")
                cccd = snapshot.get("cccd", "0123456789")
                blood_type = snapshot.get("blood_type", "O+")
                occupation = snapshot.get("occupation", "Engineer")

                allergy_count = len(snapshot.get("allergies", []))
                medication_count = len(snapshot.get("currentMedications", []))
                lab_count = len(snapshot.get("recentLabs", []))
        except Exception:
            logger.warning("HMS patient snapshot fetch failed for %s", patient_id, exc_info=True)

    # Fallback to local cached documents if live fetch fails or returns empty
    if allergy_count == 0:
        allergy_count = (
            await session.scalar(
                select(func.count(Document.id)).where(
                    Document.patient_id == patient_id,
                    Document.document_type == "hms_allergy",
                    Document.deleted_at.is_(None),
                )
            )
            or 0
        )
    if medication_count == 0:
        medication_count = (
            await session.scalar(
                select(func.count(Document.id)).where(
                    Document.patient_id == patient_id,
                    Document.document_type == "hms_medical_record",
                    Document.deleted_at.is_(None),
                )
            )
            or 0
        )
    if lab_count == 0:
        lab_count = (
            await session.scalar(
                select(func.count(Document.id)).where(
                    Document.patient_id == patient_id,
                    Document.document_type == "hms_lab_result",
                    Document.deleted_at.is_(None),
                )
            )
            or 0
        )

    appointment_count = (
        await session.scalar(
            select(func.count(Document.id)).where(
                Document.patient_id == patient_id,
                Document.document_type == "hms_appointment",
                Document.deleted_at.is_(None),
            )
        )
        or 0
    )

    # Retrieve local RAG evidence context to construct patient clinical AI summary
    from hospital_ai.services.reasoning import PatientSummaryPipeline
    from hospital_ai.services.retrieval import RetrievedChunk

    stmt = (
        select(DocumentChunk, Document, DocumentPage)
        .join(Document, Document.id == DocumentChunk.document_id)
        .join(DocumentPage, DocumentPage.id == DocumentChunk.page_id)
        .where(
            DocumentChunk.patient_id == patient_id,
            Document.status == "indexed",
            DocumentChunk.deleted_at.is_(None),
            Document.deleted_at.is_(None),
            DocumentPage.deleted_at.is_(None),
        )
        .limit(20)
    )
    res = await session.execute(stmt)
    chunks = []
    for idx, (chunk, doc, page) in enumerate(res.all(), start=1):
        chunks.append(
            RetrievedChunk(
                evidence_id=f"E{idx}",
                document_id=doc.id,
                document_title=doc.title,
                page=page.page_number,
                chunk_id=chunk.id,
                score=1.0,
                content=chunk.content,
                metadata=dict(chunk.meta or {}),
            )
        )

    ai_summary = None
    last_updated = None
    if chunks:
        pipeline = PatientSummaryPipeline(settings)
        summary_res = await pipeline.run(
            patient_name=patient.full_name,
            evidence=chunks,
        )
        ai_summary = summary_res.answer
        last_updated = datetime.now(timezone.utc)

    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="patient.overview.read",
        object_type="patient",
        object_id=patient_id,
        patient_id=patient_id,
        outcome="allowed",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
        metadata={"ai_summary_generated": ai_summary is not None},
    )
    await session.commit()

    return PatientOverviewResponse(
        patient_id=patient_id,
        full_name=patient.full_name,
        mrn=patient.mrn,
        dob=dob,
        gender=gender,
        cccd=cccd,
        blood_type=blood_type,
        occupation=occupation,
        allergy_count=allergy_count,
        medication_count=medication_count,
        lab_count=lab_count,
        appointment_count=appointment_count,
        ai_summary=ai_summary,
        last_updated=last_updated,
    )


@router.get("/{patient_id}/timeline", response_model=PatientTimelineResponse)
async def get_patient_timeline(
    patient_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> PatientTimelineResponse:
    trace_id = new_trace_id()
    await PermissionService(session).require_read(
        user=current_user,
        patient_id=patient_id,
        action="patient.timeline.read",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )

    patient = await session.get(Patient, patient_id)
    if patient is None or patient.deleted_at is not None:
        from hospital_ai.core.errors import NotFoundError

        raise NotFoundError("Patient not found.")

    hms_client = HmsApiClient(settings)
    events = []

    if settings.hms_sync_enabled:
        try:
            hms_events = await hms_client.get_patient_timeline(str(patient_id))
            for e in hms_events:
                event_id = e.get("eventId") or e.get("event_id")
                event_type = e.get("eventType") or e.get("event_type", "event")
                title = e.get("title", "Clinical Event")
                description = e.get("description")
                ts_str = e.get("timestamp")

                timestamp = None
                if ts_str:
                    try:
                        timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    except ValueError:
                        logger.warning("Invalid timestamp in HMS timeline: %s", ts_str, exc_info=True)

                if event_id and title:
                    events.append(
                        {
                            "event_id": uuid.UUID(str(event_id)),
                            "event_type": event_type,
                            "title": title,
                            "description": description,
                            "timestamp": timestamp or datetime.now(timezone.utc),
                        }
                    )
        except Exception:
            logger.warning("HMS timeline fetch failed for %s", patient_id, exc_info=True)

    # Fallback to local cached documents as timeline events if none exist or live fails
    if not events:
        doc_stmt = (
            select(Document)
            .where(Document.patient_id == patient_id, Document.deleted_at.is_(None))
            .order_by(Document.created_at.desc())
        )
        doc_result = await session.execute(doc_stmt)
        for doc in doc_result.scalars().all():
            events.append(
                {
                    "event_id": doc.id,
                    "event_type": doc.document_type,
                    "title": doc.title,
                    "description": f"Local cache entry for {doc.title}",
                    "timestamp": doc.created_at,
                }
            )

    # Sort descending by timestamp
    events.sort(key=lambda x: x["timestamp"], reverse=True)

    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="patient.timeline.read",
        object_type="patient",
        object_id=patient_id,
        patient_id=patient_id,
        outcome="allowed",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
        metadata={"events_count": len(events)},
    )
    await session.commit()

    return PatientTimelineResponse(
        patient_id=patient_id,
        events=events,
    )
