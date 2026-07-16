"""Seed script — creates synthetic users, patients, permissions, and sample documents.

Usage:
    python -m scripts.seed_data
    # or from the backend directory:
    python scripts/seed_data.py
"""

import asyncio
import hashlib
import math
import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Re-use the existing seed helpers and extend them with documents.
from hospital_ai.core.config import get_settings
from hospital_ai.db.models import (
    Base,
    ChatMessage,
    ChatThread,
    Document,
    DocumentChunk,
    DocumentPage,
    Patient,
    PatientPermission,
    User,
)

# ── Stable IDs ─────────────────────────────────────────────────────

DOCTOR_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
RECORDS_ID = uuid.UUID("10000000-0000-0000-0000-000000000002")
SECURITY_ID = uuid.UUID("10000000-0000-0000-0000-000000000003")
ADMIN_ID = uuid.UUID("10000000-0000-0000-0000-000000000004")
NURSE_ID = uuid.UUID("10000000-0000-0000-0000-000000000005")

PATIENT_ALICE_ID = uuid.UUID("20000000-0000-0000-0000-000000000001")
PATIENT_BOB_ID = uuid.UUID("20000000-0000-0000-0000-000000000002")
PATIENT_CAROL_ID = uuid.UUID("20000000-0000-0000-0000-000000000003")
PATIENT_DAN_ID = uuid.UUID("20000000-0000-0000-0000-000000000004")
PATIENT_EVE_ID = uuid.UUID("20000000-0000-0000-0000-000000000005")

DOC_ALICE_SUMMARY = uuid.UUID("30000000-0000-0000-0000-000000000001")
DOC_ALICE_LAB = uuid.UUID("30000000-0000-0000-0000-000000000002")
DOC_BOB_DISCHARGE = uuid.UUID("30000000-0000-0000-0000-000000000003")

THREAD_DOCTOR_ALICE = uuid.UUID("40000000-0000-0000-0000-000000000001")


def det_embed(text: str, dims: int = 1024) -> list[float]:
    """Deterministic embedding — same as EmbeddingService.deterministic."""
    vector = [0.0] * dims
    for word in text.lower().split():
        digest = hashlib.sha256(word.encode()).digest()
        idx = int.from_bytes(digest[:4], "big") % dims
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[idx] += sign
    norm = math.sqrt(sum(v * v for v in vector))
    return [v / norm for v in vector] if norm else vector


async def seed(session: AsyncSession) -> None:
    # ── Users ──────────────────────────────────────────────────────
    users = [
        User(
            id=DOCTOR_ID,
            email="doctor@example.test",
            full_name="Dr. Dev Doctor",
            department="Internal Medicine",
            role="doctor",
        ),
        User(
            id=RECORDS_ID,
            email="records@example.test",
            full_name="Riley Records",
            department="Medical Records",
            role="records_staff",
        ),
        User(
            id=SECURITY_ID,
            email="security@example.test",
            full_name="Sam Security",
            department="Compliance",
            role="security",
        ),
        User(id=ADMIN_ID, email="admin@example.test", full_name="Alex Admin", department="IT", role="admin"),
        User(
            id=NURSE_ID,
            email="nurse@example.test",
            full_name="Nancy Nurse",
            department="Internal Medicine",
            role="nurse",
        ),
    ]

    # ── Patients ───────────────────────────────────────────────────
    patients = [
        Patient(
            id=PATIENT_ALICE_ID,
            mrn="MRN-0001",
            full_name="Alice Synthetic",
            dob=date(1978, 5, 17),
            department="Internal Medicine",
        ),
        Patient(
            id=PATIENT_BOB_ID, mrn="MRN-0002", full_name="Bob Synthetic", dob=date(1969, 9, 9), department="Cardiology"
        ),
        Patient(
            id=PATIENT_CAROL_ID,
            mrn="MRN-0003",
            full_name="Carol Synthetic",
            dob=date(1985, 3, 22),
            department="Neurology",
        ),
        Patient(
            id=PATIENT_DAN_ID,
            mrn="MRN-0004",
            full_name="Dan Synthetic",
            dob=date(1992, 11, 1),
            department="Orthopedics",
        ),
        Patient(
            id=PATIENT_EVE_ID, mrn="MRN-0005", full_name="Eve Synthetic", dob=date(2000, 7, 14), department="Pediatrics"
        ),
    ]

    # ── Permissions ────────────────────────────────────────────────
    permissions = [
        # Doctor has read/summary access to Alice and Bob
        PatientPermission(user_id=DOCTOR_ID, patient_id=PATIENT_ALICE_ID, scope="read"),
        PatientPermission(user_id=DOCTOR_ID, patient_id=PATIENT_ALICE_ID, scope="summary"),
        PatientPermission(user_id=DOCTOR_ID, patient_id=PATIENT_ALICE_ID, scope="medication"),
        PatientPermission(user_id=DOCTOR_ID, patient_id=PATIENT_BOB_ID, scope="read"),
        PatientPermission(user_id=DOCTOR_ID, patient_id=PATIENT_BOB_ID, scope="summary"),
        # Records staff can upload for Alice
        PatientPermission(user_id=RECORDS_ID, patient_id=PATIENT_ALICE_ID, scope="upload"),
        PatientPermission(user_id=RECORDS_ID, patient_id=PATIENT_BOB_ID, scope="upload"),
        # Admin has full access
        PatientPermission(user_id=ADMIN_ID, patient_id=PATIENT_ALICE_ID, scope="admin"),
        PatientPermission(user_id=ADMIN_ID, patient_id=PATIENT_BOB_ID, scope="admin"),
        # Nurse has read for Alice
        PatientPermission(user_id=NURSE_ID, patient_id=PATIENT_ALICE_ID, scope="read"),
    ]

    for user in users:
        existing = await session.get(User, user.id)
        if not existing:
            session.add(user)
    for patient in patients:
        existing = await session.get(Patient, patient.id)
        if not existing:
            session.add(patient)
    await session.flush()
    for perm in permissions:
        session.add(perm)
    await session.flush()

    # ── Sample documents ───────────────────────────────────────────
    alice_summary_content = (
        "Patient Alice Synthetic (MRN-0001) is a 47-year-old female presenting with "
        "hypertension and type 2 diabetes. Current medications include Metformin 500mg BID "
        "and Lisinopril 10mg daily. Last HbA1c was 7.2% (target <7.0%). Blood pressure "
        "readings average 138/88 mmHg. No known drug allergies. BMI 28.4."
    )
    alice_lab_content = (
        "Lab Results for Alice Synthetic (MRN-0001)\n"
        "Date: 2026-04-15\n"
        "HbA1c: 7.2% (reference: <7.0%)\n"
        "Fasting glucose: 142 mg/dL (reference: 70-100 mg/dL)\n"
        "Total cholesterol: 218 mg/dL (reference: <200 mg/dL)\n"
        "LDL: 132 mg/dL (reference: <100 mg/dL)\n"
        "HDL: 48 mg/dL (reference: >40 mg/dL)\n"
        "Creatinine: 0.9 mg/dL (reference: 0.6-1.2 mg/dL)\n"
        "eGFR: 92 mL/min (reference: >60 mL/min)"
    )
    bob_discharge_content = (
        "Discharge Summary for Bob Synthetic (MRN-0002)\n"
        "Admission: 2026-04-10. Discharge: 2026-04-14.\n"
        "Diagnosis: Acute anterior STEMI.\n"
        "Procedure: Primary PCI to LAD with drug-eluting stent.\n"
        "Medications at discharge: Aspirin 81mg, Clopidogrel 75mg, "
        "Atorvastatin 80mg, Metoprolol 25mg BID, Lisinopril 5mg.\n"
        "Follow-up: Cardiology in 2 weeks. Cardiac rehab referral placed."
    )

    sample_docs = [
        (
            DOC_ALICE_SUMMARY,
            PATIENT_ALICE_ID,
            "Alice Synthetic — Clinical Summary",
            "clinical_summary",
            alice_summary_content,
        ),
        (DOC_ALICE_LAB, PATIENT_ALICE_ID, "Alice Synthetic — Lab Results Apr 2026", "lab_result", alice_lab_content),
        (
            DOC_BOB_DISCHARGE,
            PATIENT_BOB_ID,
            "Bob Synthetic — Discharge Summary",
            "discharge_summary",
            bob_discharge_content,
        ),
    ]

    for doc_id, patient_id, title, doc_type, content in sample_docs:
        existing = await session.get(Document, doc_id)
        if existing:
            continue
        doc = Document(
            id=doc_id,
            patient_id=patient_id,
            uploaded_by=RECORDS_ID,
            title=title,
            document_type=doc_type,
            storage_uri=f"seed://{doc_id}",
            mime_type="text/plain",
            status="indexed",
            page_count=1,
            indexed_source_sha256=hashlib.sha256(content.encode()).hexdigest(),
            index_generation=1,
        )
        session.add(doc)
        await session.flush()

        page = DocumentPage(document_id=doc_id, page_number=1, ocr_text=content, ocr_confidence=1.0)
        session.add(page)
        await session.flush()

        session.add(
            DocumentChunk(
                document_id=doc_id,
                page_id=page.id,
                patient_id=patient_id,
                chunk_index=0,
                content=content,
                token_count=len(content.split()),
                embedding=det_embed(content),
                meta={"source": "seed", "contains_phi": True, "patient_permission_required": True},
            )
        )

    # ── Sample chat thread ─────────────────────────────────────────
    existing_thread = await session.get(ChatThread, THREAD_DOCTOR_ALICE)
    if not existing_thread:
        thread = ChatThread(
            id=THREAD_DOCTOR_ALICE,
            owner_id=DOCTOR_ID,
            patient_id=PATIENT_ALICE_ID,
            title="Alice — medication review",
        )
        session.add(thread)
        await session.flush()

        session.add(
            ChatMessage(
                thread_id=THREAD_DOCTOR_ALICE,
                sender_user_id=DOCTOR_ID,
                role="user",
                content="What medications is Alice currently taking?",
            )
        )
        session.add(
            ChatMessage(
                thread_id=THREAD_DOCTOR_ALICE,
                sender_user_id=None,
                role="assistant",
                content=(
                    "Based on the clinical summary [E1], Alice Synthetic is currently prescribed:\n"
                    "- Metformin 500mg twice daily (for type 2 diabetes)\n"
                    "- Lisinopril 10mg once daily (for hypertension)\n\n"
                    "No known drug allergies are documented.\n\n"
                    "AI-assisted retrieval; clinical staff must verify before making decisions."
                ),
            )
        )

    await session.commit()
    print("✅ Seed data created successfully.")
    print(f"   Users: {len(users)}")
    print(f"   Patients: {len(patients)}")
    print(f"   Permissions: {len(permissions)}")
    print(f"   Documents: {len(sample_docs)}")
    print("   Chat threads: 1")


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)

    # Create tables if they don't exist (for local dev without Alembic).
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await seed(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
