from __future__ import annotations

import pytest
from starlette.requests import Request

from hospital_ai.api.routes.search import global_search
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID
from hospital_ai.db.models import ChatThread, ChatThreadParticipant, Document, User


def _request(q: str = None) -> Request:
    path = "/api/v1/search/global"
    if q:
        path += f"?q={q}"
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": [],
            "client": ("testclient", 50000),
        }
    )


@pytest.mark.asyncio
async def test_global_search_empty_query(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    response = await global_search(
        request=_request(),
        q=None,
        session=session,
        current_user=doctor,
    )
    assert response.patients == []
    assert response.documents == []
    assert response.threads == []


@pytest.mark.asyncio
async def test_global_search_patient_permissions(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    # Search "Alice" (authorized patient)
    response = await global_search(
        request=_request("Alice"),
        q="Alice",
        session=session,
        current_user=doctor,
    )
    assert len(response.patients) > 0
    assert any(p.id == PATIENT_ALICE_ID for p in response.patients)

    # Search "Bob" (unauthorized patient)
    response_bob = await global_search(
        request=_request("Bob"),
        q="Bob",
        session=session,
        current_user=doctor,
    )
    # Bob should not be returned because doctor lacks active treatment relationship
    assert not any(p.id == PATIENT_BOB_ID for p in response_bob.patients)


@pytest.mark.asyncio
async def test_global_search_documents_and_threads(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    # Create dummy document for Alice
    doc = Document(
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice Clinical Report 2026",
        document_type="hms_medical_record",
        storage_uri="hms://medical_records/123",
        mime_type="text/plain",
        status="ready",
    )
    session.add(doc)

    # Create chat thread for Alice
    thread = ChatThread(
        title="Reviewing Alice progress",
        scope="patient-linked",
        visibility="private",
        status="active",
        owner_user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        created_trace_id="test-trace",
    )
    session.add(thread)
    await session.flush()

    session.add(
        ChatThreadParticipant(
            thread_id=thread.id,
            user_id=DOCTOR_ID,
            access_level="owner",
            can_share=True,
            added_by_user_id=DOCTOR_ID,
            created_trace_id="test-trace",
        )
    )
    await session.commit()

    # Search "Alice"
    response = await global_search(
        request=_request("Alice"),
        q="Alice",
        session=session,
        current_user=doctor,
    )

    # Should match document and thread
    assert any(d.id == doc.id for d in response.documents)
    assert any(t.id == thread.id for t in response.threads)
