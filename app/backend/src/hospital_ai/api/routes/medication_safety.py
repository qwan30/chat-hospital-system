"""Medication safety clinical review API routes.
Các endpoint API kiểm tra an toàn sử dụng thuốc (danh sách cảnh báo tương tác thuốc, kiểm tra xung đột đơn thuốc).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_session, require_role
from hospital_ai.services.drug_check import DrugWarning, check_drug_interactions_for_query

router = APIRouter()


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


# Mock data based on conflicts.ts
MOCK_CONFLICTS = [
    {
        "id": "c-001",
        "patient": "Eleanor Vance",
        "patientId": "p-001",
        "drug": "Amiodarone 200mg PO daily",
        "conflictsWith": "Warfarin 5mg PO daily",
        "type": "interaction",
        "severity": "high",
        "rule": "Amiodarone potentiates warfarin → ↑INR",
        "source": "Lexicomp Drug Interactions 2026.4",
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
        "source": "KDIGO 2024 Guidelines",
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
        "source": "Patient allergy chart",
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
        "source": "ACR Manual on Contrast Media v2024",
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
        "source": "Internal pharmacy protocol HP-127",
        "recommendation": "Hold apixaban while on heparin gtt. Document plan.",
        "status": "overridden",
        "ts": "2026-06-11T22:00:00Z",
    },
]


@router.get("/review-queue", response_model=list[DrugConflictOut])
async def get_review_queue(
    _: dict = Depends(require_role(["admin", "pharmacist"])),
) -> list[dict]:
    """Retrieve all open medication conflicts across patients requiring clinical review.
    Lấy danh sách tất cả các xung đột thuốc/tương tác thuốc cần dược sĩ lâm sàng hoặc bác sĩ rà soát.
    """
    return MOCK_CONFLICTS


@router.get("/conflicts/{conflict_id}", response_model=DrugConflictOut)
async def get_conflict(
    conflict_id: str,
    _: dict = Depends(require_role(["admin", "pharmacist", "doctor"])),
) -> dict:
    """Get details of a specific medication conflict or interaction alert.
    Lấy thông tin chi tiết về một cảnh báo xung đột hoặc tương tác thuốc cụ thể.
    """
    for c in MOCK_CONFLICTS:
        if c["id"] == conflict_id:
            return c
    raise HTTPException(status_code=404, detail="Conflict not found")


@router.get("/patients/{patient_id}/review", response_model=list[DrugWarningOut])
async def get_patient_medication_review(
    patient_id: uuid.UUID,
    query_text: str = Query("Check for drug interactions with the patient's current medications."),
    db: AsyncSession = Depends(get_session),
    _: dict = Depends(require_role(["admin", "doctor", "pharmacist", "nurse"])),
) -> list[DrugWarning]:
    """Check for active drug warnings and interactions for a specific patient.
    Kiểm tra và trả về danh sách cảnh báo tương tác thuốc hiện tại đối với hồ sơ của một bệnh nhân.
    """
    return await check_drug_interactions_for_query(
        session=db,
        query_text=query_text,
        patient_id=patient_id,
    )
