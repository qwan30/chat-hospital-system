"""Reasoning pipelines inspired by kotaemon's ktem/reasoning module.

Provides multiple strategies for answering questions:
- SimpleQAPipeline: retrieve → generate (default)
- DecomposeQAPipeline: break complex question into sub-questions
- PatientSummaryPipeline: generate structured patient summaries
"""

import re
import uuid
from dataclasses import dataclass
from typing import Optional

from hospital_ai.core.config import Settings
from hospital_ai.evaluation.observer import EvaluationObserver
from hospital_ai.schemas.documents import EvidenceRead
from hospital_ai.services.chat_utils import (
    ChatGenerator,
    build_grounded_prompt,
    confidence_from_score,
    extract_citation_ids,
)
from hospital_ai.services.reranking import RerankerService
from hospital_ai.services.retrieval import RetrievedChunk

PATIENT_SUMMARY_SYSTEM_PROMPT = """You are a clinical summarization assistant.
Given retrieved evidence chunks about a patient, produce a structured summary
covering: demographics, active conditions, recent encounters, current medications,
and recent lab results. Each claim must cite its source with [E1], [E2] etc.
If a category has no evidence, state "No evidence available for this section."
Always end with: "Clinical staff must verify all information before making decisions."
"""

DECOMPOSE_SYSTEM_PROMPT = """You are a question decomposition assistant.
Break the following complex clinical question into 2-4 simpler sub-questions
that can each be answered independently using hospital knowledge retrieval.
Return each sub-question on its own line, prefixed with "Q: ".
"""

NO_EVIDENCE_ANSWER = (
    "I could not find sufficient evidence to answer this question. "
    "Please refine your query or contact the relevant department."
)

DISCLAIMER = "AI-assisted retrieval; clinical staff must verify before making decisions."


@dataclass(frozen=True)
class ReasoningResult:
    answer: str
    citations: list[EvidenceRead]
    confidence: str
    disclaimer: str
    pipeline: str
    sub_questions: Optional[list[str]] = None


class SimpleQAPipeline:
    """Standard retrieve → rerank → generate pipeline."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.reranker = RerankerService(settings)

    async def run(
        self,
        *,
        question: str,
        evidence: list[RetrievedChunk],
        conversation_history: Optional[list[dict[str, str]]] = None,
        evaluation_observer: Optional[EvaluationObserver] = None,
    ) -> ReasoningResult:
        reranked = self.reranker.rerank(question, evidence, top_k=self.settings.retrieval_top_k)

        if not reranked:
            return ReasoningResult(
                answer=NO_EVIDENCE_ANSWER,
                citations=[],
                confidence="low",
                disclaimer=DISCLAIMER,
                pipeline="simple_qa",
            )

        if evaluation_observer is not None:
            evaluation_observer.record_selected_context(reranked)
            evaluation_observer.record_generator_context(reranked)
        prompt = build_grounded_prompt(question, reranked, conversation_history)
        answer = await ChatGenerator(self.settings).generate(prompt)
        citation_ids = extract_citation_ids(answer)
        allowed_ids = {item.evidence_id for item in reranked}

        # Validate citations — reject answers that cite non-existent evidence
        if citation_ids and not citation_ids.issubset(allowed_ids):
            from hospital_ai.core.errors import ExternalServiceError

            raise ExternalServiceError("Generated answer contains citations not in the retrieved evidence.")

        cited = [c for c in reranked if c.evidence_id in (citation_ids & allowed_ids)]

        return ReasoningResult(
            answer=answer,
            citations=[_to_evidence_schema(c) for c in cited],
            confidence=confidence_from_score(reranked[0].score) if reranked else "low",
            disclaimer=DISCLAIMER,
            pipeline="simple_qa",
        )


class DecomposeQAPipeline:
    """Break a complex question into sub-questions, retrieve for each, then synthesize."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.simple = SimpleQAPipeline(settings)

    async def run(
        self,
        *,
        question: str,
        evidence: list[RetrievedChunk],
        conversation_history: Optional[list[dict[str, str]]] = None,
        evaluation_observer: Optional[EvaluationObserver] = None,
    ) -> ReasoningResult:
        sub_questions = _decompose_question(question)

        if len(sub_questions) <= 1:
            result = await self.simple.run(
                question=question,
                evidence=evidence,
                conversation_history=conversation_history,
                evaluation_observer=evaluation_observer,
            )
            return ReasoningResult(
                answer=result.answer,
                citations=result.citations,
                confidence=result.confidence,
                disclaimer=result.disclaimer,
                pipeline="decompose_qa",
                sub_questions=sub_questions,
            )

        # For each sub-question, score the evidence and pick best matches.
        all_cited: list[RetrievedChunk] = []
        reranker = RerankerService(self.settings)
        for sub_q in sub_questions:
            reranked = reranker.rerank(sub_q, evidence, top_k=3)
            all_cited.extend(reranked)

        # Deduplicate by chunk_id.
        seen: set[uuid.UUID] = set()
        unique_evidence: list[RetrievedChunk] = []
        for chunk in all_cited:
            if chunk.chunk_id not in seen:
                seen.add(chunk.chunk_id)
                unique_evidence.append(chunk)

        unique_evidence.sort(key=lambda c: c.score, reverse=True)
        top_evidence = unique_evidence[: self.settings.retrieval_top_k]

        if not top_evidence:
            return ReasoningResult(
                answer=NO_EVIDENCE_ANSWER,
                citations=[],
                confidence="low",
                disclaimer=DISCLAIMER,
                pipeline="decompose_qa",
                sub_questions=sub_questions,
            )

        if evaluation_observer is not None:
            evaluation_observer.record_selected_context(top_evidence)
            evaluation_observer.record_generator_context(top_evidence)
        prompt = build_grounded_prompt(question, top_evidence, conversation_history)
        answer = await ChatGenerator(self.settings).generate(prompt)
        citation_ids = extract_citation_ids(answer)
        allowed_ids = {item.evidence_id for item in top_evidence}
        cited = [c for c in top_evidence if c.evidence_id in (citation_ids & allowed_ids)]

        return ReasoningResult(
            answer=answer,
            citations=[_to_evidence_schema(c) for c in cited],
            confidence=confidence_from_score(top_evidence[0].score) if top_evidence else "low",
            disclaimer=DISCLAIMER,
            pipeline="decompose_qa",
            sub_questions=sub_questions,
        )


class PatientSummaryPipeline:
    """Generate a structured patient summary from all available evidence."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.reranker = RerankerService(settings)

    async def run(
        self,
        *,
        patient_name: str,
        evidence: list[RetrievedChunk],
        evaluation_observer: Optional[EvaluationObserver] = None,
    ) -> ReasoningResult:
        reranked = self.reranker.rerank(f"patient summary for {patient_name}", evidence, top_k=10)

        if not reranked:
            return ReasoningResult(
                answer=f"No evidence available for patient summary of {patient_name}.",
                citations=[],
                confidence="low",
                disclaimer=DISCLAIMER,
                pipeline="patient_summary",
            )

        if evaluation_observer is not None:
            evaluation_observer.record_selected_context(reranked)
            evaluation_observer.record_generator_context(reranked)
        context_lines = []
        for chunk in reranked:
            context_lines.append(
                f"[{chunk.evidence_id}] (source: {chunk.document_title}, page {chunk.page}):\n{chunk.content}"
            )

        prompt = (
            f"{PATIENT_SUMMARY_SYSTEM_PROMPT}\n\n"
            f"Patient: {patient_name}\n\n"
            f"Evidence:\n" + "\n\n".join(context_lines) + "\n\n"
            "Produce the structured patient summary now."
        )

        answer = await ChatGenerator(self.settings).generate(prompt)
        citation_ids = extract_citation_ids(answer)
        allowed_ids = {item.evidence_id for item in reranked}
        cited = [c for c in reranked if c.evidence_id in (citation_ids & allowed_ids)]

        return ReasoningResult(
            answer=answer,
            citations=[_to_evidence_schema(c) for c in cited],
            confidence=confidence_from_score(reranked[0].score) if reranked else "low",
            disclaimer=DISCLAIMER,
            pipeline="patient_summary",
        )


def _decompose_question(question: str) -> list[str]:
    """Heuristic question decomposition without calling an LLM.

    Splits on conjunctions and commas to find sub-questions.
    Falls back to the original question if decomposition doesn't help.
    """
    parts = re.split(r"\band\b|\balso\b|,\s*(?:and\s*)?", question, flags=re.IGNORECASE)
    sub_questions = [part.strip().rstrip("?").strip() + "?" for part in parts if len(part.strip()) > 10]
    return sub_questions if len(sub_questions) > 1 else [question]


def _to_evidence_schema(chunk: RetrievedChunk) -> EvidenceRead:
    return EvidenceRead(
        evidence_id=chunk.evidence_id,
        document_id=chunk.document_id,
        document_title=chunk.document_title,
        page=chunk.page,
        chunk_id=chunk.chunk_id,
        score=chunk.score,
        content=chunk.content,
        metadata=dict(chunk.metadata),
    )
