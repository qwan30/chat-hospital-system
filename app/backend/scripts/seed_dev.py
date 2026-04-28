import asyncio
import uuid
from datetime import date

from hospital_ai.core.config import get_settings
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.migrations import ADMIN_ID, PATIENT_ALICE_ID
from hospital_ai.db.migrations import seed_synthetic_data
from hospital_ai.db.models import User
from hospital_ai.db.session import get_session_factory
from hospital_ai.schemas.hms import HmsAppointmentSummaryImport
from hospital_ai.services.hms_appointments import HmsAppointmentEvidenceImporter

SYNTHETIC_APPOINTMENT_ID = uuid.UUID("30000000-0000-0000-0000-000000000001")


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
            ip_address="seed_dev",
        )
    print("Seeded synthetic users, patients, permissions, and HMS appointment evidence.")


if __name__ == "__main__":
    asyncio.run(main())
