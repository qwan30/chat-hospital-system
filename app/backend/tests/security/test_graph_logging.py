from __future__ import annotations

import pytest
from sqlalchemy import select

from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import DocumentChunk
from hospital_ai.services.graph_rag import ExtractedEntity, index_chunk_entities
from tests.conftest import create_indexed_document


@pytest.mark.asyncio
async def test_graph_index_logs_only_safe_identifiers_and_counts(session_and_settings, caplog) -> None:
    session, _ = session_and_settings
    clinical_text = "SECRET_CLINICAL_TEXT metformin patient detail"
    doc = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Logging safety note",
        content=clinical_text,
    )
    chunk = (await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))).scalar_one()

    async def extractor(_content: str):
        return [ExtractedEntity(normalized_label="secret medication", entity_type="drug")], []

    from unittest.mock import patch

    with patch("hospital_ai.services.graph_rag.logger") as mock_logger:
        await index_chunk_entities(session, chunk.id, doc.id, clinical_text, extractor=extractor)

        messages = " ".join(call.args[0] for call in mock_logger.info.call_args_list if call.args)
        assert "graph.extraction.completed" in messages
    assert "graph.index.completed" in messages
    assert clinical_text not in messages
    assert "secret medication" not in messages
