"""Tests for HMS synchronization service."""

import uuid
from typing import Tuple
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings
from hospital_ai.db.models import Document, DocumentChunk, Patient, User
from hospital_ai.services.hms_sync import HmsSyncService


SAMPLE_APPOINTMENTS = [
    {
        "id": 101,
        "date": "2025-03-15",
        "status": "completed",
        "department": "Cardiology",
        "doctorName": "Dr. Smith",
        "reason": "Routine checkup",
        "notes": "Patient stable.",
    },
    {
        "id": 102,
        "date": "2025-04-20",
        "status": "scheduled",
        "department": "Neurology",
        "doctorName": "Dr. Jones",
        "reason": "Follow-up",
    },
]

SAMPLE_LAB_RESULTS = [
    {
        "id": 201,
        "testName": "CBC",
        "date": "2025-03-16",
        "result": "Normal",
        "unit": "cells/uL",
        "referenceRange": "4500-11000",
        "status": "final",
    },
]

SAMPLE_MEDICAL_RECORDS = [
    {
        "id": 301,
        "date": "2025-03-15",
        "type": "encounter",
        "diagnosis": "Hypertension",
        "diagnosisCode": "I10",
        "treatment": "Lisinopril 10mg daily",
        "doctor": "Dr. Smith",
    },
]


@pytest.fixture
def trace_id() -> str:
    return f"test-trace-{uuid.uuid4().hex[:8]}"


@pytest.mark.asyncio
async def test_sync_appointments_creates_documents(
    session_and_settings: Tuple[AsyncSession, Settings],
    trace_id: str,
) -> None:
    session, settings = session_and_settings

    # Get first patient and user
    patient = (await session.execute(select(Patient).limit(1))).scalar_one()
    user = (await session.execute(select(User).limit(1))).scalar_one()

    service = HmsSyncService(session, settings)

    with patch.object(service.hms, "get_appointments", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = SAMPLE_APPOINTMENTS

        docs = await service.sync_appointments(
            patient_id=patient.id,
            actor_user_id=user.id,
            trace_id=trace_id,
        )

    assert len(docs) == 2
    for doc in docs:
        assert doc.patient_id == patient.id
        assert doc.document_type == "hms_appointment"
        assert doc.status == "indexed"
        assert doc.page_count == 1


@pytest.mark.asyncio
async def test_sync_lab_results_creates_documents(
    session_and_settings: Tuple[AsyncSession, Settings],
    trace_id: str,
) -> None:
    session, settings = session_and_settings
    patient = (await session.execute(select(Patient).limit(1))).scalar_one()
    user = (await session.execute(select(User).limit(1))).scalar_one()

    service = HmsSyncService(session, settings)

    with patch.object(service.hms, "get_lab_results", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = SAMPLE_LAB_RESULTS

        docs = await service.sync_lab_results(
            patient_id=patient.id,
            actor_user_id=user.id,
            trace_id=trace_id,
        )

    assert len(docs) == 1
    assert docs[0].document_type == "hms_lab_result"
    assert docs[0].status == "indexed"


@pytest.mark.asyncio
async def test_sync_medical_records_creates_documents(
    session_and_settings: Tuple[AsyncSession, Settings],
    trace_id: str,
) -> None:
    session, settings = session_and_settings
    patient = (await session.execute(select(Patient).limit(1))).scalar_one()
    user = (await session.execute(select(User).limit(1))).scalar_one()

    service = HmsSyncService(session, settings)

    with patch.object(service.hms, "get_medical_records", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = SAMPLE_MEDICAL_RECORDS

        docs = await service.sync_medical_records(
            patient_id=patient.id,
            actor_user_id=user.id,
            trace_id=trace_id,
        )

    assert len(docs) == 1
    assert docs[0].document_type == "hms_medical_record"
    assert docs[0].status == "indexed"


@pytest.mark.asyncio
async def test_sync_full_runs_all_sync_types(
    session_and_settings: Tuple[AsyncSession, Settings],
    trace_id: str,
) -> None:
    session, settings = session_and_settings
    patient = (await session.execute(select(Patient).limit(1))).scalar_one()
    user = (await session.execute(select(User).limit(1))).scalar_one()

    service = HmsSyncService(session, settings)

    with (
        patch.object(service.hms, "get_appointments", new_callable=AsyncMock) as mock_appts,
        patch.object(service.hms, "get_lab_results", new_callable=AsyncMock) as mock_labs,
        patch.object(service.hms, "get_medical_records", new_callable=AsyncMock) as mock_records,
    ):
        mock_appts.return_value = SAMPLE_APPOINTMENTS
        mock_labs.return_value = SAMPLE_LAB_RESULTS
        mock_records.return_value = SAMPLE_MEDICAL_RECORDS

        result = await service.sync_full(
            patient_id=patient.id,
            actor_user_id=user.id,
            trace_id=trace_id,
        )

    assert result["appointments"] == 2
    assert result["lab_results"] == 1
    assert result["medical_records"] == 1
    assert result["total"] == 4


@pytest.mark.asyncio
async def test_sync_creates_searchable_chunks(
    session_and_settings: Tuple[AsyncSession, Settings],
    trace_id: str,
) -> None:
    """Verify that synced documents have embedded chunks with content."""
    session, settings = session_and_settings
    patient = (await session.execute(select(Patient).limit(1))).scalar_one()
    user = (await session.execute(select(User).limit(1))).scalar_one()

    service = HmsSyncService(session, settings)

    with patch.object(service.hms, "get_appointments", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [SAMPLE_APPOINTMENTS[0]]

        docs = await service.sync_appointments(
            patient_id=patient.id,
            actor_user_id=user.id,
            trace_id=trace_id,
        )

    doc = docs[0]
    chunks = (
        await session.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
        )
    ).scalars().all()

    assert len(chunks) >= 1
    chunk = chunks[0]
    assert "Cardiology" in chunk.content
    assert chunk.embedding is not None
    assert len(chunk.embedding) > 0
    assert chunk.meta.get("source_system") == "hospital-management-system"


@pytest.mark.asyncio
async def test_sync_skip_unchanged_content(
    session_and_settings: Tuple[AsyncSession, Settings],
    trace_id: str,
) -> None:
    """Second sync with same content should not re-index."""
    session, settings = session_and_settings
    patient = (await session.execute(select(Patient).limit(1))).scalar_one()
    user = (await session.execute(select(User).limit(1))).scalar_one()

    service = HmsSyncService(session, settings)

    with patch.object(service.hms, "get_appointments", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [SAMPLE_APPOINTMENTS[0]]

        # First sync
        docs1 = await service.sync_appointments(
            patient_id=patient.id,
            actor_user_id=user.id,
            trace_id=trace_id,
        )
        gen1 = docs1[0].index_generation

        # Second sync with same data
        docs2 = await service.sync_appointments(
            patient_id=patient.id,
            actor_user_id=user.id,
            trace_id=trace_id,
        )
        gen2 = docs2[0].index_generation

    # Generation should NOT increase since content hash matches
    assert gen2 == gen1


@pytest.mark.asyncio
async def test_sync_nonexistent_patient_raises(
    session_and_settings: Tuple[AsyncSession, Settings],
    trace_id: str,
) -> None:
    session, settings = session_and_settings
    user = (await session.execute(select(User).limit(1))).scalar_one()

    service = HmsSyncService(session, settings)

    from hospital_ai.core.errors import NotFoundError

    with pytest.raises(NotFoundError):
        await service.sync_appointments(
            patient_id=uuid.uuid4(),
            actor_user_id=user.id,
            trace_id=trace_id,
        )
