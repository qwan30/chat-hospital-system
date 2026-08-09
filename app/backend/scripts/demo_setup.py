"""Demo setup script for the Hospital Knowledge Assistant.

Creates a complete demo environment with:
- Users (admin, doctor, nurse, security)
- Patients with synthetic data
- Sample documents with embeddings
- Patient permissions
- Sample audit log entries

Usage:
    python -m scripts.demo_setup

Requires:
    HOSPITAL_AI_DATABASE_URL environment variable set (or uses .env).
"""

from typing import Optional
import asyncio
import hashlib
import math
import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from hospital_ai.core.config import Settings
from hospital_ai.db.models import (
    AuditLog,
    Base,
    Document,
    DocumentChunk,
    DocumentPage,
    Patient,
    PatientPermission,
    User,
)


def deterministic_embedding(text_content: str, dimensions: int = 1024) -> list[float]:
    """Create a deterministic embedding for demo data."""
    vector = [0.0] * dimensions
    words = text_content.lower().split()
    if not words:
        return vector
    for word in words:
        digest = hashlib.sha256(word.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0:
        return vector
    return [v / norm for v in vector]


# ── Demo Data ─────────────────────────────────────────────────────────

DEMO_USERS = [
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "email": "admin@hospital.local",
        "full_name": "Alice Admin",
        "role": "admin",
        "department": "IT",
        "is_active": True,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
        "email": "doctor@hospital.local",
        "full_name": "Dr. Bob Smith",
        "role": "doctor",
        "department": "Cardiology",
        "is_active": True,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000003"),
        "email": "nurse@hospital.local",
        "full_name": "Carol Nurse",
        "role": "nurse",
        "department": "Emergency",
        "is_active": True,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000004"),
        "email": "security@hospital.local",
        "full_name": "Dave Security",
        "role": "security",
        "department": "Compliance",
        "is_active": True,
    },
]

DEMO_PATIENTS = [
    {
        "id": uuid.UUID("10000000-0000-0000-0000-000000000001"),
        "mrn": "MRN-2024-0001",
        "full_name": "John Doe",
        "dob": date(1958, 3, 15),
        "department": "Cardiology",
    },
    {
        "id": uuid.UUID("10000000-0000-0000-0000-000000000002"),
        "mrn": "MRN-2024-0002",
        "full_name": "Jane Roe",
        "dob": date(1975, 11, 22),
        "department": "Neurology",
    },
    {
        "id": uuid.UUID("10000000-0000-0000-0000-000000000003"),
        "mrn": "MRN-2024-0003",
        "full_name": "Sam Wilson",
        "dob": date(1990, 7, 8),
        "department": "Emergency",
    },
]

DEMO_DOCUMENTS = [
    {
        "patient_index": 0,
        "user_index": 1,
        "title": "CBC Lab Report - March 2025",
        "document_type": "lab_report",
        "content": (
            "Complete Blood Count (CBC) Results\n"
            "Patient: John Doe  MRN: MRN-2024-0001\n"
            "Date: March 15, 2025\n\n"
            "WBC: 7,500 cells/uL (Normal: 4,500-11,000)\n"
            "RBC: 4.8 million/uL (Normal: 4.5-5.5)\n"
            "Hemoglobin: 14.2 g/dL (Normal: 13.5-17.5)\n"
            "Hematocrit: 42% (Normal: 38-50%)\n"
            "Platelets: 250,000/uL (Normal: 150,000-400,000)\n\n"
            "All values within normal limits. No abnormalities detected."
        ),
    },
    {
        "patient_index": 0,
        "user_index": 1,
        "title": "Cardiology Encounter Note",
        "document_type": "encounter_note",
        "content": (
            "Cardiology Follow-up Note\n"
            "Patient: John Doe  MRN: MRN-2024-0001\n"
            "Attending: Dr. Bob Smith\n"
            "Date: March 20, 2025\n\n"
            "Chief Complaint: Routine follow-up for hypertension.\n"
            "Blood Pressure: 138/85 mmHg (slightly elevated)\n"
            "Heart Rate: 72 bpm regular\n\n"
            "Assessment: Essential hypertension, controlled. Continue current medications.\n"
            "Medications: Lisinopril 10mg daily, Aspirin 81mg daily.\n"
            "Plan: Continue current regimen. Follow-up in 3 months. "
            "Consider increasing Lisinopril if BP remains above 140/90."
        ),
    },
    {
        "patient_index": 1,
        "user_index": 1,
        "title": "Neurology MRI Report",
        "document_type": "imaging_report",
        "content": (
            "MRI Brain Report\n"
            "Patient: Jane Roe  MRN: MRN-2024-0002\n"
            "Date: April 5, 2025\n\n"
            "Technique: MRI Brain with and without contrast.\n"
            "Findings: No acute intracranial abnormality. Normal brain parenchyma.\n"
            "No midline shift. Ventricles are normal in size.\n"
            "No evidence of mass, hemorrhage, or infarction.\n\n"
            "Impression: Normal MRI of the brain."
        ),
    },
    {
        "patient_index": 2,
        "user_index": 2,
        "title": "Emergency Triage Assessment",
        "document_type": "triage_note",
        "content": (
            "Emergency Department Triage\n"
            "Patient: Sam Wilson  MRN: MRN-2024-0003\n"
            "Date: April 10, 2025\n\n"
            "Presenting Complaint: Acute abdominal pain, right lower quadrant.\n"
            "Duration: 6 hours, worsening.\n"
            "Vitals: BP 120/78, HR 88, Temp 37.8°C, SpO2 98%\n"
            "Triage Level: ESI-3 (Urgent)\n\n"
            "Assessment: Rule out appendicitis. CT abdomen ordered.\n"
            "Labs: CBC, CMP, UA ordered."
        ),
    },
]


DEMO_AUDIT_ENTRIES = [
    {"action": "login", "object_type": "session", "outcome": "allowed", "user_index": 0},
    {
        "action": "query_patient_data",
        "object_type": "patient",
        "outcome": "allowed",
        "user_index": 1,
        "patient_index": 0,
    },
    {"action": "view_document", "object_type": "document", "outcome": "allowed", "user_index": 1, "patient_index": 0},
    {"action": "upload_document", "object_type": "document", "outcome": "allowed", "user_index": 2, "patient_index": 2},
    {
        "action": "query_patient_data",
        "object_type": "patient",
        "outcome": "denied",
        "user_index": 2,
        "patient_index": 1,
    },
    {"action": "export_audit_log", "object_type": "audit", "outcome": "allowed", "user_index": 0},
]


async def setup_demo(settings: Optional[Settings] = None) -> None:
    """Seed the database with demo data."""
    if settings is None:
        settings = Settings()

    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]

    async with engine.begin() as conn:
        # Create schema if PostgreSQL
        if "postgresql" in settings.database_url:
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS hospital_ai"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        now = datetime.now(UTC)

        # ── Users ──
        users: list[User] = []
        for u in DEMO_USERS:
            user = User(**u, created_at=now, updated_at=now)
            session.add(user)
            users.append(user)
        await session.flush()
        print(f"  ✓ Created {len(users)} users")

        # ── Patients ──
        patients: list[Patient] = []
        for p in DEMO_PATIENTS:
            patient = Patient(**p, created_at=now, updated_at=now)
            session.add(patient)
            patients.append(patient)
        await session.flush()
        print(f"  ✓ Created {len(patients)} patients")

        # ── Permissions ──
        # Doctor has access to all patients
        for patient in patients:
            perm = PatientPermission(
                id=uuid.uuid4(),
                user_id=users[1].id,  # doctor
                patient_id=patient.id,
                scope="read",
                source="manual",
                created_at=now,
                updated_at=now,
            )
            session.add(perm)

        # Nurse has access to Emergency patient only
        perm = PatientPermission(
            id=uuid.uuid4(),
            user_id=users[2].id,  # nurse
            patient_id=patients[2].id,  # Sam Wilson (Emergency)
            scope="read",
            source="manual",
            created_at=now,
            updated_at=now,
        )
        session.add(perm)
        await session.flush()
        print("  ✓ Created patient permissions")

        # ── Documents with Chunks ──
        for d in DEMO_DOCUMENTS:
            patient = patients[d["patient_index"]]
            uploader = users[d["user_index"]]

            doc = Document(
                id=uuid.uuid4(),
                patient_id=patient.id,
                uploaded_by=uploader.id,
                title=d["title"],
                document_type=d["document_type"],
                storage_uri=f"local://demo/{uuid.uuid4().hex}.txt",
                mime_type="text/plain",
                status="ready",
                page_count=1,
                indexed_source_sha256=hashlib.sha256(d["content"].encode()).hexdigest(),
                index_generation=1,
                created_at=now,
                updated_at=now,
            )
            session.add(doc)
            await session.flush()

            # Create a page for the document
            page = DocumentPage(
                id=uuid.uuid4(),
                document_id=doc.id,
                page_number=1,
                ocr_text=d["content"],
                created_at=now,
                updated_at=now,
            )
            session.add(page)
            await session.flush()

            # Create a single chunk with embedding
            embedding = deterministic_embedding(d["content"])
            chunk = DocumentChunk(
                id=uuid.uuid4(),
                document_id=doc.id,
                page_id=page.id,
                patient_id=patient.id,
                chunk_index=1,
                content=d["content"],
                embedding=embedding,
                meta={
                    "source_system": "demo-seed",
                    "document_type": d["document_type"],
                },
                created_at=now,
                updated_at=now,
            )
            session.add(chunk)

        await session.flush()
        print(f"  ✓ Created {len(DEMO_DOCUMENTS)} documents with embeddings")

        # ── Audit Logs ──
        for i, entry in enumerate(DEMO_AUDIT_ENTRIES):
            audit = AuditLog(
                id=uuid.uuid4(),
                actor_user_id=users[entry["user_index"]].id,
                action=entry["action"],
                object_type=entry["object_type"],
                object_id=patients[entry["patient_index"]].id if "patient_index" in entry else None,
                patient_id=patients[entry["patient_index"]].id if "patient_index" in entry else None,
                outcome=entry["outcome"],
                trace_id=f"demo-trace-{uuid.uuid4().hex[:8]}",
                created_at=now - timedelta(hours=len(DEMO_AUDIT_ENTRIES) - i),
            )
            session.add(audit)

        await session.flush()
        print(f"  ✓ Created {len(DEMO_AUDIT_ENTRIES)} audit log entries")

        await session.commit()

    await engine.dispose()
    print("\n✅ Demo setup complete!")
    print("\nDev bearer tokens:")
    print("  dev-admin    → Alice Admin (admin, IT)")
    print("  dev-doctor   → Dr. Bob Smith (doctor, Cardiology)")
    print("  dev-nurse    → Carol Nurse (nurse, Emergency)")
    print("  dev-security → Dave Security (security, Compliance)")


if __name__ == "__main__":
    print("🏥 Hospital Knowledge Assistant — Demo Setup")
    print("=" * 50)
    asyncio.run(setup_demo())
