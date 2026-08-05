from __future__ import annotations
from typing import Optional
"""Isolated adapter that observes the real product retrieval service.

The adapter intentionally owns a disposable SQLite schema.  It materializes
only canonical source artifacts referenced by a case, then converts the
``RetrievalService`` output back into untrusted runtime provenance for the
evaluation runner to validate.
"""


import csv
import hashlib
import io
from collections.abc import Iterable
from pathlib import Path
from uuid import UUID

import fitz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from hospital_ai.core.config import Settings
from hospital_ai.db.models import (
    Base,
    Document,
    DocumentChunk,
    DocumentPage,
    Patient,
    PatientPermission,
    User,
)
from hospital_ai.evaluation.adapter_foundation import (
    EvaluationCaseContext,
    EvidenceResolutionError,
    RuntimeEvidenceChunk,
)
from hospital_ai.evaluation.benchmark import EvalCaseV2
from hospital_ai.evaluation.corpus_manifest import EvidenceLocator, SourceArtifact
from hospital_ai.evaluation.runner import CaseObservation
from hospital_ai.services.chat_utils import meets_evidence_threshold
from hospital_ai.services.embeddings import deterministic_embedding
from hospital_ai.services.retrieval import RetrievalService


class ProductRetrievalAdapter:
    """Run retrieval evaluation against a temporary, source-backed schema."""

    def __init__(
        self,
        source_root: Path,
        evidence_threshold: Optional[float] = None,
        retrieval_mode: str = "vector",
    ) -> None:
        if retrieval_mode not in {"vector", "bm25", "hybrid", "graph"}:
            raise ValueError("retrieval_mode must be vector, bm25, hybrid, or graph")
        self._source_root = source_root.resolve()
        self._evidence_threshold = (
            evidence_threshold if evidence_threshold is not None else Settings().evidence_threshold
        )
        self.retrieval_mode = retrieval_mode

    async def evaluate(self, case: EvalCaseV2, context: EvaluationCaseContext) -> CaseObservation:
        """Materialize one case and return only evidence actually retrieved."""

        if case.patient_id not in context.actor.allowed_patient_ids:
            return CaseObservation(
                refused=True,
                sync_safety_outcome="refused",
                stream_safety_outcome="refused",
            )
        locators = self._unique_locators(
            case.allowed_evidence + case.forbidden_evidence + case.absence_checked_evidence
        )
        artifacts = tuple((locator, context.evidence_resolver.artifact_for(locator)) for locator in locators)
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        try:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            factory = async_sessionmaker(engine, expire_on_commit=False)
            async with factory() as session:
                await self._materialize(
                    session,
                    context.actor.actor_id,
                    context.actor.role,
                    context.actor.allowed_patient_ids,
                    artifacts,
                )
                if self.retrieval_mode == "graph":
                    from hospital_ai.db.models import DocumentChunk
                    from hospital_ai.services.graph_rag import (
                        extract_entities_and_relations_offline,
                        find_related_entities,
                        index_chunk_entities,
                    )

                    chunks = list((await session.execute(select(DocumentChunk))).scalars())
                    for chunk in chunks:
                        await index_chunk_entities(
                            session,
                            chunk.id,
                            chunk.document_id,
                            chunk.content,
                            extractor=extract_entities_and_relations_offline,
                        )
                    await session.flush()

                retrieval = RetrievalService(session)
                query_embedding = deterministic_embedding(case.question)
                top_k = max(1, len(locators))
                if self.retrieval_mode == "vector":
                    results = await retrieval.search(
                        user_id=context.actor.actor_id,
                        patient_id=case.patient_id,
                        query_embedding=query_embedding,
                        top_k=top_k,
                    )
                elif self.retrieval_mode in ("bm25", "hybrid"):
                    results = await retrieval.hybrid_search(
                        user_id=context.actor.actor_id,
                        patient_id=case.patient_id,
                        query_embedding=query_embedding,
                        query_text=case.question,
                        top_k=top_k,
                        retrieval_mode=self.retrieval_mode,
                    )
                else:  # graph mode
                    base_results = await retrieval.hybrid_search(
                        user_id=context.actor.actor_id,
                        patient_id=case.patient_id,
                        query_embedding=query_embedding,
                        query_text=case.question,
                        top_k=top_k,
                        retrieval_mode="hybrid",
                    )
                    graph_nodes = list(case.graph.required_nodes) if case.graph else []
                    if graph_nodes:
                        from hospital_ai.services.graph_rag import find_related_entities

                        graph_ctx = await find_related_entities(
                            session,
                            graph_nodes,
                            patient_id=case.patient_id,
                        )
                        graph_chunks = await retrieval.get_chunks_by_ids(
                            list(graph_ctx.related_chunk_ids),
                            user_id=context.actor.actor_id,
                            patient_id=case.patient_id,
                        )
                        seen_ids = {r.chunk_id for r in base_results}
                        combined = list(base_results)
                        for gc in graph_chunks:
                            if gc.chunk_id not in seen_ids:
                                combined.append(gc)
                                seen_ids.add(gc.chunk_id)
                        results = combined
                    else:
                        results = base_results
                eval_mode = "hybrid" if self.retrieval_mode == "graph" else self.retrieval_mode
                if not results or not meets_evidence_threshold(
                    results[0],
                    eval_mode,
                    self._evidence_threshold,
                ):
                    return CaseObservation()
                evidence = tuple(self._runtime_evidence(result) for result in results)
                return CaseObservation(retrieved_evidence=evidence)
        finally:
            await engine.dispose()

    @staticmethod
    def _unique_locators(locators: tuple[EvidenceLocator, ...]) -> tuple[EvidenceLocator, ...]:
        seen: set[tuple[str, Optional[int], Optional[int], Optional[str]]] = set()
        output = []
        for locator in locators:
            key = (locator.source_path, locator.page_number, locator.row_number, locator.record_id)
            if key in seen:
                raise EvidenceResolutionError("ambiguous duplicate source locator in evaluation case")
            seen.add(key)
            output.append(locator)
        return tuple(output)

    async def _materialize(
        self,
        session,
        actor_id: UUID,
        actor_role: str,
        allowed_patient_ids: tuple[UUID, ...],
        artifacts: Iterable[tuple[EvidenceLocator, SourceArtifact]],
    ) -> None:
        artifacts = tuple(artifacts)
        session.add(
            User(
                id=actor_id,
                email=f"eval-{actor_id.hex}@example.invalid",
                full_name="Evaluation Actor",
                role=actor_role,
            )
        )
        patient_ids = {artifact.patient_id for _locator, artifact in artifacts if artifact.patient_id is not None}
        for patient_id in patient_ids:
            session.add(Patient(id=patient_id, mrn=f"EVAL-{patient_id.hex}", full_name="Evaluation Patient"))
        await session.flush()
        for patient_id in patient_ids.intersection(allowed_patient_ids):
            session.add(PatientPermission(user_id=actor_id, patient_id=patient_id, scope="read", source="evaluation"))
        await session.flush()

        for index, (locator, artifact) in enumerate(artifacts):
            if artifact.patient_id is None:
                raise EvidenceResolutionError("retrieval adapter refuses non-patient canonical artifacts")
            payload = self._read_and_verify(artifact)
            content = self._content_for_locator(payload, artifact, locator)
            document = Document(
                patient_id=artifact.patient_id,
                uploaded_by=actor_id,
                title=artifact.canonical_relative_path,
                document_type=artifact.document_type,
                storage_uri=artifact.canonical_relative_path,
                mime_type=artifact.mime_type,
                status="ready",
                page_count=1,
                indexed_source_sha256=artifact.source_sha256,
            )
            session.add(document)
            await session.flush()
            page = DocumentPage(
                document_id=document.id,
                page_number=locator.page_number or 1,
                ocr_text=content,
                ocr_confidence=1.0,
            )
            session.add(page)
            await session.flush()

            from hospital_ai.db.clinical_documents import (
                DocumentRevisionSet,
                DocumentPageRevision,
                DocumentIndexGeneration,
            )
            import datetime
            import uuid

            rev_set = DocumentRevisionSet(
                id=uuid.uuid4(),
                document_id=document.id,
                revision_number=1,
                status="approved",
                created_by_user_id=actor_id,
                submitted_at=datetime.datetime.now(datetime.UTC),
                approved_by_user_id=actor_id,
                approved_at=datetime.datetime.now(datetime.UTC),
            )
            session.add(rev_set)
            
            page_rev = DocumentPageRevision(
                id=uuid.uuid4(),
                document_id=document.id,
                page_number=locator.page_number or 1,
                revision_number=1,
                revision_type="machine_ocr",
                raw_text_snapshot=content,
                corrected_text=content,
                confidence=1.0,
                status="approved",
                created_by_user_id=actor_id,
                content_sha256=artifact.source_sha256,
                version=1,
            )
            session.add(page_rev)

            gen = DocumentIndexGeneration(
                id=uuid.uuid4(),
                document_id=document.id,
                revision_set_id=rev_set.id,
                state="active",
                revision_set_sha256=artifact.source_sha256,
                generation_sha256=artifact.source_sha256,
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
                    patient_id=artifact.patient_id,
                    chunk_index=index,
                    content=content,
                    token_count=len(content.split()),
                    embedding=deterministic_embedding(content),
                    meta={
                        "source_path": artifact.canonical_relative_path,
                        "source_sha256": artifact.source_sha256,
                        "patient_id": str(artifact.patient_id),
                        "page_number": locator.page_number,
                        "row_number": locator.row_number,
                        "record_id": locator.record_id,
                        "access_tags": list(artifact.access_tags),
                    },
                    generation_id=gen.id,
                    revision_set_id=rev_set.id,
                    page_revision_id=page_rev.id,
                    approval_state="approved",
                    source_text_sha256=artifact.source_sha256,
                    text_start_offset=0,
                    text_end_offset=len(content),
                )
            )
        await session.commit()

    def _read_and_verify(self, artifact: SourceArtifact) -> bytes:
        target = (self._source_root / artifact.canonical_relative_path).resolve()
        try:
            target.relative_to(self._source_root)
        except ValueError as error:
            raise EvidenceResolutionError("canonical source path escapes adapter source root") from error
        if not target.is_file():
            raise EvidenceResolutionError(f"canonical source is missing: {artifact.canonical_relative_path}")
        payload = target.read_bytes()
        if hashlib.sha256(payload).hexdigest() != artifact.source_sha256:
            raise EvidenceResolutionError(f"canonical source hash does not match: {artifact.canonical_relative_path}")
        return payload

    @staticmethod
    def _content_for_locator(payload: bytes, artifact: SourceArtifact, locator: EvidenceLocator) -> str:
        if artifact.mime_type == "application/pdf":
            try:
                document = fitz.open(stream=payload, filetype="pdf")
                try:
                    if locator.page_number is None:
                        return "\n".join(page.get_text("text").strip() for page in document).strip()
                    if locator.page_number > document.page_count:
                        raise EvidenceResolutionError("PDF locator page is outside the canonical source")
                    return document.load_page(locator.page_number - 1).get_text("text").strip()
                finally:
                    document.close()
            except fitz.FileDataError as error:
                raise EvidenceResolutionError("canonical PDF source cannot be read") from error
        if artifact.mime_type == "text/csv":
            decoded = payload.decode("utf-8")
            if locator.row_number is None:
                return decoded.strip()
            rows = list(csv.DictReader(io.StringIO(decoded)))
            row_index = locator.row_number - 2
            if row_index < 0 or row_index >= len(rows):
                raise EvidenceResolutionError("CSV locator row is outside the canonical source")
            return "\n".join(f"{key}: {value}" for key, value in rows[row_index].items())
        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise EvidenceResolutionError("adapter supports only source text and CSV without OCR") from error

    @staticmethod
    def _runtime_evidence(result) -> RuntimeEvidenceChunk:
        metadata = result.metadata
        try:
            return RuntimeEvidenceChunk(
                runtime_chunk_id=str(result.chunk_id),
                source_path=metadata["source_path"],
                source_sha256=metadata["source_sha256"],
                patient_id=metadata.get("patient_id"),
                page_number=metadata.get("page_number"),
                row_number=metadata.get("row_number"),
                record_id=metadata.get("record_id"),
            )
        except (KeyError, ValueError, TypeError) as error:
            raise EvidenceResolutionError("retrieval result lacks exact source provenance") from error
