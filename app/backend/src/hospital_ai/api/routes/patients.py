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
from hospital_ai.schemas.documents import DocumentRead
from hospital_ai.schemas.patients import (
    PatientLabItem,
    PatientLabResponse,
    PatientMedicationItem,
    PatientMedicationResponse,
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


@router.get("/{patient_id}/medications", response_model=PatientMedicationResponse)
async def get_patient_medications(
    patient_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PatientMedicationResponse:
    """Return structured medication list for a patient from indexed documents."""
    trace_id = new_trace_id()
    await PermissionService(session).require_read(
        user=current_user,
        patient_id=patient_id,
        action="patient.medications.read",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )

    patient = await session.get(Patient, patient_id)
    if patient is None or patient.deleted_at is not None:
        from hospital_ai.core.errors import NotFoundError

        raise NotFoundError("Patient not found.")

    # Query medication-related documents: prescriptions and discharge summaries
    stmt = (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.patient_id == patient_id,
            Document.patient_id == patient_id,
            Document.document_type.in_(["prescription", "discharge_summary"]),
            Document.status == "indexed",
            DocumentChunk.deleted_at.is_(None),
            Document.deleted_at.is_(None),
        )
        .order_by(Document.created_at.desc())
        .limit(50)
    )
    result = await session.execute(stmt)
    rows = result.all()

    # Parse structured medications from document content and metadata
    medications: list[PatientMedicationItem] = []
    seen_meds: set[str] = set()

    for chunk, doc in rows:
        content = chunk.content or ""
        meta = chunk.meta or {}
        doc_title = doc.title or ""

        # Extract medication entries from chunk metadata if available
        meds_from_meta = meta.get("medications", meta.get("meds", []))
        if isinstance(meds_from_meta, list):
            for med in meds_from_meta:
                if isinstance(med, dict):
                    drug = med.get("name", med.get("drug", ""))
                    if drug and drug.lower() not in seen_meds:
                        seen_meds.add(drug.lower())
                        medications.append(
                            PatientMedicationItem(
                                drug_name=str(drug),
                                dose=med.get("dose"),
                                route=med.get("route"),
                                frequency=med.get("frequency"),
                                started=med.get("started"),
                                prescriber=med.get("prescriber"),
                                source_document_id=doc.id,
                                source_document_title=doc_title,
                            )
                        )
        else:
            # Parse from text content (prescription format: "- Drug dose, frequency")
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("- ") or line.startswith("• "):
                    line = line.lstrip("- •").strip()
                    drug_name = line.split()[0] if line else ""
                    if drug_name and drug_name.lower() not in seen_meds and len(drug_name) > 2:
                        seen_meds.add(drug_name.lower())
                        dose_match = _extract_dose(line)
                        medications.append(
                            PatientMedicationItem(
                                drug_name=drug_name,
                                dose=dose_match,
                                route="PO" if "viên" in content.lower() or "uống" in content.lower() else None,
                                frequency=None,
                                started=str(doc.created_at.date()) if doc.created_at else None,
                                prescriber=_extract_doctor(content),
                                source_document_id=doc.id,
                                source_document_title=doc_title,
                            )
                        )

    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="patient.medications.read",
        object_type="patient",
        object_id=patient_id,
        patient_id=patient_id,
        outcome="allowed",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
        metadata={"medication_count": len(medications)},
    )
    await session.commit()

    return PatientMedicationResponse(patient_id=patient_id, medications=medications)


@router.get("/{patient_id}/labs", response_model=PatientLabResponse)
async def get_patient_labs(
    patient_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PatientLabResponse:
    """Return structured lab results for a patient from indexed documents."""
    trace_id = new_trace_id()
    await PermissionService(session).require_read(
        user=current_user,
        patient_id=patient_id,
        action="patient.labs.read",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )

    patient = await session.get(Patient, patient_id)
    if patient is None or patient.deleted_at is not None:
        from hospital_ai.core.errors import NotFoundError

        raise NotFoundError("Patient not found.")

    # Query lab result documents
    stmt = (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.patient_id == patient_id,
            Document.patient_id == patient_id,
            Document.document_type.in_(["lab_result", "hms_lab_result"]),
            Document.status == "indexed",
            DocumentChunk.deleted_at.is_(None),
            Document.deleted_at.is_(None),
        )
        .order_by(Document.created_at.desc())
        .limit(50)
    )
    result = await session.execute(stmt)
    rows = result.all()

    labs: list[PatientLabItem] = []

    for chunk, doc in rows:
        content = chunk.content or ""
        meta = chunk.meta or {}
        doc_title = doc.title or ""

        # Extract lab entries from chunk metadata if available
        labs_from_meta = meta.get("labs", meta.get("lab_results", []))
        if isinstance(labs_from_meta, list):
            for lab in labs_from_meta:
                if isinstance(lab, dict):
                    analyte = lab.get("analyte", lab.get("test", lab.get("testName", "")))
                    if analyte:
                        value_str = lab.get("value", lab.get("result", ""))
                        ref_str = lab.get("reference_range", lab.get("referenceRange", lab.get("ref", "")))
                        flag = _compute_lab_flag(str(value_str), str(ref_str)) if value_str and ref_str else None
                        labs.append(
                            PatientLabItem(
                                analyte=str(analyte),
                                value=str(value_str) if value_str else None,
                                reference_range=str(ref_str) if ref_str else None,
                                flag=flag,
                                collected=str(doc.created_at.date()) if doc.created_at else None,
                                source_document_id=doc.id,
                                source_document_title=doc_title,
                            )
                        )
        else:
            # Parse from text content: lines with analyte patterns
            lab_matches = _parse_lab_content(content)
            for lab_item in lab_matches:
                lab_item.source_document_id = doc.id
                lab_item.source_document_title = doc_title
                if lab_item.collected is None and doc.created_at:
                    lab_item.collected = str(doc.created_at.date())
                labs.append(lab_item)

    # Deduplicate by analyte name, keeping the most recent
    seen_analytes: set[str] = set()
    deduped_labs: list[PatientLabItem] = []
    for lab in labs:
        key = lab.analyte.lower()
        if key not in seen_analytes:
            seen_analytes.add(key)
            deduped_labs.append(lab)

    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="patient.labs.read",
        object_type="patient",
        object_id=patient_id,
        patient_id=patient_id,
        outcome="allowed",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
        metadata={"lab_count": len(deduped_labs)},
    )
    await session.commit()

    return PatientLabResponse(patient_id=patient_id, labs=deduped_labs)


@router.get("/{patient_id}/documents", response_model=list[DocumentRead])
async def get_patient_documents(
    patient_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[DocumentRead]:
    """Return documents for a patient (permission-filtered)."""
    trace_id = new_trace_id()
    await PermissionService(session).require_read(
        user=current_user,
        patient_id=patient_id,
        action="patient.documents.read",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )

    patient = await session.get(Patient, patient_id)
    if patient is None or patient.deleted_at is not None:
        from hospital_ai.core.errors import NotFoundError

        raise NotFoundError("Patient not found.")

    stmt = (
        select(Document)
        .where(
            Document.patient_id == patient_id,
            Document.deleted_at.is_(None),
        )
        .order_by(Document.created_at.desc())
        .limit(100)
    )
    result = await session.execute(stmt)
    documents = list(result.scalars().all())

    await AuditService(session).record(
        actor_user_id=current_user.id,
        action="patient.documents.read",
        object_type="patient",
        object_id=patient_id,
        patient_id=patient_id,
        outcome="allowed",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
        metadata={"document_count": len(documents)},
    )
    await session.commit()

    return [
        DocumentRead(
            id=doc.id,
            patient_id=doc.patient_id,
            uploaded_by=doc.uploaded_by,
            title=doc.title,
            document_type=doc.document_type,
            storage_uri=doc.storage_uri,
            mime_type=doc.mime_type,
            status=doc.status,
            page_count=doc.page_count,
            ocr_error=doc.ocr_error,
            created_at=doc.created_at,
        )
        for doc in documents
    ]


# ── Helper parsers ──────────────────────────────────────────────────


def _extract_dose(text: str) -> Optional[str]:
    """Extract dose pattern like '5mg', '500mg', '10mg' from text."""
    import re

    m = re.search(r"(\d+\.?\d*\s*(?:mg|mcg|g|ml|IU|uL|mmol)(?:\s*(?:BID|TID|QID|daily|/ngày))?)", text, re.IGNORECASE)
    return m.group(1) if m else None


def _extract_doctor(text: str) -> Optional[str]:
    """Extract doctor name from text like 'BS. Nguyen Thi Lan'."""
    import re

    m = re.search(r"BS\.\s*([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)+)", text)
    return m.group(1) if m else None


def _parse_lab_content(content: str) -> list[PatientLabItem]:
    """Parse lab results from structured text content."""
    import re

    results: list[PatientLabItem] = []
    # Pattern: analyte name followed by value and optional reference range
    # Match lines like: "Hemoglobin (HGB)                  12.5     12.0-16.0 g/dL"
    lab_pattern = re.compile(
        r"^([A-Za-zÀ-Ỹà-ỹ][A-Za-zÀ-Ỹà-ỹ\s\-().,]+?)\s{2,}"  # analyte name
        r"([\d.]+(?:\s*[x×]\s*\d+[⁰¹²³⁴⁵⁶⁷⁸⁹]*(?:/[A-Za-z]+)?)?)\s+"  # value
        r"([\d.<>]+\s*[-–]\s*[\d.<>]+(?:\s*[A-Za-z/%]+)?)",  # reference range
        re.MULTILINE,
    )
    for match in lab_pattern.finditer(content):
        analyte = match.group(1).strip()
        value = match.group(2).strip()
        ref_range = match.group(3).strip()
        flag = _compute_lab_flag(value, ref_range)
        results.append(
            PatientLabItem(
                analyte=analyte,
                value=value,
                reference_range=ref_range,
                flag=flag,
            )
        )

    # Also try simpler pattern: "Analyte: Value (Ref: range)"
    simple_pattern = re.compile(
        r"^([A-Za-zÀ-Ỹà-ỹ][A-Za-zÀ-Ỹà-ỹ\s\-().]+?):\s*([\d.]+)\s*(?:\(.*?([\d.]+\s*[-–]\s*[\d.]+).*?\))?",
        re.MULTILINE,
    )
    for match in simple_pattern.finditer(content):
        analyte = match.group(1).strip()
        value = match.group(2).strip()
        ref = match.group(3)
        if analyte.lower() not in {r.analyte.lower() for r in results} and len(analyte) > 2:
            flag = _compute_lab_flag(value, ref) if ref else None
            results.append(
                PatientLabItem(
                    analyte=analyte,
                    value=value,
                    reference_range=ref.strip() if ref else None,
                    flag=flag,
                )
            )

    return results


def _compute_lab_flag(value: str, ref_range: Optional[str]) -> Optional[str]:
    """Compute H/L flag by comparing numeric value to reference range."""
    import re

    try:
        val_num = float(re.search(r"[\d.]+", value).group()) if re.search(r"[\d.]+", value) else None
    except (ValueError, AttributeError):
        return None

    if val_num is None or not ref_range:
        return None

    try:
        ref_nums = re.findall(r"[\d.]+", ref_range)
        if len(ref_nums) >= 2:
            low = float(ref_nums[0])
            high = float(ref_nums[-1])
            if val_num > high:
                return "H"
            if val_num < low:
                return "L"
    except (ValueError, AttributeError):
        logger.debug("Unable to compute lab flag for value=%r ref_range=%r", value, ref_range)
        return None

    return None
