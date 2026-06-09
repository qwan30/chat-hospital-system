import logging
import time
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.core.security import PATIENT_READ_SCOPES
from hospital_ai.db.models import AiQuery, ChatMessage, RetrievedEvidence, User
from hospital_ai.schemas.chat import ChatResponse, DrugWarningSchema
from hospital_ai.services.audit import AuditService

# Re-export shared utilities for backward compatibility
from hospital_ai.services.chat_utils import (  # noqa: F401
    CITATION_PATTERN,
    MAX_HISTORY_MESSAGES,
    ChatGenerator,
    build_grounded_prompt,
    build_stub_answer,
    citations_are_valid,
    confidence_from_score,
    extract_citation_ids,
    meets_evidence_threshold,
    to_evidence_schema,
)
from hospital_ai.services.drug_check import DrugCheckService, DrugWarning
from hospital_ai.services.embeddings import EmbeddingService
from hospital_ai.services.graph_rag import extract_entities, find_related_entities
from hospital_ai.services.metrics import MetricsService, TimingBreakdown
from hospital_ai.services.permissions import PermissionService
from hospital_ai.services.reasoning import (
    DecomposeQAPipeline,
    PatientSummaryPipeline,
    ReasoningResult,
    SimpleQAPipeline,
)
from hospital_ai.services.retrieval import RetrievalService, RetrievedChunk

logger = logging.getLogger(__name__)

SAFE_NO_EVIDENCE_ANSWER = (
    "I could not find authorized evidence for this question. "
    "Please review the patient record directly or ask a records user to index the relevant document."
)


class ChatService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def answer(
        self,
        *,
        user: User,
        patient_id: UUID,
        question: str,
        top_k: int,
        trace_id: str,
        ip_address: str,
        thread_id: Optional[UUID] = None,
        pipeline: str = "auto",
    ) -> ChatResponse:
        started = time.perf_counter()
        ai_query = AiQuery(
            user_id=user.id,
            patient_id=patient_id,
            question=question,
            status="received",
            model=self.settings.chat_model if self.settings.chat_provider == "ollama" else "stub",
        )
        self.session.add(ai_query)
        await self.session.flush()

        has_scope = await PermissionService(self.session).has_patient_scope(
            user_id=user.id,
            patient_id=patient_id,
            accepted_scopes=PATIENT_READ_SCOPES,
        )
        if not has_scope:
            ai_query.status = "denied"
            await AuditService(self.session).record(
                actor_user_id=user.id,
                action="chat.ask",
                object_type="ai_query",
                object_id=ai_query.id,
                patient_id=patient_id,
                outcome="denied",
                trace_id=trace_id,
                ip_address=ip_address,
                metadata={"reason": "missing_patient_read_scope"},
            )
            await self.session.commit()
            raise PermissionDeniedError("User is not authorized for this patient.")

        # Gather conversation history if thread is provided
        conversation_history = await self._get_conversation_history(thread_id) if thread_id else []

        # ── Timing: embedding ────────────────────────────────────────
        t_embed_start = time.perf_counter()
        query_embedding = await EmbeddingService(self.settings).embed(question)
        t_embed_ms = int((time.perf_counter() - t_embed_start) * 1000)

        # ── Timing: retrieval ────────────────────────────────────────
        t_retrieval_start = time.perf_counter()
        retrieval_svc = RetrievalService(self.session)
        retrieval_mode = self.settings.retrieval_mode

        if retrieval_mode in ("bm25", "hybrid"):
            evidence = await retrieval_svc.hybrid_search(
                user_id=user.id,
                patient_id=patient_id,
                query_embedding=query_embedding,
                query_text=question,
                top_k=top_k,
                retrieval_mode=retrieval_mode,
            )
        else:
            evidence = await retrieval_svc.search(
                user_id=user.id,
                patient_id=patient_id,
                query_embedding=query_embedding,
                top_k=top_k,
            )

        # ── Graph RAG: boost evidence with entity relationships ──────
        try:
            query_entities = extract_entities(question)
            if query_entities:
                entity_names = [e.name for e in query_entities]
                graph_ctx = await find_related_entities(self.session, entity_names, max_hops=2, patient_id=patient_id)
                if graph_ctx.related_chunk_ids:
                    existing_ids = {e.chunk_id for e in evidence}
                    graph_only_ids = graph_ctx.related_chunk_ids - existing_ids
                    # Add graph-discovered chunks to evidence (with lower score)
                    if graph_only_ids:
                        graph_evidence = await retrieval_svc.get_chunks_by_ids(
                            list(graph_only_ids)[:top_k],
                            user_id=user.id,
                            patient_id=patient_id,
                        )
                        for ge in graph_evidence:
                            ge.metadata["retrieval_method"] = "graph"
                        evidence.extend(graph_evidence)
        except Exception:
            logger.warning("Graph RAG enrichment skipped", exc_info=True)

        t_retrieval_ms = int((time.perf_counter() - t_retrieval_start) * 1000)

        if not evidence or not meets_evidence_threshold(evidence[0], retrieval_mode, self.settings.evidence_threshold):
            ai_query.status = "no_evidence"
            ai_query.answer = SAFE_NO_EVIDENCE_ANSWER
            ai_query.latency_ms = elapsed_ms(started)
            await AuditService(self.session).record(
                actor_user_id=user.id,
                action="chat.ask",
                object_type="ai_query",
                object_id=ai_query.id,
                patient_id=patient_id,
                outcome="allowed",
                trace_id=trace_id,
                ip_address=ip_address,
                metadata={"result": "no_evidence"},
            )
            await self.session.commit()
            return ChatResponse(
                query_id=ai_query.id,
                answer=SAFE_NO_EVIDENCE_ANSWER,
                citations=[],
                confidence="low",
                thread_id=thread_id,
                pipeline="simple_qa",
            )

        # ── Drug interaction check ───────────────────────────────────
        drug_warnings: list[DrugWarning] = []
        try:
            drug_warnings = await DrugCheckService(self.session).check_interactions(
                query_text=question,
                patient_id=patient_id,
            )
        except Exception:
            logger.warning("Drug interaction check skipped", exc_info=True)

        # ── Timing: generation ───────────────────────────────────────
        selected_pipeline = _select_pipeline(pipeline, question)
        t_gen_start = time.perf_counter()
        try:
            reasoning_result = await self._run_pipeline(selected_pipeline, question, evidence, conversation_history)
        except Exception:
            ai_query.status = "failed"
            ai_query.latency_ms = elapsed_ms(started)
            await self.session.commit()
            raise
        t_gen_ms = int((time.perf_counter() - t_gen_start) * 1000)

        # F-RAG-005: defense-in-depth citation validation.  Each pipeline
        # already enforces this internally, but a service-level re-check
        # makes it impossible for a future pipeline (or refactor) to skip
        # the contract.
        allowed_evidence_ids = {item.evidence_id for item in evidence}
        answer_citation_ids = extract_citation_ids(reasoning_result.answer)
        if answer_citation_ids and not answer_citation_ids.issubset(allowed_evidence_ids):
            logger.warning(
                "Answer rejected at service boundary: invalid_citation query_id=%s allowed=%s answer_cited=%s",
                ai_query.id,
                sorted(allowed_evidence_ids),
                sorted(answer_citation_ids),
            )
            ai_query.status = "failed"
            ai_query.latency_ms = elapsed_ms(started)
            await self.session.commit()
            from hospital_ai.core.errors import ExternalServiceError

            raise ExternalServiceError("Generated answer contains citations not in the retrieved evidence.")

        # Store retrieved evidence records with trace data
        for index, item in enumerate(evidence, start=1):
            retrieval_method = item.metadata.get("retrieval_method", retrieval_mode)
            rerank_method = item.metadata.get("rerank_method", "")
            rerank_score_val = item.metadata.get("rerank_original_score")
            self.session.add(
                RetrievedEvidence(
                    ai_query_id=ai_query.id,
                    chunk_id=item.chunk_id,
                    rank=index,
                    score=item.score,
                    citation_label=item.evidence_id,
                    rerank_score=float(rerank_score_val) if rerank_score_val is not None else None,
                    retrieval_method=retrieval_method,
                    rerank_method=rerank_method or None,
                )
            )

        ai_query.status = "completed"
        ai_query.answer = reasoning_result.answer
        ai_query.latency_ms = elapsed_ms(started)

        # ── Record impact metrics ────────────────────────────────────
        try:
            timing = TimingBreakdown(
                total_ms=elapsed_ms(started),
                retrieval_ms=t_retrieval_ms,
                generation_ms=t_gen_ms,
                embedding_ms=t_embed_ms,
            )
            await MetricsService(self.session).record_query_metrics(
                query_id=ai_query.id,
                user_id=user.id,
                task_type=selected_pipeline,
                timing=timing,
                documents_retrieved=len(evidence),
                citations_count=len(reasoning_result.citations),
                thread_id=thread_id,
            )
        except Exception:
            logger.warning("Metrics recording failed", exc_info=True)

        await AuditService(self.session).record(
            actor_user_id=user.id,
            action="chat.ask",
            object_type="ai_query",
            object_id=ai_query.id,
            patient_id=patient_id,
            outcome="allowed",
            trace_id=trace_id,
            ip_address=ip_address,
            metadata={
                "result": "completed",
                "evidence_count": len(evidence),
                "pipeline": reasoning_result.pipeline,
                "drug_warnings": len(drug_warnings),
            },
        )
        await self.session.commit()

        # Convert drug warnings to schema
        warning_schemas = [
            DrugWarningSchema(
                drug_name=w.drug_name,
                interacting_entity=w.interacting_entity,
                interaction_type=w.interaction_type,
                severity=w.severity,
                evidence_chunk_id=w.evidence_chunk_id,
                message=w.message,
            )
            for w in drug_warnings
        ]

        return ChatResponse(
            query_id=ai_query.id,
            answer=reasoning_result.answer,
            citations=reasoning_result.citations,
            confidence=reasoning_result.confidence,
            disclaimer=reasoning_result.disclaimer,
            thread_id=thread_id,
            pipeline=reasoning_result.pipeline,
            warnings=warning_schemas,
        )

    async def _get_conversation_history(self, thread_id: UUID) -> list[dict[str, str]]:
        """Fetch recent messages from a chat thread for conversation context."""
        result = await self.session.execute(
            select(ChatMessage)
            .where(
                ChatMessage.thread_id == thread_id,
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(MAX_HISTORY_MESSAGES)
        )
        messages = list(result.scalars().all())
        messages.reverse()  # oldest first

        history = []
        for msg in messages:
            history.append(
                {
                    "role": msg.role,
                    "content": msg.content,
                }
            )
        return history

    async def _run_pipeline(
        self,
        pipeline_name: str,
        question: str,
        evidence: list[RetrievedChunk],
        conversation_history: list[dict[str, str]],
    ) -> ReasoningResult:
        """Run the selected reasoning pipeline."""
        if pipeline_name == "patient_summary":
            return await PatientSummaryPipeline(self.settings).run(
                patient_name="Patient",
                evidence=evidence,
            )
        elif pipeline_name == "decompose":
            return await DecomposeQAPipeline(self.settings).run(
                question=question,
                evidence=evidence,
                conversation_history=conversation_history,
            )
        else:
            return await SimpleQAPipeline(self.settings).run(
                question=question,
                evidence=evidence,
                conversation_history=conversation_history,
            )


def _select_pipeline(requested: str, question: str) -> str:
    """Auto-detect the best pipeline if 'auto' is requested."""
    if requested != "auto":
        return requested

    q = question.lower()
    summary_indicators = ["summarize", "summary", "overview", "all results", "patient summary"]
    if any(indicator in q for indicator in summary_indicators):
        return "patient_summary"

    complex_indicators = [" and ", " also ", " as well as ", " what are ", " compare "]
    if any(indicator in q for indicator in complex_indicators) and len(question) > 60:
        return "decompose"

    return "simple"


def elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
