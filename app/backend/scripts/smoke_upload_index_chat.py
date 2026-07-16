import asyncio

from hospital_ai.core.config import get_settings
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, RECORDS_ID, seed_synthetic_data
from hospital_ai.db.models import Document, User
from hospital_ai.db.session import get_session_factory
from hospital_ai.services.chat import ChatService
from hospital_ai.workers.jobs import process_document


async def main() -> None:
    settings = get_settings()
    session_factory = get_session_factory()
    async with session_factory() as session:
        await seed_synthetic_data(session)

        storage_dir = settings.storage_root / "smoke"
        storage_dir.mkdir(parents=True, exist_ok=True)
        source = storage_dir / "smoke-note.txt"
        source.write_text("Alice Synthetic has a documented allergy to penicillin.", encoding="utf-8")

        document = Document(
            patient_id=PATIENT_ALICE_ID,
            uploaded_by=RECORDS_ID,
            title="Smoke clinical note",
            document_type="clinical_note",
            storage_uri=str(source),
            mime_type="text/plain",
            status="uploaded",
        )
        session.add(document)
        await session.commit()

        await process_document(session, document.id, settings)
        doctor = await session.get(User, DOCTOR_ID)
        response = await ChatService(session, settings).answer(
            user=doctor,
            patient_id=PATIENT_ALICE_ID,
            question="What allergy is documented?",
            top_k=5,
            trace_id="local-smoke",
            ip_address="127.0.0.1",
        )
        print(response.json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
