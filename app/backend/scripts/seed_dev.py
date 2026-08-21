"""Seed development database with rich synthetic data.

Creates 3 patients with distinct clinical documents per patient:
  - Alice Synthetic  (Internal Medicine)
  - Bob Synthetic    (Cardiology)
  - Eleanor Vance    (Cardiology / AFib / CKD)

Each patient gets:
  - 1 appointment summary (HMS evidence via HmsAppointmentEvidenceImporter)
  - 1 prescription document
  - 1 lab result document
  - Graph entities and relations derived from their documents
"""

import asyncio
import sys
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Optional

# Ensure src is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
sys.path.insert(0, "src")

from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.migrations import (
    ADMIN_ID,
    DOCTOR_ID,
    PATIENT_ALICE_ID,
    PATIENT_BOB_ID,
    PATIENT_ELEANOR_ID,
    seed_synthetic_data,
)
from hospital_ai.db.models import AccessRequest, Document, DocumentChunk, DocumentPage, User
from hospital_ai.db.session import get_session_factory
from hospital_ai.schemas.hms import HmsAppointmentSummaryImport
from hospital_ai.services.graph_rag import GraphEntity, GraphRelation
from hospital_ai.services.hms_appointments import HmsAppointmentEvidenceImporter

SYNTHETIC_APPOINTMENT_ID = uuid.UUID("30000000-0000-0000-0000-000000000001")
SYNTHETIC_APPOINTMENT_ID_ELEANOR = uuid.UUID("30000000-0000-0000-0000-000000000002")
SYNTHETIC_APPOINTMENT_ID_BOB = uuid.UUID("30000000-0000-0000-0000-000000000003")

# ── Document / Chunk IDs (stable UUIDs for idempotency) ─────────────────────

# Alice
DOC_ALICE_PRESCRIPTION_ID = uuid.UUID("40000000-0000-0000-0000-000000000001")
DOC_ALICE_LAB_ID = uuid.UUID("40000000-0000-0000-0000-000000000002")

# Bob
DOC_BOB_PRESCRIPTION_ID = uuid.UUID("40000000-0000-0000-0000-000000000003")
DOC_BOB_LAB_ID = uuid.UUID("40000000-0000-0000-0000-000000000004")
DOC_BOB_DISCHARGE_ID = uuid.UUID("40000000-0000-0000-0000-000000000005")

# Eleanor
DOC_ELEANOR_PRESCRIPTION_ID = uuid.UUID("40000000-0000-0000-0000-000000000006")
DOC_ELEANOR_LAB_ID = uuid.UUID("40000000-0000-0000-0000-000000000007")


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _doc_exists(session: AsyncSession, doc_id: uuid.UUID) -> bool:
    from sqlalchemy import select

    r = await session.execute(select(Document).where(Document.id == doc_id))
    return r.scalar_one_or_none() is not None


async def _add_document(
    session: AsyncSession,
    settings: Optional[Settings] = None,
    *,
    doc_id: uuid.UUID,
    patient_id: uuid.UUID,
    uploader_id: uuid.UUID,
    title: str,
    document_type: str,
    content: str,
    chunk_meta: dict,
    chunk_uuid: uuid.UUID,
    page_uuid: uuid.UUID,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Create or update Document with CDI generation, embeddings, and return (chunk_id, doc_id)."""
    from sqlalchemy import select

    from hospital_ai.core.config import get_settings
    from hospital_ai.workers.generation_jobs import import_synthetic_generation

    if settings is None:
        settings = get_settings()

    r = await session.execute(select(Document).where(Document.id == doc_id))
    doc = r.scalar_one_or_none()

    if doc is None:
        doc = Document(
            id=doc_id,
            patient_id=patient_id,
            uploaded_by=uploader_id,
            title=title,
            document_type=document_type,
            storage_uri=f"memory://synthetic/{doc_id}",
            mime_type="text/plain",
            status="ready",
            page_count=1,
            index_generation=0,
        )
        session.add(doc)
        await session.flush()
    else:
        doc.uploaded_by = uploader_id
        doc.title = title
        doc.status = "ready"
        doc.page_count = 1
        await session.flush()

    await import_synthetic_generation(
        session=session,
        settings=settings,
        document=doc,
        content=content,
        user_id=uploader_id,
        metadata=chunk_meta,
    )
    await session.commit()
    await session.refresh(doc)

    res = await session.execute(
        select(DocumentChunk).where(
            DocumentChunk.document_id == doc_id,
            DocumentChunk.generation_id == doc.active_index_generation_id,
        )
    )
    chunk = res.scalars().first()
    actual_chunk_id = chunk.id if chunk else chunk_uuid
    return actual_chunk_id, doc.id


async def _add_graph_entity(
    session: AsyncSession,
    entity_id: uuid.UUID,
    name: str,
    entity_type: str,
    chunk_id: uuid.UUID,
    document_id: uuid.UUID,
) -> None:
    from sqlalchemy import select

    r = await session.execute(select(GraphEntity).where(GraphEntity.id == entity_id))
    existing = r.scalar_one_or_none()
    if existing is None:
        session.add(
            GraphEntity(
                id=entity_id,
                name=name,
                entity_type=entity_type,
                source_chunk_id=chunk_id,
                source_document_id=document_id,
                confidence=0.95,
            )
        )
    else:
        existing.name = name
        existing.entity_type = entity_type
        existing.source_chunk_id = chunk_id
        existing.source_document_id = document_id
        existing.confidence = 0.95


async def _add_graph_relation(
    session: AsyncSession,
    relation_id: uuid.UUID,
    source_entity_id: uuid.UUID,
    target_entity_id: uuid.UUID,
    relation_type: str,
    chunk_id: uuid.UUID,
) -> None:
    from sqlalchemy import select

    r = await session.execute(select(GraphRelation).where(GraphRelation.id == relation_id))
    existing = r.scalar_one_or_none()
    if existing is None:
        session.add(
            GraphRelation(
                id=relation_id,
                source_entity_id=source_entity_id,
                target_entity_id=target_entity_id,
                relation_type=relation_type,
                weight=1.0,
                source_chunk_id=chunk_id,
            )
        )
    else:
        existing.source_entity_id = source_entity_id
        existing.target_entity_id = target_entity_id
        existing.relation_type = relation_type
        existing.weight = 1.0
        existing.source_chunk_id = chunk_id


# ── Main seed function ───────────────────────────────────────────────────────


async def main() -> None:
    settings = get_settings()
    session_factory = get_session_factory()

    async with session_factory() as session:
        # 1. Core users, patients, and basic permissions
        await seed_synthetic_data(session)
        admin = await session.get(User, ADMIN_ID)

        # 1b. Grant Bob Synthetic permissions for local dev.
        #     Bob is intentionally excluded from migrations.py to keep security tests intact.
        from hospital_ai.db.migrations import (
            NURSE_ID as _NURSE_ID,
        )
        from hospital_ai.db.migrations import (
            PHARMACIST_ID as _PHARMACIST_ID,
        )
        from hospital_ai.db.migrations import (
            RECORDS_ID as _RECORDS_ID,
        )
        from hospital_ai.db.migrations import (
            _add_missing_permissions,
        )
        from hospital_ai.db.models import PatientPermission as PP

        await _add_missing_permissions(
            session,
            [
                PP(user_id=DOCTOR_ID, patient_id=PATIENT_BOB_ID, scope="read"),
                PP(user_id=DOCTOR_ID, patient_id=PATIENT_BOB_ID, scope="summary"),
                PP(user_id=DOCTOR_ID, patient_id=PATIENT_BOB_ID, scope="medication"),
                PP(user_id=_RECORDS_ID, patient_id=PATIENT_BOB_ID, scope="upload"),
                PP(user_id=ADMIN_ID, patient_id=PATIENT_BOB_ID, scope="admin"),
                PP(user_id=_NURSE_ID, patient_id=PATIENT_BOB_ID, scope="read"),
                PP(user_id=_NURSE_ID, patient_id=PATIENT_BOB_ID, scope="summary"),
                PP(user_id=_PHARMACIST_ID, patient_id=PATIENT_BOB_ID, scope="read"),
                PP(user_id=_PHARMACIST_ID, patient_id=PATIENT_BOB_ID, scope="medication"),
            ],
        )
        await session.commit()

        # 2. HMS Appointment Evidence ─────────────────────────────────────────
        await HmsAppointmentEvidenceImporter(session, settings).import_summary(
            user=admin,
            payload=HmsAppointmentSummaryImport(
                source_appointment_id=SYNTHETIC_APPOINTMENT_ID,
                patient_id=PATIENT_ALICE_ID,
                source_patient_id=PATIENT_ALICE_ID,
                appointment_date=date(2026, 4, 28),
                status="CHECKED_IN",
                department="Internal Medicine",
                doctor_name="Dr. Dev Doctor",
                start_time="09:00",
                end_time="09:30",
                reason="Routine follow-up & medication review",
                symptoms="Mild fatigue, occasional headaches. Denies chest pain.",
                vital_signs_summary="BP 122/76, HR 72, SpO2 99%, Temp 36.8°C.",
                follow_up_summary="Lisinopril 10 mg daily continued. Check HbA1c at next visit.",
            ),
            trace_id=new_trace_id(),
            ip_address="127.0.0.1",
        )

        await HmsAppointmentEvidenceImporter(session, settings).import_summary(
            user=admin,
            payload=HmsAppointmentSummaryImport(
                source_appointment_id=SYNTHETIC_APPOINTMENT_ID_ELEANOR,
                patient_id=PATIENT_ELEANOR_ID,
                source_patient_id=PATIENT_ELEANOR_ID,
                appointment_date=date(2026, 6, 10),
                status="COMPLETED",
                department="Cardiology",
                doctor_name="Dr. Dev Doctor",
                start_time="10:00",
                end_time="10:30",
                reason="Routine AFib follow up",
                symptoms="Patient reports occasional palpitations. Denies shortness of breath. History of AFib, CKD stage 3.",  # noqa: E501
                vital_signs_summary="BP 135/85, HR 88 (irregular), SpO2 97%.",
                follow_up_summary=(
                    "Continue Apixaban 5mg BID. Renal labs: Creatinine 1.6, eGFR 42. "
                    "Metoprolol succinate 50mg daily. Note: Sulfa allergy (hives)."
                ),
            ),
            trace_id=new_trace_id(),
            ip_address="127.0.0.1",
        )

        await HmsAppointmentEvidenceImporter(session, settings).import_summary(
            user=admin,
            payload=HmsAppointmentSummaryImport(
                source_appointment_id=SYNTHETIC_APPOINTMENT_ID_BOB,
                patient_id=PATIENT_BOB_ID,
                source_patient_id=PATIENT_BOB_ID,
                appointment_date=date(2026, 5, 15),
                status="COMPLETED",
                department="Cardiology",
                doctor_name="Dr. Dev Doctor",
                start_time="14:00",
                symptoms=(
                    "Bob reports mild dyspnea on exertion. No active chest pain. "
                    "History of CAD, CABG 2023. Hypertension."
                ),
                vital_signs_summary="BP 138/88, HR 80, SpO2 96%.",
                follow_up_summary=(
                    "Continue Aspirin 81mg daily, Atorvastatin 40mg nightly, "
                    "Carvedilol 6.25mg BID. Schedule echocardiogram. "
                    "LDL: 72 mg/dL, Troponin I: 0.02 ng/mL (normal)."
                ),
            ),
            trace_id=new_trace_id(),
            ip_address="127.0.0.1",
        )

        # 3. Alice — Prescription & Labs ──────────────────────────────────────
        ALICE_CHUNK_PRESC = uuid.UUID("50000000-0000-0000-0000-000000000001")
        ALICE_PAGE_PRESC = uuid.UUID("50000000-0000-0000-0000-000000000011")
        c_alice_presc, d_alice_presc = await _add_document(
            session,
            settings,
            doc_id=DOC_ALICE_PRESCRIPTION_ID,
            patient_id=PATIENT_ALICE_ID,
            uploader_id=admin.id,
            title="Alice Synthetic — Prescription 2026-04",
            document_type="prescription",
            content=(
                "BỆNH VIỆN ĐA KHOA TỔNG HỢP\n"
                "ĐƠN THUỐC\n"
                "Bệnh nhân: Alice Synthetic | MRN: MRN-0001\n"
                "Ngày kê đơn: 28/04/2026 | BS. Dev Doctor\n\n"
                "Danh sách thuốc:\n"
                "- Lisinopril 10 mg, 1 viên/ngày, uống buổi sáng\n"
                "- Metformin 500 mg, 2 lần/ngày (sáng-tối), uống sau ăn\n"
                "- Amlodipine 5 mg, 1 viên/ngày, uống buổi tối\n\n"
                "Chú ý: Tái khám sau 4 tuần. Theo dõi đường huyết mỗi tuần."
            ),
            chunk_meta={
                "medications": [
                    {
                        "name": "Lisinopril",
                        "dose": "10 mg",
                        "route": "PO",
                        "frequency": "1 lần/ngày",
                        "prescriber": "BS. Dev Doctor",
                    },  # noqa: E501
                    {
                        "name": "Metformin",
                        "dose": "500 mg",
                        "route": "PO",
                        "frequency": "2 lần/ngày",
                        "prescriber": "BS. Dev Doctor",
                    },  # noqa: E501
                    {
                        "name": "Amlodipine",
                        "dose": "5 mg",
                        "route": "PO",
                        "frequency": "1 lần/ngày",
                        "prescriber": "BS. Dev Doctor",
                    },  # noqa: E501
                ]
            },
            chunk_uuid=ALICE_CHUNK_PRESC,
            page_uuid=ALICE_PAGE_PRESC,
        )

        ALICE_CHUNK_LAB = uuid.UUID("50000000-0000-0000-0000-000000000002")
        ALICE_PAGE_LAB = uuid.UUID("50000000-0000-0000-0000-000000000012")
        c_alice_lab, d_alice_lab = await _add_document(
            session,
            settings,
            doc_id=DOC_ALICE_LAB_ID,
            patient_id=PATIENT_ALICE_ID,
            uploader_id=admin.id,
            title="Alice Synthetic — Lab Results 2026-04",
            document_type="lab_result",
            content=(
                "KẾT QUẢ XÉT NGHIỆM\n"
                "Bệnh nhân: Alice Synthetic | MRN: MRN-0001\n"
                "Ngày lấy mẫu: 28/04/2026\n\n"
                "Glucose (fasting)       6.2      3.9-6.1 mmol/L\n"
                "HbA1c                   7.4      4.0-5.6 %\n"
                "Creatinine              85       60-110 umol/L\n"
                "eGFR                    72       >60 mL/min\n"
                "ALT                     28       7-56 U/L\n"
                "Cholesterol (total)     5.1      <5.2 mmol/L\n"
                "LDL                     3.2      <3.0 mmol/L\n"
                "HDL                     1.3      >1.0 mmol/L\n"
            ),
            chunk_meta={
                "labs": [
                    {"analyte": "Glucose", "value": "6.2", "reference_range": "3.9-6.1 mmol/L"},
                    {"analyte": "HbA1c", "value": "7.4", "reference_range": "4.0-5.6 %"},
                    {"analyte": "Creatinine", "value": "85", "reference_range": "60-110 umol/L"},
                    {"analyte": "eGFR", "value": "72", "reference_range": ">60 mL/min"},
                    {"analyte": "ALT", "value": "28", "reference_range": "7-56 U/L"},
                    {"analyte": "Cholesterol total", "value": "5.1", "reference_range": "<5.2 mmol/L"},
                    {"analyte": "LDL", "value": "3.2", "reference_range": "<3.0 mmol/L"},
                    {"analyte": "HDL", "value": "1.3", "reference_range": ">1.0 mmol/L"},
                ]
            },
            chunk_uuid=ALICE_CHUNK_LAB,
            page_uuid=ALICE_PAGE_LAB,
        )

        # 4. Bob — Prescription, Labs & Discharge ─────────────────────────────
        BOB_CHUNK_PRESC = uuid.UUID("50000000-0000-0000-0000-000000000003")
        BOB_PAGE_PRESC = uuid.UUID("50000000-0000-0000-0000-000000000013")
        c_bob_presc, d_bob_presc = await _add_document(
            session,
            settings,
            doc_id=DOC_BOB_PRESCRIPTION_ID,
            patient_id=PATIENT_BOB_ID,
            uploader_id=admin.id,
            title="Bob Synthetic — Cardiology Prescription 2026-05",
            document_type="prescription",
            content=(
                "BỆNH VIỆN TIM MẠCH TRUNG ƯƠNG\n"
                "ĐƠN THUỐC TIM MẠCH\n"
                "Bệnh nhân: Bob Synthetic | MRN: MRN-0002\n"
                "Ngày kê đơn: 15/05/2026 | BS. Dev Doctor\n\n"
                "Chẩn đoán: Bệnh động mạch vành (CAD), Tăng huyết áp, Sau mổ CABG\n\n"
                "Danh sách thuốc:\n"
                "- Aspirin 81 mg, 1 viên/ngày, uống buổi sáng sau ăn\n"
                "- Atorvastatin 40 mg, 1 viên/ngày, uống buổi tối trước khi ngủ\n"
                "- Carvedilol 6.25 mg, 2 lần/ngày (sáng-tối), uống sau ăn\n"
                "- Ramipril 5 mg, 1 viên/ngày, uống buổi sáng\n\n"
                "Chú ý: Theo dõi huyết áp hàng ngày. Hẹn siêu âm tim sau 4 tuần."
            ),
            chunk_meta={
                "medications": [
                    {
                        "name": "Aspirin",
                        "dose": "81 mg",
                        "route": "PO",
                        "frequency": "1 lần/ngày",
                        "prescriber": "BS. Dev Doctor",
                    },  # noqa: E501
                    {
                        "name": "Atorvastatin",
                        "dose": "40 mg",
                        "route": "PO",
                        "frequency": "1 lần/ngày",
                        "prescriber": "BS. Dev Doctor",
                    },  # noqa: E501
                    {
                        "name": "Carvedilol",
                        "dose": "6.25 mg",
                        "route": "PO",
                        "frequency": "2 lần/ngày",
                        "prescriber": "BS. Dev Doctor",
                    },  # noqa: E501
                    {
                        "name": "Ramipril",
                        "dose": "5 mg",
                        "route": "PO",
                        "frequency": "1 lần/ngày",
                        "prescriber": "BS. Dev Doctor",
                    },  # noqa: E501
                ]
            },
            chunk_uuid=BOB_CHUNK_PRESC,
            page_uuid=BOB_PAGE_PRESC,
        )

        BOB_CHUNK_LAB = uuid.UUID("50000000-0000-0000-0000-000000000004")
        BOB_PAGE_LAB = uuid.UUID("50000000-0000-0000-0000-000000000014")
        c_bob_lab, d_bob_lab = await _add_document(
            session,
            settings,
            doc_id=DOC_BOB_LAB_ID,
            patient_id=PATIENT_BOB_ID,
            uploader_id=admin.id,
            title="Bob Synthetic — Cardiac Lab Panel 2026-05",
            document_type="lab_result",
            content=(
                "KẾT QUẢ XÉT NGHIỆM TIM MẠCH\n"
                "Bệnh nhân: Bob Synthetic | MRN: MRN-0002\n"
                "Ngày lấy mẫu: 15/05/2026\n\n"
                "Troponin I              0.02     <0.04 ng/mL\n"
                "BNP                     180      <100 pg/mL\n"
                "LDL                     72       <100 mg/dL\n"
                "HDL                     38       >40 mg/dL\n"
                "Triglycerides           148      <150 mg/dL\n"
                "Creatinine              1.1      0.7-1.3 mg/dL\n"
                "eGFR                    65       >60 mL/min\n"
                "HbA1c                   5.8      4.0-5.6 %\n"
                "CRP (high-sensitivity)  3.2      <3.0 mg/L\n"
            ),
            chunk_meta={
                "labs": [
                    {"analyte": "Troponin I", "value": "0.02", "reference_range": "<0.04 ng/mL"},
                    {"analyte": "BNP", "value": "180", "reference_range": "<100 pg/mL"},
                    {"analyte": "LDL", "value": "72", "reference_range": "<100 mg/dL"},
                    {"analyte": "HDL", "value": "38", "reference_range": ">40 mg/dL"},
                    {"analyte": "Triglycerides", "value": "148", "reference_range": "<150 mg/dL"},
                    {"analyte": "Creatinine", "value": "1.1", "reference_range": "0.7-1.3 mg/dL"},
                    {"analyte": "eGFR", "value": "65", "reference_range": ">60 mL/min"},
                    {"analyte": "HbA1c", "value": "5.8", "reference_range": "4.0-5.6 %"},
                    {"analyte": "CRP hs", "value": "3.2", "reference_range": "<3.0 mg/L"},
                ]
            },
            chunk_uuid=BOB_CHUNK_LAB,
            page_uuid=BOB_PAGE_LAB,
        )

        BOB_CHUNK_DISCHARGE = uuid.UUID("50000000-0000-0000-0000-000000000005")
        BOB_PAGE_DISCHARGE = uuid.UUID("50000000-0000-0000-0000-000000000015")
        c_bob_discharge, d_bob_discharge = await _add_document(
            session,
            settings,
            doc_id=DOC_BOB_DISCHARGE_ID,
            patient_id=PATIENT_BOB_ID,
            uploader_id=admin.id,
            title="Bob Synthetic — Discharge Summary Post-CABG 2023",
            document_type="discharge_summary",
            content=(
                "TÓM TẮT XUẤT VIỆN\n"
                "Bệnh nhân: Bob Synthetic | MRN: MRN-0002\n"
                "Ngày nhập viện: 10/03/2023 | Ngày xuất viện: 18/03/2023\n"
                "Chẩn đoán chính: Bệnh động mạch vành 3 nhánh (CAD). "
                "Đã thực hiện phẫu thuật bắc cầu động mạch vành (CABG) x3.\n"
                "Diễn biến: Phẫu thuật thành công. Không có biến chứng lớn sau mổ. "
                "Xuất viện trong tình trạng ổn định.\n"
                "Thuốc kê khi xuất viện: Aspirin 81mg, Atorvastatin 40mg, Carvedilol 6.25mg BID.\n"
                "Dị ứng: Penicillin (phát ban).\n"
                "Theo dõi: Tái khám tim mạch sau 6 tuần, siêu âm tim kiểm tra chức năng thất trái."
            ),
            chunk_meta={
                "medications": [
                    {
                        "name": "Aspirin",
                        "dose": "81 mg",
                        "route": "PO",
                        "frequency": "1 lần/ngày",
                        "prescriber": "BS. Dev Doctor",
                    },  # noqa: E501
                    {
                        "name": "Atorvastatin",
                        "dose": "40 mg",
                        "route": "PO",
                        "frequency": "1 lần/ngày",
                        "prescriber": "BS. Dev Doctor",
                    },  # noqa: E501
                    {
                        "name": "Carvedilol",
                        "dose": "6.25 mg",
                        "route": "PO",
                        "frequency": "BID",
                        "prescriber": "BS. Dev Doctor",
                    },  # noqa: E501
                ],
                "allergies": ["Penicillin (phát ban)"],
                "diagnoses": ["CAD 3-vessel disease", "Post-CABG"],
            },
            chunk_uuid=BOB_CHUNK_DISCHARGE,
            page_uuid=BOB_PAGE_DISCHARGE,
        )

        # 5. Eleanor — Prescription & Labs ───────────────────────────────────
        ELEANOR_CHUNK_PRESC = uuid.UUID("50000000-0000-0000-0000-000000000006")
        ELEANOR_PAGE_PRESC = uuid.UUID("50000000-0000-0000-0000-000000000016")
        c_eleanor_presc, d_eleanor_presc = await _add_document(
            session,
            settings,
            doc_id=DOC_ELEANOR_PRESCRIPTION_ID,
            patient_id=PATIENT_ELEANOR_ID,
            uploader_id=admin.id,
            title="Eleanor Vance — AFib/CKD Prescription 2026-06",
            document_type="prescription",
            content=(
                "BỆNH VIỆN TIM MẠCH\n"
                "ĐƠN THUỐC\n"
                "Bệnh nhân: Eleanor Vance | MRN: MRN-0003\n"
                "Ngày kê đơn: 10/06/2026 | BS. Dev Doctor\n\n"
                "Chẩn đoán: Rung nhĩ (AFib), Bệnh thận mạn giai đoạn 3 (CKD Stage 3)\n\n"
                "Danh sách thuốc:\n"
                "- Apixaban 5 mg, 2 lần/ngày (sáng-tối), uống trong bữa ăn\n"
                "- Metoprolol succinate 50 mg, 1 viên/ngày, uống buổi sáng\n"
                "- Furosemide 40 mg, 1 viên/ngày, uống buổi sáng\n\n"
                "Dị ứng: Sulfa (nổi mề đay)\n"
                "Chú ý: Tránh NSAIDs. Theo dõi chức năng thận định kỳ."
            ),
            chunk_meta={
                "medications": [
                    {
                        "name": "Apixaban",
                        "dose": "5 mg",
                        "route": "PO",
                        "frequency": "2 lần/ngày",
                        "prescriber": "BS. Dev Doctor",
                    },  # noqa: E501
                    {
                        "name": "Metoprolol succinate",
                        "dose": "50 mg",
                        "route": "PO",
                        "frequency": "1 lần/ngày",
                        "prescriber": "BS. Dev Doctor",
                    },  # noqa: E501
                    {
                        "name": "Furosemide",
                        "dose": "40 mg",
                        "route": "PO",
                        "frequency": "1 lần/ngày",
                        "prescriber": "BS. Dev Doctor",
                    },  # noqa: E501
                ],
                "allergies": ["Sulfa (nổi mề đay)"],
            },
            chunk_uuid=ELEANOR_CHUNK_PRESC,
            page_uuid=ELEANOR_PAGE_PRESC,
        )

        ELEANOR_CHUNK_LAB = uuid.UUID("50000000-0000-0000-0000-000000000007")
        ELEANOR_PAGE_LAB = uuid.UUID("50000000-0000-0000-0000-000000000017")
        c_eleanor_lab, d_eleanor_lab = await _add_document(
            session,
            settings,
            doc_id=DOC_ELEANOR_LAB_ID,
            patient_id=PATIENT_ELEANOR_ID,
            uploader_id=admin.id,
            title="Eleanor Vance — Renal & Cardiac Labs 2026-06",
            document_type="lab_result",
            content=(
                "KẾT QUẢ XÉT NGHIỆM\n"
                "Bệnh nhân: Eleanor Vance | MRN: MRN-0003\n"
                "Ngày lấy mẫu: 10/06/2026\n\n"
                "Creatinine              1.6      0.7-1.3 mg/dL\n"
                "eGFR                    42       >60 mL/min\n"
                "BUN                     28       7-25 mg/dL\n"
                "BNP                     420      <100 pg/mL\n"
                "INR                     1.0      0.8-1.2\n"
                "Potassium               4.3      3.5-5.0 mEq/L\n"
                "Sodium                  138      135-145 mEq/L\n"
                "Hemoglobin              11.2     12.0-16.0 g/dL\n"
                "Platelets               210      150-400 x10³/uL\n"
            ),
            chunk_meta={
                "labs": [
                    {"analyte": "Creatinine", "value": "1.6", "reference_range": "0.7-1.3 mg/dL"},
                    {"analyte": "eGFR", "value": "42", "reference_range": ">60 mL/min"},
                    {"analyte": "BUN", "value": "28", "reference_range": "7-25 mg/dL"},
                    {"analyte": "BNP", "value": "420", "reference_range": "<100 pg/mL"},
                    {"analyte": "INR", "value": "1.0", "reference_range": "0.8-1.2"},
                    {"analyte": "Potassium", "value": "4.3", "reference_range": "3.5-5.0 mEq/L"},
                    {"analyte": "Sodium", "value": "138", "reference_range": "135-145 mEq/L"},
                    {"analyte": "Hemoglobin", "value": "11.2", "reference_range": "12.0-16.0 g/dL"},
                    {"analyte": "Platelets", "value": "210", "reference_range": "150-400 x10³/uL"},
                ]
            },
            chunk_uuid=ELEANOR_CHUNK_LAB,
            page_uuid=ELEANOR_PAGE_LAB,
        )

        await session.flush()

        # 6. Graph Entities & Relations ───────────────────────────────────────
        # Alice entities
        E_ALICE_LISINOPRIL = uuid.UUID("60000000-0000-0000-0000-000000000001")
        E_ALICE_METFORMIN = uuid.UUID("60000000-0000-0000-0000-000000000002")
        E_ALICE_AMLODIPINE = uuid.UUID("60000000-0000-0000-0000-000000000003")
        E_ALICE_DIABETES = uuid.UUID("60000000-0000-0000-0000-000000000004")
        E_ALICE_HYPERTENSION = uuid.UUID("60000000-0000-0000-0000-000000000005")
        E_ALICE_HBA1C = uuid.UUID("60000000-0000-0000-0000-000000000006")

        for eid, name, etype in [
            (E_ALICE_LISINOPRIL, "Lisinopril", "drug"),
            (E_ALICE_METFORMIN, "Metformin", "drug"),
            (E_ALICE_AMLODIPINE, "Amlodipine", "drug"),
            (E_ALICE_DIABETES, "Type 2 Diabetes Mellitus", "condition"),
            (E_ALICE_HYPERTENSION, "Hypertension", "condition"),
            (E_ALICE_HBA1C, "HbA1c 7.4%", "lab"),
        ]:
            await _add_graph_entity(session, eid, name, etype, c_alice_presc, d_alice_presc)

        for rid, src, tgt, rel in [
            (uuid.UUID("70000000-0000-0000-0000-000000000001"), E_ALICE_LISINOPRIL, E_ALICE_HYPERTENSION, "treats"),
            (uuid.UUID("70000000-0000-0000-0000-000000000002"), E_ALICE_METFORMIN, E_ALICE_DIABETES, "treats"),
            (uuid.UUID("70000000-0000-0000-0000-000000000003"), E_ALICE_AMLODIPINE, E_ALICE_HYPERTENSION, "treats"),
            (uuid.UUID("70000000-0000-0000-0000-000000000004"), E_ALICE_DIABETES, E_ALICE_HBA1C, "indicated_by"),
        ]:
            await _add_graph_relation(session, rid, src, tgt, rel, c_alice_presc)

        # Bob entities
        E_BOB_ASPIRIN = uuid.UUID("60000000-0000-0000-0000-000000000011")
        E_BOB_ATORVASTATIN = uuid.UUID("60000000-0000-0000-0000-000000000012")
        E_BOB_CARVEDILOL = uuid.UUID("60000000-0000-0000-0000-000000000013")
        E_BOB_RAMIPRIL = uuid.UUID("60000000-0000-0000-0000-000000000014")
        E_BOB_CAD = uuid.UUID("60000000-0000-0000-0000-000000000015")
        E_BOB_CABG = uuid.UUID("60000000-0000-0000-0000-000000000016")
        E_BOB_BNP = uuid.UUID("60000000-0000-0000-0000-000000000017")
        E_BOB_LDL = uuid.UUID("60000000-0000-0000-0000-000000000018")

        for eid, name, etype in [
            (E_BOB_ASPIRIN, "Aspirin", "drug"),
            (E_BOB_ATORVASTATIN, "Atorvastatin", "drug"),
            (E_BOB_CARVEDILOL, "Carvedilol", "drug"),
            (E_BOB_RAMIPRIL, "Ramipril", "drug"),
            (E_BOB_CAD, "Coronary Artery Disease (CAD)", "condition"),
            (E_BOB_CABG, "CABG Procedure", "encounter"),
            (E_BOB_BNP, "BNP 180 pg/mL", "lab"),
            (E_BOB_LDL, "LDL 72 mg/dL", "lab"),
        ]:
            await _add_graph_entity(session, eid, name, etype, c_bob_presc, d_bob_presc)

        for rid, src, tgt, rel in [
            (uuid.UUID("70000000-0000-0000-0000-000000000011"), E_BOB_ASPIRIN, E_BOB_CAD, "treats"),
            (uuid.UUID("70000000-0000-0000-0000-000000000012"), E_BOB_ATORVASTATIN, E_BOB_CAD, "treats"),
            (uuid.UUID("70000000-0000-0000-0000-000000000013"), E_BOB_CARVEDILOL, E_BOB_CAD, "treats"),
            (uuid.UUID("70000000-0000-0000-0000-000000000014"), E_BOB_CAD, E_BOB_CABG, "treated_by_procedure"),
            (uuid.UUID("70000000-0000-0000-0000-000000000015"), E_BOB_RAMIPRIL, E_BOB_CAD, "treats"),
            (uuid.UUID("70000000-0000-0000-0000-000000000016"), E_BOB_CAD, E_BOB_BNP, "indicated_by"),
            (uuid.UUID("70000000-0000-0000-0000-000000000017"), E_BOB_ATORVASTATIN, E_BOB_LDL, "reduces"),
        ]:
            await _add_graph_relation(session, rid, src, tgt, rel, c_bob_presc)

        # Eleanor entities
        E_ELEANOR_APIXABAN = uuid.UUID("60000000-0000-0000-0000-000000000021")
        E_ELEANOR_METOPROLOL = uuid.UUID("60000000-0000-0000-0000-000000000022")
        E_ELEANOR_FUROSEMIDE = uuid.UUID("60000000-0000-0000-0000-000000000023")
        E_ELEANOR_AFIB = uuid.UUID("60000000-0000-0000-0000-000000000024")
        E_ELEANOR_CKD = uuid.UUID("60000000-0000-0000-0000-000000000025")
        E_ELEANOR_CREATININE = uuid.UUID("60000000-0000-0000-0000-000000000026")
        E_ELEANOR_BNP = uuid.UUID("60000000-0000-0000-0000-000000000027")
        E_ELEANOR_SULFA_ALLERGY = uuid.UUID("60000000-0000-0000-0000-000000000028")
        E_ELEANOR_EFGR = uuid.UUID("60000000-0000-0000-0000-000000000029")

        for eid, name, etype, cid, did in [
            (E_ELEANOR_APIXABAN, "Apixaban 5mg BID", "drug", c_eleanor_presc, d_eleanor_presc),
            (E_ELEANOR_METOPROLOL, "Metoprolol succinate 50mg", "drug", c_eleanor_presc, d_eleanor_presc),
            (E_ELEANOR_FUROSEMIDE, "Furosemide 40mg", "drug", c_eleanor_presc, d_eleanor_presc),
            (E_ELEANOR_AFIB, "Atrial Fibrillation (AFib)", "condition", c_eleanor_presc, d_eleanor_presc),
            (E_ELEANOR_CKD, "CKD Stage 3", "condition", c_eleanor_presc, d_eleanor_presc),
            (E_ELEANOR_CREATININE, "Creatinine 1.6 mg/dL", "lab", c_eleanor_lab, d_eleanor_lab),
            (E_ELEANOR_BNP, "BNP 420 pg/mL", "lab", c_eleanor_lab, d_eleanor_lab),
            (E_ELEANOR_SULFA_ALLERGY, "Sulfa allergy (hives)", "condition", c_eleanor_presc, d_eleanor_presc),
            (E_ELEANOR_EFGR, "eGFR 42 mL/min", "lab", c_eleanor_lab, d_eleanor_lab),
        ]:
            await _add_graph_entity(session, eid, name, etype, cid, did)

        for rid, src, tgt, rel in [
            (uuid.UUID("70000000-0000-0000-0000-000000000021"), E_ELEANOR_APIXABAN, E_ELEANOR_AFIB, "treats"),
            (uuid.UUID("70000000-0000-0000-0000-000000000022"), E_ELEANOR_METOPROLOL, E_ELEANOR_AFIB, "rate_controls"),
            (uuid.UUID("70000000-0000-0000-0000-000000000023"), E_ELEANOR_FUROSEMIDE, E_ELEANOR_CKD, "monitors"),
            (uuid.UUID("70000000-0000-0000-0000-000000000024"), E_ELEANOR_CKD, E_ELEANOR_CREATININE, "indicated_by"),
            (uuid.UUID("70000000-0000-0000-0000-000000000025"), E_ELEANOR_AFIB, E_ELEANOR_BNP, "indicated_by"),
            (uuid.UUID("70000000-0000-0000-0000-000000000026"), E_ELEANOR_CKD, E_ELEANOR_EFGR, "indicated_by"),
            (uuid.UUID("70000000-0000-0000-0000-000000000027"), E_ELEANOR_APIXABAN, E_ELEANOR_CKD, "dose_adjusted_for"),
            (uuid.UUID("70000000-0000-0000-0000-000000000028"), E_ELEANOR_SULFA_ALLERGY, E_ELEANOR_AFIB, "complicates"),
        ]:
            await _add_graph_relation(session, rid, src, tgt, rel, c_eleanor_presc)

        # 7. Seed access requests for development
        #   - ar-001 (approved request for Alice MRN-0001 from Pharmacist Riya Patel)
        #   - ar-002 (pending request for Eleanor MRN-0003 from Pharmacist Riya Patel)
        ar_001_id = uuid.UUID("90000000-0000-0000-0000-000000000001")
        ar_002_id = uuid.UUID("90000000-0000-0000-0000-000000000002")

        from sqlalchemy import select

        ar_001_exists = (
            await session.execute(select(AccessRequest).where(AccessRequest.id == ar_001_id))
        ).scalar_one_or_none()  # noqa: E501
        if not ar_001_exists:
            session.add(
                AccessRequest(
                    id=ar_001_id,
                    patient_id=PATIENT_ALICE_ID,
                    user_id=_PHARMACIST_ID,
                    justification="Need to review Alice's medication list for pharmacy safety checks.",
                    status="approved",
                    reviewed_by_user_id=ADMIN_ID,
                    reviewed_at=datetime.now(UTC) - timedelta(hours=2.5),
                    review_notes="Approved for pharmacy review.",
                    created_at=datetime.now(UTC) - timedelta(hours=3),
                )
            )

        ar_002_exists = (
            await session.execute(select(AccessRequest).where(AccessRequest.id == ar_002_id))
        ).scalar_one_or_none()  # noqa: E501
        if not ar_002_exists:
            session.add(
                AccessRequest(
                    id=ar_002_id,
                    patient_id=PATIENT_ELEANOR_ID,
                    user_id=_PHARMACIST_ID,
                    justification="Justification for reviewing Eleanor Vance's cardiology documents.",
                    status="pending",
                    created_at=datetime.now(UTC) - timedelta(hours=1),
                )
            )

        from hospital_ai.db.models import ChatThread

        # Seed a DAPT conversation for E2E testing
        thread = await session.execute(select(ChatThread).where(ChatThread.title == "DAPT Guideline Query"))
        if thread.scalar_one_or_none() is None:
            session.add(
                ChatThread(
                    title="DAPT Guideline Query",
                    scope="general",
                    visibility="private",
                    status="active",
                    owner_user_id=DOCTOR_ID,
                    created_trace_id="seed_dev_trace",
                    last_message_at=datetime.now(UTC),
                )
            )
            await session.commit()

        # Seed Graph RAG relations for Eleanor Vance (MRN-0003)
        eleanor_doc_id = uuid.UUID("77777777-0000-0000-0000-000000000003")
        existing_doc = await session.get(Document, eleanor_doc_id)
        if existing_doc is None:
            eleanor_doc = Document(
                id=eleanor_doc_id,
                patient_id=PATIENT_ELEANOR_ID,
                title="Cardiology Consultation & Management Note",
                document_type="clinical_note",
                storage_uri="local://mock-clinical-note-eleanor",
                mime_type="text/plain",
                status="ready",
                uploaded_by=DOCTOR_ID,
            )
            session.add(eleanor_doc)

            page_id = uuid.UUID("77777777-0000-0000-0000-000000000004")
            page = DocumentPage(
                id=page_id,
                document_id=eleanor_doc_id,
                page_number=1,
                ocr_text=(
                    "Eleanor Vance is a 74yo female with persistent Atrial Fibrillation on Apixaban. "
                    "Also diagnosed with Chronic Kidney Disease Stage 3 with baseline eGFR 58 mL/min "
                    "indicated by elevated Creatinine. "
                    "Apixaban treats Atrial Fibrillation. Elevated Creatinine indicates Chronic Kidney Disease."
                ),
                ocr_confidence=1.0,
            )
            session.add(page)

            chunk_id = uuid.UUID("77777777-0000-0000-0000-000000000005")
            chunk = DocumentChunk(
                id=chunk_id,
                document_id=eleanor_doc_id,
                page_id=page_id,
                patient_id=PATIENT_ELEANOR_ID,
                content=page.ocr_text,
                chunk_index=0,
            )
            session.add(chunk)
            await session.flush()

            # Entities
            ent_afib = GraphEntity(
                id=uuid.UUID("77777777-0000-0000-0000-000000000010"),
                name="Atrial Fibrillation",
                entity_type="condition",
                source_chunk_id=chunk_id,
                source_document_id=eleanor_doc_id,
                confidence=1.0,
            )
            ent_apixaban = GraphEntity(
                id=uuid.UUID("77777777-0000-0000-0000-000000000011"),
                name="Apixaban",
                entity_type="drug",
                source_chunk_id=chunk_id,
                source_document_id=eleanor_doc_id,
                confidence=1.0,
            )
            ent_ckd = GraphEntity(
                id=uuid.UUID("77777777-0000-0000-0000-000000000012"),
                name="Chronic Kidney Disease",
                entity_type="condition",
                source_chunk_id=chunk_id,
                source_document_id=eleanor_doc_id,
                confidence=1.0,
            )
            ent_creat = GraphEntity(
                id=uuid.UUID("77777777-0000-0000-0000-000000000013"),
                name="Creatinine",
                entity_type="lab",
                source_chunk_id=chunk_id,
                source_document_id=eleanor_doc_id,
                confidence=1.0,
            )
            ent_egfr = GraphEntity(
                id=uuid.UUID("77777777-0000-0000-0000-000000000014"),
                name="eGFR",
                entity_type="lab",
                source_chunk_id=chunk_id,
                source_document_id=eleanor_doc_id,
                confidence=1.0,
            )
            session.add_all([ent_afib, ent_apixaban, ent_ckd, ent_creat, ent_egfr])
            await session.flush()

            # Relations
            rel_1 = GraphRelation(
                id=uuid.UUID("77777777-0000-0000-0000-000000000020"),
                source_entity_id=ent_apixaban.id,
                target_entity_id=ent_afib.id,
                relation_type="treats",
                weight=1.0,
                source_chunk_id=chunk_id,
            )
            rel_2 = GraphRelation(
                id=uuid.UUID("77777777-0000-0000-0000-000000000021"),
                source_entity_id=ent_creat.id,
                target_entity_id=ent_ckd.id,
                relation_type="indicates",
                weight=1.0,
                source_chunk_id=chunk_id,
            )
            rel_3 = GraphRelation(
                id=uuid.UUID("77777777-0000-0000-0000-000000000022"),
                source_entity_id=ent_egfr.id,
                target_entity_id=ent_ckd.id,
                relation_type="indicates",
                weight=1.0,
                source_chunk_id=chunk_id,
            )
            session.add_all([rel_1, rel_2, rel_3])
            await session.commit()

    print("Seeded synthetic users, patients, permissions, HMS appointment evidence, ChatThreads, and Graph RAG data.")


if __name__ == "__main__":
    asyncio.run(main())
