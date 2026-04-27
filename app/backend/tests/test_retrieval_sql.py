import pytest

from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID
from hospital_ai.services.embeddings import deterministic_embedding
from hospital_ai.services.retrieval import PERMISSION_FILTERED_RETRIEVAL_SQL, RetrievalService
from tests.conftest import create_indexed_document


def test_retrieval_sql_repeats_patient_permission_filter():
    sql = PERMISSION_FILTERED_RETRIEVAL_SQL.lower()
    assert "from patient_permissions" in sql
    assert "pp.user_id = :user_id" in sql
    assert "pp.patient_id = :patient_id" in sql
    assert "where exists (select 1 from allowed)" in sql
    assert "c.patient_id = :patient_id" in sql


@pytest.mark.asyncio
async def test_unauthorized_patient_chunks_are_not_retrieved(session_and_settings):
    session, _ = session_and_settings
    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice note",
        content="Alice has a documented penicillin allergy.",
    )
    await create_indexed_document(
        session,
        patient_id=PATIENT_BOB_ID,
        uploaded_by=DOCTOR_ID,
        title="Bob note",
        content="Bob has a confidential cardiology note.",
    )

    results = await RetrievalService(session).search(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_BOB_ID,
        query_embedding=deterministic_embedding("confidential cardiology"),
        top_k=5,
    )

    assert results == []


@pytest.mark.asyncio
async def test_authorized_patient_chunks_are_retrieved(session_and_settings):
    session, _ = session_and_settings
    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice discharge",
        content="Alice should follow up with internal medicine after discharge.",
    )

    results = await RetrievalService(session).search(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        query_embedding=deterministic_embedding("internal medicine discharge"),
        top_k=5,
    )

    assert len(results) == 1
    assert results[0].evidence_id == "E1"
    assert results[0].document_title == "Alice discharge"
