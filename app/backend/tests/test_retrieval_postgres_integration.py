from __future__ import annotations

import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from hospital_ai.core.config import Settings
from hospital_ai.core.security import PATIENT_READ_SCOPES
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, seed_synthetic_data
from hospital_ai.db.models import Base, PatientPermission
from hospital_ai.services.embeddings import deterministic_embedding
from hospital_ai.services.retrieval import RetrievalService
from tests.conftest import create_indexed_document

POSTGRES_TEST_URL = os.getenv("HOSPITAL_AI_TEST_POSTGRES_URL")

pytestmark = pytest.mark.skipif(
    POSTGRES_TEST_URL is None,
    reason="Set HOSPITAL_AI_TEST_POSTGRES_URL to run PostgreSQL retrieval integration tests.",
)


@pytest_asyncio.fixture
async def postgres_session_and_settings(
    tmp_path: Path,
) -> AsyncIterator[tuple[AsyncSession, Settings]]:
    settings = Settings(
        database_url=POSTGRES_TEST_URL,
        storage_root=tmp_path / "storage",
        worker_inline=True,
        embedding_provider="deterministic",
        chat_provider="stub",
        evidence_threshold=0.0,
    )
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        await seed_synthetic_data(session)
        yield session, settings

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_postgres_retrieval_blocks_revoked_permission(
    postgres_session_and_settings,
):
    session, _ = postgres_session_and_settings
    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice PostgreSQL revoked note",
        content="PostgreSQL retrieval must filter revoked permissions.",
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
        query_embedding=deterministic_embedding("revoked permissions"),
        top_k=5,
    )

    assert results == []


@pytest.mark.asyncio
async def test_postgres_retrieval_blocks_expired_permission(
    postgres_session_and_settings,
):
    session, _ = postgres_session_and_settings
    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Alice PostgreSQL expired note",
        content="PostgreSQL retrieval must filter expired permissions.",
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
        query_embedding=deterministic_embedding("expired permissions"),
        top_k=5,
    )

    assert results == []
