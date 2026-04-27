import sys
import uuid
from pathlib import Path
from typing import AsyncIterator, Tuple

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hospital_ai.core.config import Settings
from hospital_ai.db.migrations import seed_synthetic_data
from hospital_ai.db.models import Base, Document, DocumentChunk, DocumentPage
from hospital_ai.services.embeddings import deterministic_embedding


@pytest_asyncio.fixture
async def session_and_settings(tmp_path: Path) -> AsyncIterator[Tuple[AsyncSession, Settings]]:
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        storage_root=tmp_path / "storage",
        worker_inline=True,
        embedding_provider="deterministic",
        chat_provider="stub",
        evidence_threshold=0.0,
    )
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        await seed_synthetic_data(session)
        yield session, settings

    await engine.dispose()


async def create_indexed_document(
    session: AsyncSession,
    *,
    patient_id: uuid.UUID,
    uploaded_by: uuid.UUID,
    title: str,
    content: str,
) -> Document:
    document = Document(
        patient_id=patient_id,
        uploaded_by=uploaded_by,
        title=title,
        document_type="note",
        storage_uri="memory://synthetic",
        mime_type="text/plain",
        status="indexed",
        page_count=1,
    )
    session.add(document)
    await session.flush()

    page = DocumentPage(
        document_id=document.id,
        page_number=1,
        ocr_text=content,
        ocr_confidence=1.0,
    )
    session.add(page)
    await session.flush()

    session.add(
        DocumentChunk(
            document_id=document.id,
            page_id=page.id,
            patient_id=patient_id,
            chunk_index=0,
            content=content,
            token_count=len(content.split()),
            embedding=deterministic_embedding(content),
            meta={"page_number": 1},
        )
    )
    await session.commit()
    return document
