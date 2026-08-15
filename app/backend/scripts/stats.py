import asyncio
import json

from sqlalchemy import func, select

from hospital_ai.core.config import get_settings
from hospital_ai.db.models import Document, Patient
from hospital_ai.db.session import create_async_engine


async def main():
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.connect() as conn:
        # 1. OCR ingested documents
        ocr_docs = await conn.scalar(select(func.count(Document.id)).where(Document.status == "ocr_completed"))

        # 2. Patient documents
        patient_docs = await conn.scalar(select(func.count(Document.id)))

        # 3. Patients
        patients = await conn.scalar(select(func.count(Patient.id)))

        print(json.dumps({"ocr_completed_docs": ocr_docs, "total_documents": patient_docs, "total_patients": patients}))


if __name__ == "__main__":
    asyncio.run(main())
