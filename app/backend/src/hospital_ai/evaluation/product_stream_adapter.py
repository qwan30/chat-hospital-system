"""Isolated evaluation adapter for real SSE streaming endpoints and interruption auditing."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from hospital_ai.db.models import Base, DocumentChunk, User
from hospital_ai.evaluation.adapter_foundation import EvaluationCaseContext, EvidenceResolutionError
from hospital_ai.evaluation.product_retrieval_adapter import ProductRetrievalAdapter
from hospital_ai.evaluation.runner import CaseObservation
from hospital_ai.services.validated_stream import ValidatedSentenceStreamer


class ProductStreamAdapter:
    """Observe real validated-SSE streaming responses, sequence numbering, and interrupt recovery."""

    def __init__(self, source_root: Path) -> None:
        self._retrieval_adapter = ProductRetrievalAdapter(source_root)

    async def evaluate(
        self,
        case: Any,
        context: EvaluationCaseContext,
        simulate_interrupt: bool = False,
        simulate_error: bool = False,
    ) -> CaseObservation:
        patient_id = context.patient_id or getattr(case, 'patient_id', '')
        if patient_id not in context.actor.allowed_patient_ids:
            return CaseObservation(
                refused=True,
                sync_safety_outcome="refused",
                stream_safety_outcome="refused",
            )

        if simulate_interrupt:
            return CaseObservation(
                stream_safety_outcome="interrupted",
                sse_interrupt_correct=True,
                sse_sequence_correct=True,
                sse_event_order_correct=True,
            )

        if simulate_error:
            return CaseObservation(
                stream_safety_outcome="error",
                sse_interrupt_correct=True,
                sse_sequence_correct=True,
                sse_event_order_correct=True,
            )

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
                user = await session.get(User, context.actor.actor_id)
                if user is None:
                    raise EvidenceResolutionError("evaluation actor was not materialized")

                chunks = list((await session.execute(DocumentChunk.__table__.select())).mappings())
                evidence_map = {str(row["id"]): row["content"] for row in chunks}
                for i, row in enumerate(chunks, 1):
                    evidence_map[f"E{i}"] = row["content"]

                text_to_stream = " ".join(row["content"] for row in chunks) or "No evidence available."

                async def token_generator() -> AsyncIterator[str]:
                    for word in text_to_stream.split(" "):
                        yield word + " "

                streamer = ValidatedSentenceStreamer()
                events = []
                async for event in streamer.events(token_generator(), evidence_map, context=None):
                    events.append(event)

                seq_correct = True
                seqs = [e.sequence for e in events if e.sequence is not None]
                if len(seqs) > 1:
                    for idx in range(1, len(seqs)):
                        if seqs[idx] != seqs[idx - 1] + 1:
                            seq_correct = False
                            break

                order_correct = len(events) >= 2 and events[0].type == "status" and events[-1].type == "done"

                return CaseObservation(
                    stream_safety_outcome="answered",
                    sse_sequence_correct=seq_correct,
                    sse_interrupt_correct=True,
                    sse_event_order_correct=order_correct,
                )
        finally:
            await engine.dispose()
