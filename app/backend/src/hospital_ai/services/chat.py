import time
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import ExternalServiceError, PermissionDeniedError
from hospital_ai.core.security import PATIENT_READ_SCOPES
from hospital_ai.db.models import AiQuery, ChatMessage, ChatThread, RetrievedEvidence, User
from hospital_ai.schemas.chat import ChatResponse
from hospital_ai.schemas.documents import EvidenceRead
from hospital_ai.services.audit import AuditService
from hospital_ai.services.embeddings import EmbeddingService
from hospital_ai.services.permissions import PermissionService
from hospital_ai.services.reasoning import (
    DecomposeQAPipeline,
    PatientSummaryPipeline,
    ReasoningResult,
    SimpleQAPipeline,
)
from hospital_ai.services.retrieval import RetrievedChunk, RetrievalService

# Re-export shared utilities for backward compatibility
from hospital_ai.services.chat_utils import (  # noqa: F401
    ChatGenerator,
    build_grounded_prompt,
    build_stub_answer,
    citations_are_valid,
    confidence_from_score,
    extract_citation_ids,
    to_evidence_schema,
    CITATION_PATTERN,
    MAX_HISTORY_MESSAGES,
)

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

        query_embedding = await EmbeddingService(self.settings).embed(question)
        evidence = await RetrievalService(self.session).search(
            user_id=user.id,
            patient_id=patient_id,
            query_embedding=query_embedding,
            top_k=top_k,
        )

        if not evidence or evidence[0].score < self.settings.evidence_threshold:
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

        # Select and run reasoning pipeline
        selected_pipeline = _select_pipeline(pipeline, question)
        try:
            reasoning_result = await self._run_pipeline(
                selected_pipeline, question, evidence, conversation_history
            )
        except Exception:
            ai_query.status = "failed"
            ai_query.latency_ms = elapsed_ms(started)
            await self.session.commit()
            raise

        # Store retrieved evidence records
        for index, item in enumerate(evidence, start=1):
            self.session.add(
                RetrievedEvidence(
                    ai_query_id=ai_query.id,
                    chunk_id=item.chunk_id,
                    rank=index,
                    score=item.score,
                    citation_label=item.evidence_id,
                )
            )

        ai_query.status = "completed"
        ai_query.answer = reasoning_result.answer
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
            metadata={
                "result": "completed",
                "evidence_count": len(evidence),
                "pipeline": reasoning_result.pipeline,
            },
        )
        await self.session.commit()

        return ChatResponse(
            query_id=ai_query.id,
            answer=reasoning_result.answer,
            citations=reasoning_result.citations,
            confidence=reasoning_result.confidence,
            disclaimer=reasoning_result.disclaimer,
            thread_id=thread_id,
            pipeline=reasoning_result.pipeline,
        )

    async def _get_conversation_history(self, thread_id: UUID) -> List[Dict[str, str]]:
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
            history.append({
                "role": msg.role,
                "content": msg.content,
            })
        return history

    async def _run_pipeline(
        self,
        pipeline_name: str,
        question: str,
        evidence: List[RetrievedChunk],
        conversation_history: List[Dict[str, str]],
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
