import os
import sys
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Rate limiting is fail-closed (enabled unless TESTING opts out), and
# hospital_ai.api.limiter reads this at import time — so it must be set
# before any hospital_ai module is imported below.
os.environ.setdefault("TESTING", "true")

# Match the CI backend-test job (ci.yml sets HOSPITAL_AI_DISABLE_GUARDRAILS=true).
# The guardrail scanners are ONNX models that take ~4-8s per scan on CPU; running
# them for real makes the suite slow and timing-dependent. Tests that exercise
# guardrail behaviour patch the scanners directly instead.
os.environ.setdefault("HOSPITAL_AI_DISABLE_GUARDRAILS", "true")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # noqa: E402

import datetime  # noqa: E402
from datetime import timezone  # noqa: E402

if not hasattr(datetime, "UTC"):  # noqa: E402
    datetime.UTC = timezone.utc  # noqa: E402, UP017

from hospital_ai.core.config import Settings  # noqa: E402
from hospital_ai.db.migrations import seed_synthetic_data  # noqa: E402
from hospital_ai.db.models import Base, Document, DocumentChunk, DocumentPage  # noqa: E402
from hospital_ai.services.embeddings import deterministic_embedding  # noqa: E402


@pytest.fixture(autouse=True)
def mock_extract_entities_and_relations_nlp(monkeypatch):
    from hospital_ai.services.graph_rag import ExtractedEntity, ExtractedRelation

    async def mock_extract_nlp(content):
        entities = []
        relations = []

        if "metformin" in content.lower():
            entities.append(ExtractedEntity("metformin", "drug"))
        if "diabetes" in content.lower():
            entities.append(ExtractedEntity("diabetes", "condition"))
            relations.append(ExtractedRelation("metformin", "diabetes", "treats"))
        if "lisinopril" in content.lower():
            entities.append(ExtractedEntity("lisinopril", "drug"))
        if "hypertension" in content.lower():
            entities.append(ExtractedEntity("hypertension", "condition"))
        if "lisinopril" in content.lower() and "hypertension" in content.lower():
            relations.append(ExtractedRelation("lisinopril", "hypertension", "treats"))
        if "aspirin" in content.lower():
            entities.append(ExtractedEntity("aspirin", "drug"))
        if "metformin" in content.lower() and "aspirin" in content.lower():
            # Add an explicit relation to simulate the test's expectation for Bob's text
            relations.append(ExtractedRelation("metformin", "aspirin", "prescribed_for"))

        return entities, relations

    monkeypatch.setattr("hospital_ai.services.graph_rag.extract_entities_and_relations_nlp", mock_extract_nlp)


@pytest_asyncio.fixture
async def session_and_settings(tmp_path: Path) -> AsyncIterator[tuple[AsyncSession, Settings]]:
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
    from hospital_ai.db.clinical_documents import (
        DocumentRevisionSet,
        DocumentPageRevision,
        DocumentIndexGeneration,
    )
    import hashlib

    document = Document(
        patient_id=patient_id,
        uploaded_by=uploaded_by,
        title=title,
        document_type="note",
        storage_uri="memory://synthetic",
        mime_type="text/plain",
        status="ready",
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

    content_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
    page_rev = DocumentPageRevision(
        id=uuid.uuid4(),
        document_id=document.id,
        page_number=1,
        revision_number=1,
        revision_type="machine_ocr",
        raw_text_snapshot=content,
        corrected_text=content,
        confidence=1.0,
        status="approved",
        created_by_user_id=uploaded_by,
        content_sha256=content_sha,
        version=1,
    )
    session.add(page_rev)
    await session.flush()

    rev_set = DocumentRevisionSet(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_number=1,
        status="approved",
        created_by_user_id=uploaded_by,
        submitted_at=datetime.datetime.now(datetime.UTC),
        approved_by_user_id=uploaded_by,
        approved_at=datetime.datetime.now(datetime.UTC),
    )
    session.add(rev_set)
    await session.flush()

    gen = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_set_id=rev_set.id,
        state="active",
        revision_set_sha256=content_sha,
        generation_sha256=content_sha,
        created_at=datetime.datetime.now(datetime.UTC),
        started_at=datetime.datetime.now(datetime.UTC),
        activated_at=datetime.datetime.now(datetime.UTC),
    )
    session.add(gen)
    await session.flush()

    document.approved_revision_set_id = rev_set.id
    document.active_index_generation_id = gen.id

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
            generation_id=gen.id,
            revision_set_id=rev_set.id,
            page_revision_id=page_rev.id,
            approval_state="approved",
            source_text_sha256=content_sha,
            text_start_offset=0,
            text_end_offset=len(content),
        )
    )
    await session.commit()
    return document
