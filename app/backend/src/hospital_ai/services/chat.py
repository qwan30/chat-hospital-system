from __future__ import annotations

import logging
import time
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.core.security import PATIENT_READ_SCOPES
from hospital_ai.db.models import AiQuery, ChatMessage, ChatThread, RetrievedEvidence, User
from hospital_ai.evaluation.observer import (
    EvaluationControls,
    EvaluationObserver,
    GraphCertificationError,
)
from hospital_ai.schemas.chat import ChatResponse, DrugWarningSchema
from hospital_ai.services.audit import AuditService

# Re-export shared utilities for backward compatibility
from hospital_ai.services.chat_utils import (
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

__all__ = [
    "CITATION_PATTERN",
    "MAX_HISTORY_MESSAGES",
    "ChatGenerator",
    "build_grounded_prompt",
    "build_stub_answer",
    "citations_are_valid",
    "confidence_from_score",
    "extract_citation_ids",
    "meets_evidence_threshold",
    "to_evidence_schema",
]
from hospital_ai.services.drug_check import DrugCheckService, DrugWarning
from hospital_ai.services.embeddings import EmbeddingService
from hospital_ai.services.graph_rag import extract_entities_and_relations_nlp, find_related_entities
from hospital_ai.services.guardrails import get_input_guardrail, get_output_guardrail
from hospital_ai.services.memory import MemoryService
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

SAFE_INJECTION_DETECTED_ANSWER = "Your request was blocked due to a detected security policy violation."

SAFE_PHI_LEAK_BLOCKED_ANSWER = (
    "The generated response was blocked because it contained sensitive information or uncited medical advice."
)

PERMISSION_DENIED_CHAT_ANSWER = (
    "Bạn không có quyền xem thông tin này. Giải thích: Yêu cầu của bạn liên quan đến "
    "dữ liệu nhạy cảm hoặc hồ sơ bệnh án nằm ngoài phạm vi phân quyền của tài khoản hiện tại."
)


class ChatService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def answer(
        self,
        *,
        user: User,
        patient_id: Optional[UUID],
        question: str,
        top_k: int,
        trace_id: str,
        ip_address: str,
        thread_id: Optional[UUID] = None,
        pipeline: str = "auto",
        evaluation_controls: Optional[EvaluationControls] = None,
        evaluation_observer: Optional[EvaluationObserver] = None,
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

        if patient_id:
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

        # --- Input Guardrail Check ---
        input_guard = get_input_guardrail()
        input_result = await input_guard.scan(question)

        if input_result.blocked:
            blocked_reason = input_result.reason
            ai_query.status = "denied"
            ai_query.answer = SAFE_INJECTION_DETECTED_ANSWER
            ai_query.latency_ms = elapsed_ms(started)
            await AuditService(self.session).record(
                actor_user_id=user.id,
                action="chat.ask",
                object_type="ai_query",
                object_id=ai_query.id,
                patient_id=patient_id,
                outcome="denied",
                trace_id=trace_id,
                ip_address=ip_address,
                metadata={"reason": "input_guardrail_blocked", "details": blocked_reason},
            )
            await self.session.commit()
            return ChatResponse(
                query_id=ai_query.id,
                answer=SAFE_INJECTION_DETECTED_ANSWER,
                citations=[],
                confidence="low",
                thread_id=thread_id,
                pipeline="blocked",
            )

        # Continue with question
        # Gather conversation history if thread is provided
        conversation_history = await self._get_conversation_history(thread_id, user.id, patient_id) if thread_id else []

        # Check for chit-chat query
        from hospital_ai.services.chat_utils import is_chitchat_query

        if is_chitchat_query(question):
            from hospital_ai.services.llm import LLMManager
            from hospital_ai.services.llm.base import LLMMessage

            manager = LLMManager(settings=self.settings)
            llm = manager.get()

            messages = [
                LLMMessage(
                    role="system",
                    content=(
                        "You are a friendly hospital knowledge assistant. "
                        "Since this is a greeting or general conversational query, "
                        "respond naturally and politely."
                    ),
                ),
                LLMMessage(role="user", content=question),
            ]

            t_gen_start = time.perf_counter()
            if self.settings.chat_provider == "stub":
                lower_q = question.lower()
                if "xin chào" in lower_q or "chào" in lower_q or "hello" in lower_q or "hi" in lower_q:
                    ans_text = "Xin chào! Tôi là trợ lý ảo HMS AI Copilot. Tôi có thể giúp gì cho bạn hôm nay?"
                elif "cảm ơn" in lower_q or "cám ơn" in lower_q or "thank" in lower_q or "thanks" in lower_q:
                    ans_text = "Không có gì! Nếu bạn cần thêm thông tin gì khác, cứ hỏi tôi nhé."
                else:
                    ans_text = "Tôi là HMS AI Copilot, trợ lý thông tin bệnh viện của bạn. Tôi có thể giúp gì cho bạn?"
            else:
                try:
                    response = await llm.generate(messages)
                    ans_text = response.text
                except Exception:
                    raise
            t_gen_ms = int((time.perf_counter() - t_gen_start) * 1000)

            output_result = await get_output_guardrail().scan(question, ans_text)
            if output_result.blocked:
                ai_query.status = "denied"
                ai_query.answer = SAFE_PHI_LEAK_BLOCKED_ANSWER
                ai_query.latency_ms = elapsed_ms(started)
                await AuditService(self.session).record(
                    actor_user_id=user.id,
                    action="chat.ask",
                    object_type="ai_query",
                    object_id=ai_query.id,
                    patient_id=patient_id,
                    outcome="denied",
                    trace_id=trace_id,
                    ip_address=ip_address,
                    metadata={"reason": "output_guardrail_blocked", "details": output_result.reason},
                )
                await self.session.commit()
                return ChatResponse(
                    query_id=ai_query.id,
                    answer=SAFE_PHI_LEAK_BLOCKED_ANSWER,
                    citations=[],
                    confidence="low",
                    thread_id=thread_id,
                    pipeline="blocked",
                )

            ai_query.status = "completed"
            ai_query.answer = ans_text
            ai_query.latency_ms = elapsed_ms(started)

            try:
                timing = TimingBreakdown(
                    total_ms=elapsed_ms(started),
                    retrieval_ms=0,
                    generation_ms=t_gen_ms,
                    embedding_ms=0,
                )
                await MetricsService(self.session).record_query_metrics(
                    query_id=ai_query.id,
                    user_id=user.id,
                    task_type="chitchat",
                    timing=timing,
                    documents_retrieved=0,
                    citations_count=0,
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
                    "evidence_count": 0,
                    "pipeline": "chitchat",
                },
            )
            await self.session.commit()

            if thread_id is not None:
                await MemoryService(self.session, self.settings).update_session_memory(
                    thread_id=thread_id,
                    patient_id=patient_id,
                    new_question=question,
                    new_answer=ans_text,
                    source_ids=[],
                )

            return ChatResponse(
                query_id=ai_query.id,
                answer=ans_text,
                citations=[],
                confidence="high",
                thread_id=thread_id,
                pipeline="chitchat",
            )

        # ── Timing: embedding ────────────────────────────────────────
        t_embed_start = time.perf_counter()

        hyde_text = question
        if self.settings.enable_hyde:
            from hospital_ai.services.llm import LLMManager
            from hospital_ai.services.llm.base import LLMMessage

            manager = LLMManager(settings=self.settings)
            llm = manager.get()
            messages = [
                LLMMessage(
                    role="system",
                    content=(
                        "You are a medical assistant. Provide a brief, "
                        "authoritative hypothetical answer to the following question. "
                        "Do not include disclaimers, just provide the expected hypothetical answer content. "
                        "Focus on keywords and relevant entities."
                    ),
                ),
                LLMMessage(role="user", content=question),
            ]
            try:
                response = await llm.generate(messages)
                hyde_text = f"{question}\n{response.text}"
            except Exception as e:
                logger.warning("HyDE generation failed: %s", e)

        query_embedding = await EmbeddingService(self.settings).embed(hyde_text)
        t_embed_ms = int((time.perf_counter() - t_embed_start) * 1000)

        # ── Timing: retrieval ────────────────────────────────────────
        t_retrieval_start = time.perf_counter()
        retrieval_svc = RetrievalService(self.session, evaluation_observer)
        retrieval_mode = (
            "hybrid"
            if evaluation_controls is not None and evaluation_controls.mode != "rag_off"
            else self.settings.retrieval_mode
        )

        if getattr(self.settings, "ab_test_retrieval", False):
            import random

            retrieval_mode = "hybrid" if random.random() > 0.5 else "vector"

        evidence = []
        rag_enabled = evaluation_controls is None or evaluation_controls.mode != "rag_off"
        if rag_enabled and retrieval_mode in ("bm25", "hybrid"):
            evidence = await retrieval_svc.hybrid_search(
                user_id=user.id,
                patient_id=patient_id,
                query_embedding=query_embedding,
                query_text=question,
                top_k=top_k,
                retrieval_mode=retrieval_mode,
            )
        elif rag_enabled:
            evidence = await retrieval_svc.search(
                user_id=user.id,
                patient_id=patient_id,
                query_embedding=query_embedding,
                top_k=top_k,
            )

        # ── Graph RAG: boost evidence with entity relationships ──────
        graph_enabled = evaluation_controls is None or evaluation_controls.mode == "hybrid_graph_on"
        try:
            if graph_enabled and patient_id:
                if evaluation_observer is not None:
                    evaluation_observer.record_graph_execution()
                query_entities, _ = await extract_entities_and_relations_nlp(question)
                if query_entities:
                    entity_names = [e.normalized_label for e in query_entities]
                    graph_ctx = await find_related_entities(
                        self.session, entity_names, max_hops=2, patient_id=patient_id
                    )
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
                            graph_evidence = [
                                RetrievedChunk(
                                    evidence_id=ge.evidence_id,
                                    document_id=ge.document_id,
                                    document_title=ge.document_title,
                                    page=ge.page,
                                    chunk_id=ge.chunk_id,
                                    score=ge.score,
                                    content=ge.content,
                                    metadata={**ge.metadata, "retrieval_method": "graph"},
                                )
                                for ge in graph_evidence
                            ]
                            if evaluation_observer is not None:
                                evaluation_observer.record_graph_expanded(graph_evidence)
                            evidence.extend(graph_evidence)
                            evidence = evidence[:top_k]
        except Exception as error:
            if evaluation_controls is not None and evaluation_controls.graph_required:
                raise GraphCertificationError("Graph traversal failed during required certification") from error
            logger.warning("Graph RAG enrichment skipped", exc_info=True)

        t_retrieval_ms = int((time.perf_counter() - t_retrieval_start) * 1000)

        if not evidence or not meets_evidence_threshold(evidence[0], retrieval_mode, self.settings.evidence_threshold):
            is_blocked = retrieval_svc.blocked_chunk_count > 0
            answer_text = PERMISSION_DENIED_CHAT_ANSWER if is_blocked else SAFE_NO_EVIDENCE_ANSWER
            result_status = "denied" if is_blocked else "no_evidence"
            outcome = "denied" if is_blocked else "allowed"

            ai_query.status = result_status
            ai_query.answer = answer_text
            ai_query.latency_ms = elapsed_ms(started)
            await AuditService(self.session).record(
                actor_user_id=user.id,
                action="chat.ask",
                object_type="ai_query",
                object_id=ai_query.id,
                patient_id=patient_id,
                outcome=outcome,
                trace_id=trace_id,
                ip_address=ip_address,
                metadata={"result": result_status},
            )
            await self.session.commit()
            return ChatResponse(
                query_id=ai_query.id,
                answer=answer_text,
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
            if evaluation_observer is None:
                reasoning_result = await self._run_pipeline(selected_pipeline, question, evidence, conversation_history)
            else:
                reasoning_result = await self._run_pipeline(
                    selected_pipeline,
                    question,
                    evidence,
                    conversation_history,
                    evaluation_observer=evaluation_observer,
                )
        except Exception:
            ai_query.status = "failed"
            ai_query.latency_ms = elapsed_ms(started)
            await self.session.commit()
            raise
        t_gen_ms = int((time.perf_counter() - t_gen_start) * 1000)

        # --- Output Guardrail Check ---
        output_guard = get_output_guardrail()
        output_result = await output_guard.scan(question, reasoning_result.answer)

        if output_result.blocked:
            blocked_reason = output_result.reason
            ai_query.status = "denied"
            ai_query.answer = SAFE_PHI_LEAK_BLOCKED_ANSWER
            ai_query.latency_ms = elapsed_ms(started)
            await AuditService(self.session).record(
                actor_user_id=user.id,
                action="chat.ask",
                object_type="ai_query",
                object_id=ai_query.id,
                patient_id=patient_id,
                outcome="denied",
                trace_id=trace_id,
                ip_address=ip_address,
                metadata={"reason": "output_guardrail_blocked", "details": blocked_reason},
            )
            await self.session.commit()
            return ChatResponse(
                query_id=ai_query.id,
                answer=SAFE_PHI_LEAK_BLOCKED_ANSWER,
                citations=[],
                confidence="low",
                thread_id=thread_id,
                pipeline="blocked",
            )

        # F-RAG-005: defense-in-depth citation validation.  Each pipeline
        # already enforces this internally, but a service-level re-check
        # makes it impossible for a future pipeline (or refactor) to skip
        # the contract.
        allowed_evidence_ids = {item.evidence_id for item in evidence}
        answer_citation_ids = extract_citation_ids(reasoning_result.answer)
        if not answer_citation_ids or not answer_citation_ids.issubset(allowed_evidence_ids):
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
        cited_evidence = [item for item in evidence if item.evidence_id in answer_citation_ids]
        if evaluation_observer is not None:
            evaluation_observer.record_cited_chunks(cited_evidence)
        for index, item in enumerate(cited_evidence, start=1):
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

        if thread_id is not None:
            source_ids = [str(item.document_id) for item in evidence]
            await MemoryService(self.session, self.settings).update_session_memory(
                thread_id=thread_id,
                patient_id=patient_id,
                new_question=question,
                new_answer=reasoning_result.answer,
                source_ids=source_ids,
            )

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

    async def _get_conversation_history(
        self, thread_id: UUID, user_id: UUID, request_patient_id: Optional[UUID]
    ) -> list[dict[str, str]]:
        """Fetch recent messages from a chat thread for conversation context."""
        thread = await self.session.get(ChatThread, thread_id)
        if not thread:
            return []

        if thread.owner_user_id != user_id:
            from hospital_ai.db.models import ChatThreadParticipant

            participant = await self.session.execute(
                select(ChatThreadParticipant).where(
                    ChatThreadParticipant.thread_id == thread_id,
                    ChatThreadParticipant.user_id == user_id,
                )
            )
            if not participant.scalar_one_or_none():
                raise PermissionDeniedError("User is not authorized for this thread.")

        if thread.patient_id and thread.patient_id != request_patient_id:
            raise PermissionDeniedError("Thread patient mismatch.")
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
        evaluation_observer: Optional[EvaluationObserver] = None,
    ) -> ReasoningResult:
        """Run the selected reasoning pipeline."""
        if pipeline_name == "patient_summary":
            return await PatientSummaryPipeline(self.settings).run(
                patient_name="Patient",
                evidence=evidence,
                evaluation_observer=evaluation_observer,
            )
        elif pipeline_name == "decompose":
            return await DecomposeQAPipeline(self.settings).run(
                question=question,
                evidence=evidence,
                conversation_history=conversation_history,
                evaluation_observer=evaluation_observer,
            )
        else:
            return await SimpleQAPipeline(self.settings).run(
                question=question,
                evidence=evidence,
                conversation_history=conversation_history,
                evaluation_observer=evaluation_observer,
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
