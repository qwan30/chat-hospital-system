import re
import time
from typing import Dict, List, Sequence, Set
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import ExternalServiceError, PermissionDeniedError
from hospital_ai.core.security import PATIENT_READ_SCOPES
from hospital_ai.db.models import AiQuery, RetrievedEvidence, User
from hospital_ai.schemas.chat import ChatResponse
from hospital_ai.schemas.documents import EvidenceRead
from hospital_ai.services.audit import AuditService
from hospital_ai.services.embeddings import EmbeddingService
from hospital_ai.services.permissions import PermissionService
from hospital_ai.services.retrieval import RetrievedChunk, RetrievalService

CITATION_PATTERN = re.compile(r"\[(E\d+)\]")
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
            )

        prompt = build_grounded_prompt(question, evidence)
        answer = await ChatGenerator(self.settings).generate(prompt)
        citation_ids = extract_citation_ids(answer)
        allowed_ids = {item.evidence_id for item in evidence}
        if not citation_ids or not citation_ids.issubset(allowed_ids):
            ai_query.status = "failed"
            ai_query.latency_ms = elapsed_ms(started)
            await AuditService(self.session).record(
                actor_user_id=user.id,
                action="chat.ask",
                object_type="ai_query",
                object_id=ai_query.id,
                patient_id=patient_id,
                outcome="failed",
                trace_id=trace_id,
                ip_address=ip_address,
                metadata={"reason": "invalid_citations", "citations": sorted(citation_ids)},
            )
            await self.session.commit()
            raise ExternalServiceError("Generated answer included invalid or missing citations.")

        cited_evidence = [item for item in evidence if item.evidence_id in citation_ids]
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
        ai_query.answer = answer
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
            metadata={"result": "completed", "evidence_count": len(evidence)},
        )
        await self.session.commit()

        return ChatResponse(
            query_id=ai_query.id,
            answer=answer,
            citations=[to_evidence_schema(item) for item in cited_evidence],
            confidence=confidence_from_score(evidence[0].score),
        )


class ChatGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate(self, prompt: str) -> str:
        if self.settings.chat_provider == "ollama":
            return await self._generate_ollama(prompt)
        return "Based on the authorized evidence, the record indicates relevant clinical details in [E1]."

    async def _generate_ollama(self, prompt: str) -> str:
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.settings.chat_model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a hospital knowledge assistant. Answer only from the evidence. "
                        "Cite every factual claim using evidence IDs like [E1]."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExternalServiceError("Local Ollama chat request failed.") from exc
        data = response.json()
        message = data.get("message") or {}
        content = message.get("content")
        if not content:
            raise ExternalServiceError("Ollama chat response did not include message content.")
        return str(content)


def build_grounded_prompt(question: str, evidence: Sequence[RetrievedChunk]) -> str:
    blocks = []
    for item in evidence:
        blocks.append(
            f"[{item.evidence_id}] Document: {item.document_title}; page: {item.page}\n{item.content}"
        )
    return (
        "Question:\n"
        f"{question}\n\n"
        "Authorized evidence:\n"
        + "\n\n".join(blocks)
        + "\n\nAnswer using only the evidence. Include citations like [E1]."
    )


def extract_citation_ids(answer: str) -> Set[str]:
    return set(CITATION_PATTERN.findall(answer))


def citations_are_valid(answer: str, allowed_evidence_ids: Set[str]) -> bool:
    citation_ids = extract_citation_ids(answer)
    return bool(citation_ids) and citation_ids.issubset(allowed_evidence_ids)


def confidence_from_score(score: float) -> str:
    if score >= 0.78:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def to_evidence_schema(item: RetrievedChunk) -> EvidenceRead:
    return EvidenceRead(
        evidence_id=item.evidence_id,
        document_id=item.document_id,
        document_title=item.document_title,
        page=item.page,
        chunk_id=item.chunk_id,
        score=item.score,
        metadata=dict(item.metadata),
    )
