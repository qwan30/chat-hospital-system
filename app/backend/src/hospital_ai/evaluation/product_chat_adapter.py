"""Isolated deterministic adapter for the non-streaming product chat path.

This adapter uses the real ``ChatService`` with the built-in stub generator,
deterministic embeddings, a disposable SQLite schema, and the internal
evaluation observer.  It deliberately reports SSE as ``not_evaluated`` rather
than claiming transport parity from a non-streaming invocation.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.db.models import Base, DocumentChunk, User
from hospital_ai.evaluation.adapter_foundation import (
    EvaluationCaseContext,
    EvidenceResolutionError,
    RuntimeEvidenceChunk,
)
from hospital_ai.evaluation.benchmark import EvalCaseV2
from hospital_ai.evaluation.observer import EvaluationControls, InMemoryEvaluationObserver
from hospital_ai.evaluation.product_retrieval_adapter import ProductRetrievalAdapter
from hospital_ai.evaluation.runner import CaseObservation
from hospital_ai.services.chat import (
    PERMISSION_DENIED_CHAT_ANSWER,
    SAFE_INJECTION_DETECTED_ANSWER,
    SAFE_NO_EVIDENCE_ANSWER,
    SAFE_PHI_LEAK_BLOCKED_ANSWER,
    ChatService,
)


class ProductChatAdapter:
    """Run source-backed, authorization-aware non-streaming chat evaluation."""

    def __init__(self, source_root: Path) -> None:
        self._retrieval_adapter = ProductRetrievalAdapter(source_root)

    async def evaluate(self, case: EvalCaseV2, context: EvaluationCaseContext) -> CaseObservation:
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
                chunks = list((await session.execute(DocumentChunk.__table__.select())).mappings())
                bindings = {row["id"]: row["id"] for row in chunks}
                observer = InMemoryEvaluationObserver(logical_evidence_by_chunk=bindings, require_indexed=True)
                user = await session.get(User, context.actor.actor_id)
                if user is None:
                    raise EvidenceResolutionError("evaluation actor was not materialized")
                try:
                    response = await ChatService(session, self._settings(len(locators))).answer(
                        user=user,
                        patient_id=case.patient_id,
                        question=case.question,
                        top_k=max(1, len(locators)),
                        trace_id=f"evaluation-{case.case_id}",
                        ip_address="127.0.0.1",
                        pipeline="simple",
                        evaluation_controls=EvaluationControls.hybrid_graph_off(case.case_id),
                        evaluation_observer=observer,
                    )
                except PermissionDeniedError:
                    return CaseObservation(
                        refused=True,
                        sync_safety_outcome="refused",
                        stream_safety_outcome="not_evaluated",
                        answer_text=PERMISSION_DENIED_CHAT_ANSWER,
                    )
                snapshot = observer.snapshot()
                retrieved = await self._runtime_evidence(session, snapshot.authorized_chunk_ids)
                cited = await self._runtime_evidence(session, snapshot.cited_chunk_ids)
                refused = response.answer in {
                    SAFE_NO_EVIDENCE_ANSWER,
                    SAFE_INJECTION_DETECTED_ANSWER,
                    SAFE_PHI_LEAK_BLOCKED_ANSWER,
                    PERMISSION_DENIED_CHAT_ANSWER,
                }
                answer = response.answer.casefold()
                return CaseObservation(
                    retrieved_evidence=retrieved,
                    cited_evidence=cited,
                    covered_fact_ids=tuple(
                        fact.fact_id
                        for fact in case.expected_facts
                        if all(term.casefold() in answer for term in fact.verification_terms)
                    ),
                    refused=refused,
                    sync_safety_outcome="refused" if refused else "answered",
                    stream_safety_outcome="not_evaluated",
                    answer_text=response.answer,
                )
        finally:
            await engine.dispose()

    @staticmethod
    def _settings(top_k: int) -> Settings:
        return Settings(
            chat_provider="stub",
            embedding_provider="deterministic",
            retrieval_mode="hybrid",
            retrieval_top_k=top_k,
            evidence_threshold=0.0,
            enable_hyde=False,
            disable_guardrails=True,
        )

    async def _runtime_evidence(self, session, chunk_ids: tuple) -> tuple[RuntimeEvidenceChunk, ...]:
        values = []
        for chunk_id in chunk_ids:
            chunk = await session.get(DocumentChunk, chunk_id)
            if chunk is None:
                raise EvidenceResolutionError("chat observer reported a missing indexed chunk")
            metadata = chunk.meta
            try:
                values.append(
                    RuntimeEvidenceChunk(
                        runtime_chunk_id=str(chunk.id),
                        source_path=metadata["source_path"],
                        source_sha256=metadata["source_sha256"],
                        patient_id=metadata.get("patient_id"),
                        page_number=metadata.get("page_number"),
                        row_number=metadata.get("row_number"),
                        record_id=metadata.get("record_id"),
                    )
                )
            except (KeyError, TypeError, ValueError) as error:
                raise EvidenceResolutionError("chat evidence lacks exact source provenance") from error
        return tuple(values)
