from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import select
from starlette.requests import Request

from hospital_ai.api.routes.hms import sync_patient
from hospital_ai.api.routes.patients import (
    get_patient_labs,
    get_patient_medications,
    get_patient_overview,
    get_patient_timeline,
)
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID, RECORDS_ID
from hospital_ai.db.models import DocumentChunk, User
from hospital_ai.services.hms_connector import HmsApiClient
from tests.conftest import create_indexed_document


def _request(method: str = "GET", path: str = "/") -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [],
            "client": ("testclient", 50000),
        }
    )


@pytest.mark.asyncio
async def test_patient_overview_unauthorized(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    # Bob is unauthorized for Doctor
    with pytest.raises(PermissionDeniedError):
        await get_patient_overview(
            patient_id=PATIENT_BOB_ID,
            request=_request(path=f"/api/v1/patients/{PATIENT_BOB_ID}/overview"),
            session=session,
            current_user=doctor,
        )


@pytest.mark.asyncio
async def test_patient_overview_healthy_hms(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    # Settings: enable HMS integration
    settings.hms_sync_enabled = True

    mock_snapshot = {
        "dob": "1990-05-15",
        "gender": "Female",
        "cccd": "987654321",
        "blood_type": "AB-",
        "occupation": "Teacher",
        "allergies": [{"allergen": "Dust"}],
        "currentMedications": [{"drug": "Aspirin"}],
        "recentLabs": [{"test": "CBC"}],
    }

    with patch.object(HmsApiClient, "get_patient_snapshot", return_value=mock_snapshot) as mock_get:
        response = await get_patient_overview(
            patient_id=PATIENT_ALICE_ID,
            request=_request(path=f"/api/v1/patients/{PATIENT_ALICE_ID}/overview"),
            session=session,
            current_user=doctor,
            settings=settings,
        )

        mock_get.assert_called_once_with(str(PATIENT_ALICE_ID))
        assert response.dob.strftime("%Y-%m-%d") == "1990-05-15"
        assert response.gender == "Female"
        assert response.cccd == "987654321"
        assert response.blood_type == "AB-"
        assert response.occupation == "Teacher"
        assert response.allergy_count == 1
        assert response.medication_count == 1
        assert response.lab_count == 1


@pytest.mark.asyncio
async def test_patient_overview_fallback_and_summary_pipeline(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    # Settings: disable HMS sync to trigger local read-model fallback
    settings.hms_sync_enabled = False

    # Create dummy indexed document & chunk to trigger summary pipeline
    doc = await create_indexed_document(
        session=session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice Clinical Notes",
        content="Patient has allergy to penicillin. Diagnosed with mild hypertension.",
    )
    doc.document_type = "hms_medical_record"
    await session.commit()

    with patch("hospital_ai.services.chat_utils.ChatGenerator.generate", return_value="AI summary response [E1]"):
        response = await get_patient_overview(
            patient_id=PATIENT_ALICE_ID,
            request=_request(path=f"/api/v1/patients/{PATIENT_ALICE_ID}/overview"),
            session=session,
            current_user=doctor,
            settings=settings,
        )

        assert response.gender == "Unknown"
        assert response.cccd == "0123456789"
        assert response.blood_type == "O+"
        assert response.ai_summary is not None
        assert "AI summary response" in response.ai_summary


@pytest.mark.asyncio
async def test_patient_overview_fallback_medication_count_matches_medication_tab(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    settings.hms_sync_enabled = False

    prescription = await create_indexed_document(
        session=session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Active Prescription",
        content="Continue antihypertensive therapy.",
    )
    prescription.document_type = "prescription"
    prescription_chunk = (
        await session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == prescription.id))
    ).one()
    prescription_chunk.meta = {
        "medications": [
            {"name": "Lisinopril", "dose": "10mg daily"},
            {"drug": "Metformin", "dose": "500mg BID"},
        ]
    }

    discharge_summary = await create_indexed_document(
        session=session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Discharge Summary",
        content="Discharge medication list",
    )
    discharge_summary.document_type = "discharge_summary"
    discharge_chunk = (
        await session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == discharge_summary.id))
    ).one()
    discharge_chunk.meta = {"medications": [{"name": "Aspirin", "dose": "81mg daily"}]}
    await session.commit()

    with patch("hospital_ai.services.chat_utils.ChatGenerator.generate", return_value="AI summary response [E1]"):
        overview = await get_patient_overview(
            patient_id=PATIENT_ALICE_ID,
            request=_request(path=f"/api/v1/patients/{PATIENT_ALICE_ID}/overview"),
            session=session,
            current_user=doctor,
            settings=settings,
        )

    medications = await get_patient_medications(
        patient_id=PATIENT_ALICE_ID,
        request=_request(path=f"/api/v1/patients/{PATIENT_ALICE_ID}/medications"),
        session=session,
        current_user=doctor,
    )

    assert {item.drug_name for item in medications.medications} == {"Aspirin", "Lisinopril", "Metformin"}
    assert len(medications.medications) == 3
    assert overview.medication_count == len(medications.medications)


@pytest.mark.asyncio
async def test_patient_overview_fallback_lab_count_matches_lab_tab(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    settings.hms_sync_enabled = False

    structured_labs = await create_indexed_document(
        session=session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Structured Labs",
        content="Structured lab metadata",
    )
    structured_labs.document_type = "lab_result"
    structured_chunk = (
        await session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == structured_labs.id))
    ).one()
    structured_chunk.meta = {
        "labs": [
            {"analyte": "Glucose", "value": "180", "reference_range": "70-110"},
            {"analyte": "Sodium", "value": "135", "reference_range": "136-145"},
        ]
    }

    text_labs = await create_indexed_document(
        session=session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Text Labs",
        content="Follow-up lab observations",
    )
    text_labs.document_type = "hms_lab_result"
    text_chunk = await session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == text_labs.id))
    text_chunk.one().meta = {
        "labs": [
            {"analyte": "Glucose", "value": "180", "reference_range": "70-110"},
            {"analyte": "Hemoglobin", "value": "11", "reference_range": "12-16"},
        ]
    }
    await session.commit()

    with patch("hospital_ai.services.chat_utils.ChatGenerator.generate", return_value="AI summary response [E1]"):
        overview = await get_patient_overview(
            patient_id=PATIENT_ALICE_ID,
            request=_request(path=f"/api/v1/patients/{PATIENT_ALICE_ID}/overview"),
            session=session,
            current_user=doctor,
            settings=settings,
        )

    labs = await get_patient_labs(
        patient_id=PATIENT_ALICE_ID,
        request=_request(path=f"/api/v1/patients/{PATIENT_ALICE_ID}/labs"),
        session=session,
        current_user=doctor,
    )

    assert {(item.analyte, item.flag) for item in labs.labs} == {
        ("Glucose", "H"),
        ("Sodium", "L"),
        ("Hemoglobin", "L"),
    }
    assert len(labs.labs) == 3
    assert overview.lab_count == len(labs.labs)


@pytest.mark.asyncio
async def test_patient_timeline_hms_and_fallback(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    settings.hms_sync_enabled = True

    mock_hms_timeline = [
        {
            "eventId": str(uuid.uuid4()),
            "eventType": "appointment",
            "title": "Clinical Consult",
            "description": "Routine checkup",
            "timestamp": "2026-06-01T10:00:00Z",
        }
    ]

    with patch.object(HmsApiClient, "get_patient_timeline", return_value=mock_hms_timeline):
        response = await get_patient_timeline(
            patient_id=PATIENT_ALICE_ID,
            request=_request(path=f"/api/v1/patients/{PATIENT_ALICE_ID}/timeline"),
            session=session,
            current_user=doctor,
            settings=settings,
        )
        assert len(response.events) == 1
        assert response.events[0].title == "Clinical Consult"

    # Create local document for fallback path
    await create_indexed_document(
        session=session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice Clinic Report",
        content="Alice visit on 2026-06-02. Follow-up clinic report notes.",
    )

    # Test local fallback if HMS fails
    with patch.object(HmsApiClient, "get_patient_timeline", side_effect=Exception("HMS Down")):
        response_fallback = await get_patient_timeline(
            patient_id=PATIENT_ALICE_ID,
            request=_request(path=f"/api/v1/patients/{PATIENT_ALICE_ID}/timeline"),
            session=session,
            current_user=doctor,
            settings=settings,
        )
        # Should return local documents as timeline events
        assert len(response_fallback.events) >= 1
        assert "Notes" in response_fallback.events[0].title or "Report" in response_fallback.events[0].title


@pytest.mark.asyncio
async def test_patient_sync_permissions_and_healthy_flow(session_and_settings):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    records_user = await session.get(User, RECORDS_ID)

    # Doctor (not records staff/admin) should get PermissionDeniedError
    with pytest.raises(PermissionDeniedError):
        await sync_patient(
            patient_id=PATIENT_ALICE_ID,
            request=_request(method="POST", path=f"/api/v1/hms/sync/patients/{PATIENT_ALICE_ID}"),
            session=session,
            current_user=doctor,
            settings=settings,
        )

    # Records user is authorized
    mock_sync_result = {"appointments": 1, "lab_results": 2, "medical_records": 1, "total": 4}
    with patch("hospital_ai.services.hms_sync.HmsSyncService.sync_full", return_value=mock_sync_result) as mock_sync:
        res = await sync_patient(
            patient_id=PATIENT_ALICE_ID,
            request=_request(method="POST", path=f"/api/v1/hms/sync/patients/{PATIENT_ALICE_ID}"),
            session=session,
            current_user=records_user,
            settings=settings,
        )

        mock_sync.assert_called_once()
        assert res.synced["total"] == 4
        assert "completed" in res.message.lower()

    # Records user triggers failing sync (HMS offline fallback)
    with patch("hospital_ai.services.hms_sync.HmsSyncService.sync_full", side_effect=Exception("Timeout")):
        res_fail = await sync_patient(
            patient_id=PATIENT_ALICE_ID,
            request=_request(method="POST", path=f"/api/v1/hms/sync/patients/{PATIENT_ALICE_ID}"),
            session=session,
            current_user=records_user,
            settings=settings,
        )

        assert res_fail.synced["total"] == 0
        assert "failed" in res_fail.message.lower()
