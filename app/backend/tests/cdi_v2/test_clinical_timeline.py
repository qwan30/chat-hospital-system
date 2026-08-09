from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from hospital_ai.api.routes.document_graph import get_document_timeline
from hospital_ai.db.models import User


@pytest.mark.asyncio
async def test_clinical_timeline_endpoint(session_and_settings) -> None:
    session, _ = session_and_settings
    doctor = User(id=uuid.uuid4(), email="doc@test.com", full_name="Doc", role="doctor", is_active=True)

    with pytest.raises(HTTPException) as exc:
        await get_document_timeline(uuid.uuid4(), session, doctor)
    assert exc.value.status_code == 404
