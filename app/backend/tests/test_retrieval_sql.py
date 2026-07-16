from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update

from hospital_ai.core.security import PATIENT_READ_SCOPES
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage, PatientPermission
from hospital_ai.services.embeddings import deterministic_embedding
from hospital_ai.services.permissions import ACTIVE_PATIENT_PERMISSION_SQL
from hospital_ai.services.retrieval import PERMISSION_FILTERED_RETRIEVAL_SQL, RetrievalService
from tests.conftest import create_indexed_document


def test_retrieval_sql_does_not_repeat_patient_permission_filter():
    sql = PERMISSION_FILTERED_RETRIEVAL_SQL.lower()
    assert ACTIVE_PATIENT_PERMISSION_SQL.lower() not in sql
    assert "from patient_permissions" not in sql
    assert "pp.user_id = :user_id" not in sql
    assert "where exists (select 1 from allowed)" not in sql
    assert "c.patient_id = :patient_id" in sql
    assert "d.patient_id = :patient_id" in sql
    assert "p.id = c.page_id and p.document_id = c.document_id" in sql
    assert "c.embedding is not null" in sql
    assert "c.deleted_at is null" in sql
    assert "d.deleted_at is null" in sql
    assert "p.deleted_at is null" in sql


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
async def test_revoked_patient_permission_blocks_portable_retrieval(session_and_settings):
    session, _ = session_and_settings
    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice revoked note",
        content="Alice has a note that must not be retrieved after revocation.",
    )
    await session.execute(
        update(PatientPermission)
        .where(
            PatientPermission.user_id == DOCTOR_ID,
            PatientPermission.patient_id == PATIENT_ALICE_ID,
            PatientPermission.scope.in_(PATIENT_READ_SCOPES),
        )
        .values(deleted_at=datetime.now(UTC))
    )
    await session.commit()

    results = await RetrievalService(session).search(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        query_embedding=deterministic_embedding("revoked note"),
        top_k=5,
    )

    assert results == []


@pytest.mark.asyncio
async def test_expired_patient_permission_blocks_portable_retrieval(session_and_settings):
    session, _ = session_and_settings
    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice expired note",
        content="Alice has a note that must not be retrieved after expiration.",
    )
    await session.execute(
        update(PatientPermission)
        .where(
            PatientPermission.user_id == DOCTOR_ID,
            PatientPermission.patient_id == PATIENT_ALICE_ID,
            PatientPermission.scope.in_(PATIENT_READ_SCOPES),
        )
        .values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
    )
    await session.commit()

    results = await RetrievalService(session).search(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        query_embedding=deterministic_embedding("expired note"),
        top_k=5,
    )

    assert results == []


@pytest.mark.asyncio
async def test_soft_deleted_document_is_not_retrieved(session_and_settings):
    session, _ = session_and_settings
    document = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice deleted document",
        content="Deleted document content must not be retrieved.",
    )
    await session.execute(update(Document).where(Document.id == document.id).values(deleted_at=datetime.now(UTC)))
    await session.commit()

    results = await RetrievalService(session).search(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        query_embedding=deterministic_embedding("deleted document"),
        top_k=5,
    )

    assert results == []


@pytest.mark.asyncio
async def test_soft_deleted_page_is_not_retrieved(session_and_settings):
    session, _ = session_and_settings
    document = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice deleted page",
        content="Deleted page content must not be retrieved.",
    )
    await session.execute(
        update(DocumentPage).where(DocumentPage.document_id == document.id).values(deleted_at=datetime.now(UTC))
    )
    await session.commit()

    results = await RetrievalService(session).search(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        query_embedding=deterministic_embedding("deleted page"),
        top_k=5,
    )

    assert results == []


@pytest.mark.asyncio
async def test_soft_deleted_chunk_is_not_retrieved(session_and_settings):
    session, _ = session_and_settings
    document = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice deleted chunk",
        content="Deleted chunk content must not be retrieved.",
    )
    await session.execute(
        update(DocumentChunk).where(DocumentChunk.document_id == document.id).values(deleted_at=datetime.now(UTC))
    )
    await session.commit()

    results = await RetrievalService(session).search(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        query_embedding=deterministic_embedding("deleted chunk"),
        top_k=5,
    )

    assert results == []


@pytest.mark.asyncio
async def test_mismatched_chunk_document_patient_is_not_retrieved(session_and_settings):
    session, _ = session_and_settings
    document = await create_indexed_document(
        session,
        patient_id=PATIENT_BOB_ID,
        uploaded_by=DOCTOR_ID,
        title="Bob mismatched note",
        content="Bob content must not be exposed through an Alice-owned chunk.",
    )
    await session.execute(
        update(DocumentChunk).where(DocumentChunk.document_id == document.id).values(patient_id=PATIENT_ALICE_ID)
    )
    await session.commit()

    results = await RetrievalService(session).search(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        query_embedding=deterministic_embedding("Bob content"),
        top_k=5,
    )

    assert results == []


@pytest.mark.asyncio
async def test_mismatched_chunk_page_document_is_not_retrieved(session_and_settings):
    session, _ = session_and_settings
    alice_document = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice mismatched note",
        content="Alice content should not use a page from another document.",
    )
    bob_document = await create_indexed_document(
        session,
        patient_id=PATIENT_BOB_ID,
        uploaded_by=DOCTOR_ID,
        title="Bob page source",
        content="Bob page must not be cited for Alice evidence.",
    )
    bob_page_result = await session.execute(select(DocumentPage).where(DocumentPage.document_id == bob_document.id))
    bob_page = bob_page_result.scalar_one()
    await session.execute(
        update(DocumentChunk).where(DocumentChunk.document_id == alice_document.id).values(page_id=bob_page.id)
    )
    await session.commit()

    results = await RetrievalService(session).search(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        query_embedding=deterministic_embedding("Alice content"),
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
