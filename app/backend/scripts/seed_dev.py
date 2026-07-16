import asyncio
import uuid
from datetime import date

from hospital_ai.core.config import get_settings
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.migrations import ADMIN_ID, PATIENT_ALICE_ID, PATIENT_ELEANOR_ID, seed_synthetic_data
from hospital_ai.db.models import User
from hospital_ai.db.session import get_session_factory
from hospital_ai.schemas.hms import HmsAppointmentSummaryImport
from hospital_ai.services.hms_appointments import HmsAppointmentEvidenceImporter

SYNTHETIC_APPOINTMENT_ID = uuid.UUID("30000000-0000-0000-0000-000000000001")
SYNTHETIC_APPOINTMENT_ID_ELEANOR = uuid.UUID("30000000-0000-0000-0000-000000000002")


async def main() -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        await seed_synthetic_data(session)
        admin = await session.get(User, ADMIN_ID)
        await HmsAppointmentEvidenceImporter(session, get_settings()).import_summary(
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
                reason="Synthetic follow-up visit",
                symptoms="Synthetic dizziness and medication review notes.",
                vital_signs_summary="Blood pressure 128/78, heart rate 78, oxygen saturation 98%.",
                follow_up_summary="Review symptoms and medication reconciliation at discharge planning.",
            ),
            trace_id=new_trace_id(),
            ip_address="127.0.0.1",
        )
        await HmsAppointmentEvidenceImporter(session, get_settings()).import_summary(
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
                symptoms="Patient reports occasional palpitations. Denies shortness of breath. History of AFib, CKD stage 3.",
                vital_signs_summary="Blood pressure 135/85, heart rate 88 (irregular), oxygen 97%.",
                follow_up_summary="Continue Apixaban. Renal labs: Creatinine 1.6, eGFR 42. Note: Sulfa allergy (hives).",
            ),
            trace_id=new_trace_id(),
            ip_address="127.0.0.1",
        )

        import datetime

        from sqlalchemy import select

        from hospital_ai.db.migrations import DOCTOR_ID, HOSPITAL_PUBLIC_ID
        from hospital_ai.db.models import ChatThread, Document, DocumentChunk, DocumentPage

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
                    last_message_at=datetime.datetime.now(datetime.UTC),
                )
            )
            await session.commit()

        # Seed synthetic medical guidelines
        guidelines = [
            ("Sepsis Guidelines", "Sepsis treatment protocol: Administer broad-spectrum antibiotics within 1 hour. Start IV fluids 30mL/kg for hypotension or lactate >= 4 mmol/L."),
            ("DAPT Protocol", "Dual Antiplatelet Therapy (DAPT) Protocol: Aspirin 81mg daily plus Clopidogrel 75mg daily for 12 months post-DES placement."),
            ("Diabetes Management", "Inpatient Diabetes Management: Target blood glucose 140-180 mg/dL. Use basal-bolus insulin regimen. Avoid sliding scale insulin alone.")
        ]

        for i, (title, content) in enumerate(guidelines):
            doc_exists = await session.execute(select(Document).where(Document.title == title))
            if doc_exists.scalar_one_or_none() is None:
                doc = Document(
                    patient_id=HOSPITAL_PUBLIC_ID,
                    uploaded_by=ADMIN_ID,
                    title=title,
                    document_type="guideline",
                    storage_uri=f"local://guideline_{i}",
                    mime_type="text/plain",
                    status="indexed",
                    page_count=1,
                    index_generation=1,
                )
                session.add(doc)
                await session.flush()

                page = DocumentPage(
                    document_id=doc.id,
                    page_number=1,
                    ocr_text=content,
                    ocr_confidence=1.0,
                )
                session.add(page)
                await session.flush()

                chunk = DocumentChunk(
                    document_id=doc.id,
                    page_id=page.id,
                    patient_id=HOSPITAL_PUBLIC_ID,
                    chunk_index=0,
                    content=content,
                    token_count=len(content.split()),
                )
                session.add(chunk)
        await session.commit()

    print("Seeded synthetic users, patients, permissions, HMS appointment evidence, and ChatThreads.")


if __name__ == "__main__":
    asyncio.run(main())
