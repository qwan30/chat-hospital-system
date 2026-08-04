"""Seed deterministic synthetic clinical notes for local Graph RAG development."""

import asyncio
import uuid
from datetime import datetime

from sqlalchemy import delete, or_

from hospital_ai.db.migrations import DOCTOR_ID
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage, Patient, User
from hospital_ai.db.session import get_session_factory
from hospital_ai.services.graph_rag import GraphEntity, GraphRelation

MOCK_CLINICAL_NOTES = [
    {
        "subject_id": "10001",
        "category": "Discharge summary",
        "description": "Synthetic Graph RAG fixture",
        "text": (
            "Patient is a 65-year-old male presenting with severe chest pain and "
            "shortness of breath. Diagnosed with acute myocardial infarction. The patient "
            "was prescribed Aspirin and Metoprolol which treats the infarction. Patient "
            "also has a history of Type 2 Diabetes Mellitus, which causes peripheral "
            "neuropathy. Metoprolol contraindicates severe asthma, but patient has no "
            "history of asthma. Patient reported a headache as a side effect "
            "(has_symptom) of the medication."
        ),
        "entities": [
            {"name": "acute myocardial infarction", "type": "condition"},
            {"name": "aspirin", "type": "drug"},
            {"name": "metoprolol", "type": "drug"},
            {"name": "type 2 diabetes mellitus", "type": "condition"},
            {"name": "peripheral neuropathy", "type": "condition"},
            {"name": "severe asthma", "type": "condition"},
            {"name": "headache", "type": "symptom"},
        ],
        "relations": [
            ("metoprolol", "acute myocardial infarction", "treats"),
            ("type 2 diabetes mellitus", "peripheral neuropathy", "causes"),
            ("metoprolol", "severe asthma", "contraindicates"),
            ("metoprolol", "headache", "has_symptom"),
        ],
    },
    {
        "subject_id": "10002",
        "category": "Progress Note",
        "description": "Synthetic Graph RAG fixture",
        "text": (
            "Female patient, 42 years old. Complains of persistent joint pain and morning "
            "stiffness. Rheumatoid arthritis is the primary diagnosis. Prescribed "
            "Methotrexate. Methotrexate treats rheumatoid arthritis. Methotrexate causes "
            "nausea. Patient also takes Ibuprofen which treats joint pain. Patient "
            "has_symptom fatigue."
        ),
        "entities": [
            {"name": "rheumatoid arthritis", "type": "condition"},
            {"name": "methotrexate", "type": "drug"},
            {"name": "nausea", "type": "symptom"},
            {"name": "ibuprofen", "type": "drug"},
            {"name": "joint pain", "type": "symptom"},
            {"name": "fatigue", "type": "symptom"},
        ],
        "relations": [
            ("methotrexate", "rheumatoid arthritis", "treats"),
            ("methotrexate", "nausea", "causes"),
            ("ibuprofen", "joint pain", "treats"),
            ("ibuprofen", "fatigue", "has_symptom"),
        ],
    },
]


async def main() -> None:
    session_factory = get_session_factory()

    async with session_factory() as session:
        doctor = await session.get(User, DOCTOR_ID)
        if not doctor:
            print("Doctor user not found. Run seed_dev.py first.")
            return

        print("Clearing old synthetic Graph RAG patients...")
        await session.execute(
            delete(Patient).where(
                or_(Patient.mrn.like("MOCK-%"), Patient.mrn.like("MIMIC-%"))
            )
        )
        await session.commit()

        print("Seeding deterministic synthetic clinical notes for Graph RAG development...")

        for note in MOCK_CLINICAL_NOTES:
            patient_id = uuid.uuid4()
            patient = Patient(
                id=patient_id,
                full_name=f"Mock Patient_{note['subject_id']}",
                dob=datetime(1970, 1, 1).date(),
                mrn=f"MOCK-{note['subject_id']}",
                department="Cardiology",
                status="active",
            )
            session.add(patient)
            await session.flush()

            doc_id = uuid.uuid4()
            doc = Document(
                id=doc_id,
                patient_id=patient_id,
                title=f"{note['category']} - {note['description']}",
                document_type="clinical_note",
                storage_uri="local://mock-clinical-note",
                mime_type="text/plain",
                status="indexed",
                uploaded_by=DOCTOR_ID,
            )
            session.add(doc)

            page_id = uuid.uuid4()
            page = DocumentPage(
                id=page_id,
                document_id=doc_id,
                page_number=1,
                ocr_text=note["text"],
                ocr_confidence=1.0,
            )
            session.add(page)

            chunk = DocumentChunk(
                id=uuid.uuid4(),
                document_id=doc_id,
                page_id=page_id,
                patient_id=patient_id,
                content=note["text"],
                chunk_index=0,
            )
            session.add(chunk)
            await session.flush()

            entity_rows = {}
            for entity in note["entities"]:
                row = GraphEntity(
                    name=entity["name"],
                    entity_type=entity["type"],
                    source_chunk_id=chunk.id,
                    source_document_id=doc.id,
                    confidence=1.0,
                )
                session.add(row)
                entity_rows[entity["name"]] = row

            await session.flush()

            for source, target, relation in note["relations"]:
                source_row = entity_rows.get(source)
                target_row = entity_rows.get(target)
                if source_row and target_row:
                    session.add(
                        GraphRelation(
                            source_entity_id=source_row.id,
                            target_entity_id=target_row.id,
                            relation_type=relation,
                            weight=1.0,
                            source_chunk_id=chunk.id,
                        )
                    )

            print(
                " -> Seeded "
                f"{len(note['entities'])} entities and {len(note['relations'])} relations "
                f"for mock patient {note['subject_id']}."
            )

        await session.commit()
        print("Successfully seeded synthetic Graph RAG clinical-note fixtures.")


if __name__ == "__main__":
    asyncio.run(main())
