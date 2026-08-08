"""Isolated, offline-safe adapter for the product Graph RAG traversal.

The adapter materializes canonical evidence in a disposable SQLite schema,
indexes it through the real graph models, then fetches graph-discovered chunks
through the production permission-aware retrieval service.  It never starts an
LLM provider: graph extraction is explicitly limited to the deterministic
fallback grammar.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from hospital_ai.db.models import Base, DocumentChunk
from hospital_ai.evaluation.adapter_foundation import EvaluationCaseContext, EvidenceResolutionError
from hospital_ai.evaluation.product_retrieval_adapter import ProductRetrievalAdapter
from hospital_ai.evaluation.runner import CaseObservation
from hospital_ai.services.graph_rag import (
    ExtractedRelation,
    extract_entities_and_relations_offline,
    find_related_entities,
    index_chunk_entities,
)
from hospital_ai.services.retrieval import RetrievalService


class ProductGraphAdapter:
    """Observe patient-scoped Graph RAG with verified, canonical source files."""

    def __init__(self, source_root: Path) -> None:
        self._retrieval_adapter = ProductRetrievalAdapter(source_root)

    async def evaluate(self, case: Any, context: EvaluationCaseContext) -> CaseObservation:
        if case.graph is None:
            raise EvidenceResolutionError("graph adapter requires a graph expectation")
        patient_id = context.patient_id or getattr(case, "patient_id", "")
        if patient_id not in context.actor.allowed_patient_ids:
            raise EvidenceResolutionError("evaluation actor is not authorized for the requested patient")

        locators = self._retrieval_adapter._unique_locators(
            case.allowed_evidence + case.forbidden_evidence + case.absence_checked_evidence
        )
        artifacts = tuple((locator, context.evidence_resolver.artifact_for(locator)) for locator in locators)
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        try:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            factory = async_sessionmaker(engine, expire_on_commit=False)
            async with factory() as session:
                await self._retrieval_adapter._materialize(
                    session,
                    context.actor.actor_id,
                    context.actor.role,
                    context.actor.allowed_patient_ids,
                    artifacts,
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

                graph = await find_related_entities(
                    session,
                    list(case.graph.required_nodes),
                    patient_id=patient_id,
                )
                evidence = await RetrievalService(session).get_chunks_by_ids(
                    list(graph.related_chunk_ids),
                    user_id=context.actor.actor_id,
                    patient_id=patient_id,
                )
                edge_ids = tuple(
                    sorted(
                        f"{relation.subject_label}|{relation.relation_type}|{relation.object_label}"
                        for relation in graph.relations
                    )
                )
                return CaseObservation(
                    retrieved_evidence=tuple(self._retrieval_adapter._runtime_evidence(item) for item in evidence),
                    graph_node_ids=tuple(entity.normalized_label for entity in graph.entities),
                    graph_edge_ids=edge_ids,
                    graph_path_ids=self._path_ids(graph.relations),
                )
        finally:
            await engine.dispose()

    @staticmethod
    def _path_ids(relations: list[ExtractedRelation]) -> tuple[str, ...]:
        """Return every observed direct or connected relationship path."""

        def edge_id(relation: ExtractedRelation) -> str:
            return f"{relation.subject_label}|{relation.relation_type}|{relation.object_label}"

        adjacency = defaultdict(list)
        for relation in relations:
            adjacency[relation.subject_label.casefold()].append(relation)

        paths: set[tuple[str, ...]] = set()

        def visit(path: tuple[ExtractedRelation, ...]) -> None:
            paths.add(tuple(edge_id(relation) for relation in path))
            tail = path[-1].object_label.casefold()
            for candidate in adjacency.get(tail, []):
                if candidate not in path:
                    visit(path + (candidate,))

        for relation in relations:
            visit((relation,))
        return tuple(">>".join(path) for path in sorted(paths))
