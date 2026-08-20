from __future__ import annotations

import pytest

from hospital_ai.api.routes.timeline import get_global_timeline
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, RECORDS_ID
from hospital_ai.db.models import ChatThread, Document, User


@pytest.mark.asyncio
async def test_get_global_timeline_with_events(session_and_settings):
    session, settings = session_and_settings
    current_user = await session.get(User, DOCTOR_ID)

    doc = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=RECORDS_ID,
        title="Discharge Summary Note",
        document_type="clinical_note",
        storage_uri="mock/path/discharge.pdf",
        mime_type="application/pdf",
        status="ready",
    )
    session.add(doc)

    thread = ChatThread(
        patient_id=PATIENT_ALICE_ID,
        created_by_user_id=DOCTOR_ID,
        title="Consultation regarding hypertension",
        scope="patient-linked",
    )
    session.add(thread)
    await session.commit()

    response = await get_global_timeline(
        limit=50,
        offset=0,
        db=session,
        current_user=current_user,
    )

    assert response is not None
    assert response.total_count >= 2
    types = [e.type for e in response.events]
    assert "document" in types
    assert "chat" in types

    doc_event = next(e for e in response.events if e.type == "document")
    assert "Discharge Summary Note" in doc_event.body
