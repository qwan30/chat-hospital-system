import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session, require_role
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.models import User
from hospital_ai.services.drug_check import DrugWarning, check_drug_interactions_for_query
from hospital_ai.services.permissions import PermissionService

router = APIRouter()


def require_demo_mode(settings: Settings = Depends(get_settings)) -> Settings:
    """Guard endpoints that return synthetic demo data.

    These fixtures are clinically realistic but entirely fabricated. Serving
    them outside an explicit demo deployment would put un-sourced drug advice
    in front of clinicians, so they are unavailable when demo_mode is off.
    """
    if not settings.demo_mode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint unavailable: synthetic demo data is disabled outside demo mode.",
        )
    return settings


class DrugConflictOut(BaseModel):
    id: str
    patient: str
    patientId: str
    drug: str
    conflictsWith: str
    type: str
    severity: str
    rule: str
    source: str
    recommendation: str
    status: str
    ts: str


class DrugWarningOut(BaseModel):
    drug_name: str
    interacting_entity: str
    interaction_type: str
    severity: str
    evidence_chunk_id: uuid.UUID
    message: str


# SYNTHETIC demo fixtures mirroring the frontend's conflicts.ts.
#
# WARNING: every patient name, drug pairing, and recommendation below is
# fabricated, and the `source` citations do not refer to real publications.
# This data must never be presented as clinical guidance — it exists so the
# pharmacist demo screens have something to render. Access is gated by
# `require_demo_mode`, and each `source` is prefixed to make the payload
# self-labelling if it is ever inspected in isolation.
DEMO_CONFLICTS = [
    {
        "id": "c-001",
        "patient": "Eleanor Vance",
        "patientId": "p-001",
        "drug": "Amiodarone 200mg PO daily",
        "conflictsWith": "Warfarin 5mg PO daily",
        "type": "interaction",
        "severity": "high",
        "rule": "Amiodarone potentiates warfarin → ↑INR",
        "source": "SYNTHETIC DEMO DATA — Lexicomp Drug Interactions 2026.4",
        "recommendation": "Reduce warfarin dose 30-50% and recheck INR in 3-5 days.",
        "status": "open",
        "ts": "2026-06-12T16:00:00Z",
    },
    {
        "id": "c-002",
        "patient": "Priya Raman",
        "patientId": "p-004",
        "drug": "Ibuprofen 600mg PRN",
        "conflictsWith": "CKD stage 3 (eGFR 42)",
        "type": "renal",
        "severity": "high",
        "rule": "NSAIDs contraindicated when eGFR < 60 in CHF",
        "source": "SYNTHETIC DEMO DATA — KDIGO 2024 Guidelines",
        "recommendation": "Use acetaminophen instead. Avoid NSAIDs.",
        "status": "open",
        "ts": "2026-06-12T14:32:00Z",
    },
    {
        "id": "c-003",
        "patient": "Marcus Okafor",
        "patientId": "p-002",
        "drug": "Penicillin G 5 MU IV q6h",
        "conflictsWith": "Documented penicillin allergy (hives, 2018)",
        "type": "allergy",
        "severity": "critical",
        "rule": "Beta-lactam allergy match",
        "source": "SYNTHETIC DEMO DATA — Patient allergy chart",
        "recommendation": "Switch to vancomycin or clindamycin. Confirm allergy severity.",
        "status": "ack",
        "ts": "2026-06-12T11:20:00Z",
    },
    {
        "id": "c-004",
        "patient": "Hassan Karimi",
        "patientId": "p-007",
        "drug": "Metformin 1g BID",
        "conflictsWith": "Contrast study scheduled tomorrow",
        "type": "interaction",
        "severity": "moderate",
        "rule": "Hold metformin 48h pre/post IV contrast (eGFR < 60)",
        "source": "SYNTHETIC DEMO DATA — ACR Manual on Contrast Media v2024",
        "recommendation": "Hold metformin starting today. Resume 48h post-contrast.",
        "status": "open",
        "ts": "2026-06-12T10:00:00Z",
    },
    {
        "id": "c-005",
        "patient": "Noah Petersen",
        "patientId": "p-011",
        "drug": "Heparin gtt",
        "conflictsWith": "Apixaban 5mg BID (home med)",
        "type": "duplicate",
        "severity": "moderate",
        "rule": "Overlapping anticoagulation increases bleeding risk",
        "source": "SYNTHETIC DEMO DATA — Internal pharmacy protocol HP-127",
        "recommendation": "Hold apixaban while on heparin gtt. Document plan.",
        "status": "overridden",
        "ts": "2026-06-11T22:00:00Z",
    },
]


@router.get("/review-queue", response_model=list[DrugConflictOut])
async def get_review_queue(
    _: dict = Depends(require_role(["admin", "pharmacist"])),
    __: Settings = Depends(require_demo_mode),
) -> list[dict]:
    """Return the synthetic pharmacist review queue. Demo-mode only."""
    return DEMO_CONFLICTS


@router.get("/conflicts/{conflict_id}", response_model=DrugConflictOut)
async def get_conflict(
    conflict_id: str,
    _: dict = Depends(require_role(["admin", "pharmacist", "doctor"])),
    __: Settings = Depends(require_demo_mode),
) -> dict:
    """Return one synthetic conflict record. Demo-mode only."""
    for c in DEMO_CONFLICTS:
        if c["id"] == conflict_id:
            return c
    raise HTTPException(status_code=404, detail="Conflict not found")


@router.get("/patients/{patient_id}/review", response_model=list[DrugWarningOut])
async def get_patient_medication_review(
    patient_id: uuid.UUID,
    request: Request,
    query_text: str = Query("Check for drug interactions with the patient's current medications."),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    _: dict = Depends(require_role(["admin", "doctor", "pharmacist", "nurse"])),
) -> list[DrugWarning]:
    # This endpoint returns real patient graph data, so a role check alone is not
    # sufficient -- without a patient-scope check any doctor or nurse could read
    # drug interactions for any patient_id. require_read enforces the ABAC grant
    # and records the audit entry that this route previously never wrote.
    trace_id = new_trace_id()
    await PermissionService(db).require_read(
        user=current_user,
        patient_id=patient_id,
        action="medication.review.read",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )
    return await check_drug_interactions_for_query(
        session=db,
        query_text=query_text,
        patient_id=patient_id,
    )
