import uuid

import pytest
from fastapi import HTTPException

from hospital_ai.api.routes.document_graph import get_document_graph
from hospital_ai.db.models import User
from hospital_ai.services.graph_query import GraphFilters


@pytest.mark.asyncio
async def test_document_graph_api_returns_404_for_unknown_doc(session_and_settings) -> None:
    session, _ = session_and_settings
    doctor = User(id=uuid.uuid4(), email="doc@test.com", full_name="Doc", role="doctor", is_active=True)
    filters = GraphFilters()

    with pytest.raises(HTTPException) as exc:
        await get_document_graph(uuid.uuid4(), filters, session, doctor)
    assert exc.value.status_code == 404
