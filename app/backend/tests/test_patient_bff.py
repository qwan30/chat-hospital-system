import uuid
from unittest.mock import patch

import pytest
from starlette.requests import Request

from hospital_ai.api.routes.hms import sync_patient
from hospital_ai.api.routes.patients import get_patient_overview, get_patient_timeline
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID, RECORDS_ID
from hospital_ai.db.models import User
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
        assert response.medication_count >= 1
        assert response.ai_summary is not None
        assert "AI summary response" in response.ai_summary


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
