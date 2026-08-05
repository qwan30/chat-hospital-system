from __future__ import annotations
import uuid

import pytest

from hospital_ai.db.migrations import DOCTOR_ID
from hospital_ai.db.models import Document, Patient, User
from hospital_ai.services.graph_query import GraphFilters, GraphQueryService


@pytest.fixture
async def graph_fixture(session_and_settings):
    session, _ = session_and_settings

    patient_id = uuid.uuid4()
    patient = Patient(id=patient_id, full_name="Test", mrn="MRN")
    session.add(patient)

    doc = Document(
        id=uuid.uuid4(),
        patient_id=patient_id,
        title="Doc",
        uploaded_by=DOCTOR_ID,
        mime_type="text/plain",
        storage_uri="mem",
        status="ready",
        document_type="clinical_note",
    )
    session.add(doc)
    await session.flush()

    class GraphData:
        pass

    data = GraphData()
    data.patient_id = patient_id
    data.document = doc
    data.session = session

    return data


@pytest.mark.asyncio
async def test_document_graph_filters_each_source_by_its_own_active_generation(graph_fixture) -> None:
    session = graph_fixture.session
    doctor = await session.get(User, DOCTOR_ID)
    filters = GraphFilters(hop_depth=2, min_confidence=0.8)

    body = await GraphQueryService(session).document_graph(graph_fixture.document, doctor, filters)

    assert all(item["generation_id"] == item["source_active_generation_id"] for item in body.mentions)
    assert all(item["evidence_ids"] for item in body.assertions)


@pytest.mark.asyncio
async def test_superseded_graph_requires_capability(graph_fixture) -> None:
    session = graph_fixture.session
    doctor = await session.get(User, DOCTOR_ID)
    filters = GraphFilters(include_superseded=True)

    from hospital_ai.core.errors import PermissionDeniedError

    with pytest.raises(PermissionDeniedError) as exc:
        # In a real app we would call the route
        from hospital_ai.api.routes.document_graph import get_document_graph

        await get_document_graph(graph_fixture.document.id, filters, session, doctor)
    assert "missing capability" in str(exc.value)
