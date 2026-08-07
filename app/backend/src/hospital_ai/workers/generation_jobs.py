from __future__ import annotations

import asyncio
import hashlib
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings
from hospital_ai.db.clinical_documents import (
    DocumentIndexGeneration,
    DocumentPageRevision,
    DocumentRevisionPage,
    DocumentRevisionSet,
    GenerationStageResult,
)
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage
from hospital_ai.services.chunking import ChunkingService
from hospital_ai.services.embeddings import EmbeddingService
from hospital_ai.services.generations import (
    GENERATION_STAGES,
    ActivationResult,
    GenerationService,
    calculate_generation_hash,
)
from hospital_ai.services.ocr import OcrPage

logger = logging.getLogger(__name__)

GenerationBuildResult = ActivationResult


@dataclass
class StageOutput:
    sha256: str
    row_count: int = 0


class StageRunner:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def run(
        self,
        stage: str,
        generation: DocumentIndexGeneration,
        revision_set: DocumentRevisionSet,
        custom_metadata: Optional[dict[str, Any]] = None,
    ) -> StageOutput:
        doc = await self.session.get(Document, generation.document_id)
        if not doc:
            raise ValueError(f"Document {generation.document_id} not found")

        if stage == "ocr_normalization":
            result = await self.session.execute(
                select(DocumentRevisionPage, DocumentPageRevision)
                .join(DocumentPageRevision, DocumentPageRevision.id == DocumentRevisionPage.page_revision_id)
                .where(DocumentRevisionPage.revision_set_id == revision_set.id)
                .order_by(DocumentRevisionPage.page_number)
            )
            rows = result.all()
            if not rows:
                content_str = "empty"
            else:
                content_str = "".join(rev.corrected_text for _, rev in rows)
            sha256 = hashlib.sha256(content_str.encode("utf-8")).hexdigest()
            return StageOutput(sha256=sha256, row_count=len(rows))

        elif stage == "facts":
            sha256 = hashlib.sha256(f"{generation.id}:facts".encode()).hexdigest()
            return StageOutput(sha256=sha256, row_count=0)

        elif stage == "chunks":
            result = await self.session.execute(
                select(DocumentRevisionPage, DocumentPageRevision)
                .join(DocumentPageRevision, DocumentPageRevision.id == DocumentRevisionPage.page_revision_id)
                .where(DocumentRevisionPage.revision_set_id == revision_set.id)
                .order_by(DocumentRevisionPage.page_number)
            )
            rev_pages = result.all()
            if not rev_pages:
                sha256 = hashlib.sha256(b"no_chunks").hexdigest()
                return StageOutput(sha256=sha256, row_count=0)

            pages_for_chunking = []
            page_map: dict[int, tuple[DocumentPage, DocumentPageRevision]] = {}
            for rev_p, page_rev in rev_pages:
                pages_for_chunking.append(
                    OcrPage(
                        page_number=rev_p.page_number,
                        text=page_rev.corrected_text,
                        confidence=float(page_rev.confidence or 1.0),
                    )
                )
                res = await self.session.execute(
                    select(DocumentPage).where(
                        DocumentPage.document_id == doc.id, DocumentPage.page_number == rev_p.page_number
                    )
                )
                db_page = res.scalar_one_or_none()
                if not db_page:
                    db_page = DocumentPage(
                        id=uuid.uuid4(),
                        document_id=doc.id,
                        page_number=rev_p.page_number,
                        ocr_text=page_rev.corrected_text,
                        ocr_confidence=page_rev.confidence,
                    )
                    self.session.add(db_page)
                    await self.session.flush()
                else:
                    db_page.ocr_text = page_rev.corrected_text
                    db_page.ocr_confidence = page_rev.confidence
                page_map[rev_p.page_number] = (db_page, page_rev)

            chunks = ChunkingService().chunk_pages(pages_for_chunking)
            for c_idx, chunk in enumerate(chunks):
                db_page, page_rev = page_map[chunk.page_number]
                meta_dict = {
                    "page_number": chunk.page_number,
                    "start_offset": chunk.start_offset,
                    "end_offset": chunk.end_offset,
                    "chunk_type": chunk.chunk_type,
                }
                if custom_metadata:
                    meta_dict.update(custom_metadata)
                db_chunk = DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=doc.id,
                    page_id=db_page.id,
                    patient_id=doc.patient_id,
                    chunk_index=c_idx,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    generation_id=generation.id,
                    revision_set_id=revision_set.id,
                    page_revision_id=page_rev.id,
                    meta=meta_dict,
                )
                self.session.add(db_chunk)
            await self.session.flush()
            sha256 = hashlib.sha256(f"{generation.id}:chunks:{len(chunks)}".encode()).hexdigest()
            return StageOutput(sha256=sha256, row_count=len(chunks))

        elif stage == "embeddings":
            res = await self.session.execute(
                select(DocumentChunk)
                .where(DocumentChunk.generation_id == generation.id)
                .order_by(DocumentChunk.chunk_index)
            )
            chunks = list(res.scalars().all())
            if chunks:
                embeddings = await EmbeddingService(self.settings).embed_many(c.content for c in chunks)
                if len(chunks) != len(embeddings):
                    raise ValueError("Embedding provider returned an unexpected number of vectors.")
                for c, emb in zip(chunks, embeddings, strict=True):
                    c.embedding = emb
                await self.session.flush()
            sha256 = hashlib.sha256(f"{generation.id}:embeddings:{len(chunks)}".encode()).hexdigest()
            return StageOutput(sha256=sha256, row_count=len(chunks))

        elif stage == "lexical_index":
            from hospital_ai.workers.jobs import _populate_tsvectors

            await _populate_tsvectors(self.session, doc.id)
            sha256 = hashlib.sha256(f"{generation.id}:lexical".encode()).hexdigest()
            return StageOutput(sha256=sha256, row_count=1)

        elif stage == "graph":
            from hospital_ai.services.graph_index import GraphIndexService
            from hospital_ai.services.graph_rag import GraphExtraction, extract_entities_and_relations_nlp

            res = await self.session.execute(
                select(DocumentChunk)
                .where(DocumentChunk.generation_id == generation.id)
                .order_by(DocumentChunk.chunk_index)
            )
            chunks = list(res.scalars().all())

            graph_service = GraphIndexService(self.session)
            import time
            start_time = time.time()
            trace_id = uuid.uuid4().hex
            
            for chunk in chunks:
                try:
                    entities, relations = await extract_entities_and_relations_nlp(chunk.content)
                    extraction = GraphExtraction(entities=entities, relations=relations)
                    await graph_service.index_chunk(generation.id, chunk, extraction)
                except Exception:
                    logger.error(
                        "generation.graph.failed",
                        extra={
                            "trace_id": trace_id,
                            "generation_id": str(generation.id),
                            "chunk_id": str(chunk.id),
                            "error_code": "GRAPH_EXTRACTION_FAILED",
                        },
                    )
                    raise

            sha256 = hashlib.sha256(f"{generation.id}:graph".encode()).hexdigest()
            logger.info(
                "generation.graph.completed",
                extra={
                    "trace_id": trace_id,
                    "generation_id": str(generation.id),
                    "chunk_count": len(chunks),
                    "output_sha256": sha256,
                    "latency": time.time() - start_time,
                },
            )
            return StageOutput(sha256=sha256, row_count=len(chunks))

        elif stage == "timeline":
            sha256 = hashlib.sha256(f"{generation.id}:timeline".encode()).hexdigest()
            return StageOutput(sha256=sha256, row_count=1)

        else:
            raise ValueError(f"Unknown generation stage {stage}")


class GenerationBuilder:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.stage_runner = StageRunner(session, settings)

    @classmethod
    def from_settings(cls, session: AsyncSession, settings: Settings) -> GenerationBuilder:
        return cls(session, settings)

    async def _lock_building_generation(self, generation_id: uuid.UUID) -> DocumentIndexGeneration:
        gen = await self.session.get(DocumentIndexGeneration, generation_id)
        if not gen or gen.state != "building":
            raise ValueError(f"Building generation {generation_id} not found or not building")
        gen.started_at = datetime.now(UTC)
        return gen

    async def _generation_hash(self, generation_id: uuid.UUID) -> str:
        res = await self.session.execute(
            select(GenerationStageResult.output_sha256)
            .where(GenerationStageResult.generation_id == generation_id)
            .order_by(GenerationStageResult.stage)
        )
        hashes = [h or "" for h in res.scalars().all()]
        return (
            hashlib.sha256(val.encode("utf-8") for val in hashes if val).hexdigest()
            if any(hashes)
            else hashlib.sha256(str(generation_id).encode("utf-8")).hexdigest()
        )

    async def _record_stage(
        self, generation_id: uuid.UUID, stage: str, output_sha256: str, row_count: int, status: str
    ) -> None:
        row = GenerationStageResult(
            id=uuid.uuid4(),
            generation_id=generation_id,
            stage=stage,
            status=status,
            output_sha256=output_sha256,
            completed_at=datetime.now(UTC) if status == "completed" else None,
        )
        self.session.add(row)
        await self.session.flush()

    async def build(
        self, generation_id: uuid.UUID, custom_metadata: Optional[dict[str, Any]] = None
    ) -> ActivationResult:
        try:
            generation = await self._lock_building_generation(generation_id)
            revision_set = await self.session.get(DocumentRevisionSet, generation.revision_set_id)
            if not revision_set:
                raise ValueError(f"Revision set {generation.revision_set_id} not found")

            for stage in GENERATION_STAGES:
                output = await self.stage_runner.run(stage, generation, revision_set, custom_metadata=custom_metadata)
                await self._record_stage(generation.id, stage, output.sha256, output.row_count, "completed")
                await self.session.commit()
                # Re-fetch generation after commit
                generation = await self.session.get(DocumentIndexGeneration, generation_id)
                if not generation:
                    raise ValueError(f"Generation {generation_id} missing after stage {stage}")
                revision_set = await self.session.get(DocumentRevisionSet, generation.revision_set_id)

            # Compute hash
            res = await self.session.execute(
                select(GenerationStageResult.output_sha256)
                .where(GenerationStageResult.generation_id == generation.id)
                .order_by(GenerationStageResult.stage)
            )
            generation.generation_sha256 = calculate_generation_hash([str(h) for h in res.scalars().all()])
            await self.session.commit()

            doc = await self.session.get(Document, generation.document_id)
            if not doc:
                raise ValueError(f"Document {generation.document_id} not found")
            return await GenerationService(self.session).activate(
                generation.id, expected_active_generation_id=doc.active_index_generation_id
            )
        except Exception as exc:
            logger.exception("Failed building generation %s: %s", generation_id, exc)
            await self.session.rollback()
            await GenerationService(self.session).fail(generation_id, "STAGE_FAILED", str(exc))
            raise


async def import_synthetic_generation(
    session: AsyncSession,
    settings: Settings,
    document: Document,
    content: str,
    user_id: uuid.UUID,
    metadata: dict[str, Any],
) -> ActivationResult:
    """Helper to create a synthetic source revision-set and build index generation for importers."""
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
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
        created_by_user_id=user_id,
        approved_by_user_id=user_id,
        approved_at=datetime.now(UTC),
        content_sha256=content_hash,
    )
    session.add(page_rev)
    await session.flush()

    result_num = await session.execute(
        select(func.max(DocumentRevisionSet.revision_number)).where(DocumentRevisionSet.document_id == document.id)
    )
    max_num = result_num.scalar() or 0
    rev_set = DocumentRevisionSet(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_number=max_num + 1,
        status="approved",
        created_by_user_id=user_id,
        submitted_at=datetime.now(UTC),
        approved_by_user_id=user_id,
        approved_at=datetime.now(UTC),
    )
    session.add(rev_set)
    await session.flush()

    rev_page = DocumentRevisionPage(
        revision_set_id=rev_set.id,
        page_number=1,
        page_revision_id=page_rev.id,
    )
    session.add(rev_page)

    gen = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_set_id=rev_set.id,
        state="building",
        revision_set_sha256=content_hash,
    )
    session.add(gen)
    await session.flush()
    await session.commit()

    builder = GenerationBuilder.from_settings(session, settings)
    return await builder.build(gen.id, custom_metadata=metadata)


def build_generation_job(generation_id: str) -> None:
    async def run() -> None:
        from hospital_ai.core.config import get_settings
        from hospital_ai.db.session import get_session_factory

        async with get_session_factory()() as session:
            await GenerationBuilder.from_settings(session, get_settings()).build(uuid.UUID(generation_id))

    asyncio.run(run())


def enqueue_build_generation_job(generation_id: uuid.UUID, settings: Optional[Settings] = None) -> None:
    from hospital_ai.workers.queue import enqueue_build_generation

    enqueue_build_generation(generation_id, settings)
