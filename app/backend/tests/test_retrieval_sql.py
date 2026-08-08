from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update

from hospital_ai.core.security import PATIENT_READ_SCOPES
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage, PatientPermission, User
from hospital_ai.services.embeddings import deterministic_embedding
from hospital_ai.services.retrieval import RetrievalService, _scope_matches
from tests.conftest import create_indexed_document


def test_forward_bm25_migration_creates_tsvector_and_gin_index():
    from pathlib import Path

    migrations = Path(__file__).parents[1] / "alembic" / "versions"
    forward_migrations = [
        path.read_text(encoding="utf-8").lower()
        for path in migrations.glob("*.py")
        if "search_vector" in path.read_text(encoding="utf-8").lower() and path.name != "0006_add_phase4_tables.py"
    ]
    assert any("tsvector" in migration and "gin" in migration for migration in forward_migrations)


def test_bm25_migration_downgrade_restores_parent_text_schema_contract():
    from pathlib import Path

    migration = (Path(__file__).parents[1] / "alembic" / "versions" / "0009_repair_search_vector_gin.py").read_text()
    assert "def downgrade" in migration
    assert "ALTER COLUMN search_vector TYPE text" in migration
    assert "DROP TRIGGER" in migration


def test_role_scope_matching_is_exact_after_normalization():
    assert _scope_matches(" Medication ", "medication")
    assert not _scope_matches("medication", "medications")
    assert not _scope_matches("medication", "medication_safety")
    assert not _scope_matches("labs", "lab")


@pytest.mark.asyncio
async def test_postgres_vector_query_embedding_uses_native_list_binding(monkeypatch):
    class Result:
        def all(self):
            return []

    class Session:
        def __init__(self):
            self.params = None

        async def execute(self, statement, params=None):
            self.params = params
            return Result()

    session = Session()
    monkeypatch.setattr(
        "hospital_ai.services.retrieval.ActiveEvidenceScope.authorized_chunk_ids",
        lambda self, *, user_id, patient_id: [],
    )

    await RetrievalService(session)._search_postgres(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        query_embedding=[0.1, 0.2],
        top_k=1,
    )

    assert session.params["query_embedding"] == [0.1, 0.2]


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


@pytest.mark.asyncio
async def test_ready_with_warnings_document_remains_retrievable(session_and_settings):
    session, _ = session_and_settings
    document = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Preserved discharge",
        content="The previous generation remains valid after a failed replacement.",
    )
    document.status = "ready_with_warnings"
    await session.commit()

    results = await RetrievalService(session).search(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        query_embedding=deterministic_embedding("previous generation remains valid"),
        top_k=5,
    )

    assert len(results) == 1
    assert results[0].document_title == "Preserved discharge"


@pytest.mark.asyncio
async def test_global_knowledge_is_runtime_quarantined(session_and_settings):
    session, _ = session_and_settings
    await create_indexed_document(
        session,
        patient_id=None,
        uploaded_by=DOCTOR_ID,
        title="Unreviewed Guideline",
        content="Unreviewed public guidance.",
    )

    service = RetrievalService(session)
    assert (
        await service.search(
            user_id=DOCTOR_ID,
            patient_id=None,
            query_embedding=deterministic_embedding("guidance"),
            top_k=5,
        )
        == []
    )
    assert (
        await service.hybrid_search(
            user_id=DOCTOR_ID,
            patient_id=None,
            query_embedding=deterministic_embedding("guidance"),
            query_text="guidance",
            top_k=5,
        )
        == []
    )


@pytest.mark.asyncio
async def test_patient_linked_excludes_global_knowledge(session_and_settings):
    session, _ = session_and_settings
    await create_indexed_document(
        session,
        patient_id=None,
        uploaded_by=DOCTOR_ID,
        title="Unreviewed Guideline",
        content="Shared discharge guidance must stay quarantined.",
    )
    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice Discharge Note",
        content="Alice-specific discharge guidance.",
    )

    results = await RetrievalService(session).search(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        query_embedding=deterministic_embedding("discharge guidance"),
        top_k=5,
    )

    assert [result.document_title for result in results] == ["Alice Discharge Note"]


@pytest.mark.asyncio
async def test_hybrid_search_filters_denied_access_tags(session_and_settings):
    session, _ = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    assert doctor is not None
    doctor.role = "lab_staff"

    document = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Restricted medication note",
        content="Medication-only content must not reach lab staff.",
    )
    await session.execute(
        update(DocumentChunk)
        .where(DocumentChunk.document_id == document.id)
        .values(meta={"access_tags": ["medication"]})
    )
    await session.commit()

    results = await RetrievalService(session).hybrid_search(
        user_id=DOCTOR_ID,
        patient_id=PATIENT_ALICE_ID,
        query_embedding=deterministic_embedding("medication content"),
        query_text="medication content",
        top_k=5,
    )

    assert results == []
