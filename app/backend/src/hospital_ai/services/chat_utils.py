"""Shared utilities for chat and reasoning pipelines.

Extracted to avoid circular imports between chat.py and reasoning.py.
"""

import re
from collections.abc import Sequence
from typing import Optional

from hospital_ai.core.config import Settings
from hospital_ai.schemas.documents import EvidenceRead
from hospital_ai.services.retrieval import RetrievedChunk

CITATION_PATTERN = re.compile(r"\[(E\d+)\]")
MAX_HISTORY_MESSAGES = 10


class ChatGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate(self, prompt: str) -> str:
        """Generate a response using the configured LLM provider."""
        from hospital_ai.services.llm import LLMManager
        from hospital_ai.services.llm.base import LLMMessage

        manager = LLMManager(settings=self.settings)
        llm = manager.get()

        messages = [
            LLMMessage(
                role="system",
                content=self.settings.system_prompt,
            ),
            LLMMessage(role="user", content=prompt),
        ]

        try:
            response = await llm.generate(messages)
            return response.text
        except Exception:
            # Fall back to stub answer if provider is unavailable
            if self.settings.chat_provider == "stub":
                return build_stub_answer(prompt)
            raise


def build_grounded_prompt(
    question: str,
    evidence: Sequence[RetrievedChunk],
    conversation_history: Optional[list[dict[str, str]]] = None,
) -> str:
    blocks = []
    for item in evidence:
        blocks.append(f"[{item.evidence_id}] Document: {item.document_title}; page: {item.page}\n{item.content}")
    parts: list[str] = []
    if conversation_history:
        parts.append("Previous conversation:")
        for msg in conversation_history[-MAX_HISTORY_MESSAGES:]:
            role = msg.get("role", "user").capitalize()
            parts.append(f"{role}: {msg['content']}")
        parts.append("")
    parts.append("Question:")
    parts.append(question)
    parts.append("")
    parts.append("Authorized evidence:")
    parts.append("\n\n".join(blocks))
    parts.append("")
    parts.append("Answer using only the evidence. Include citations like [E1].")
    return "\n".join(parts)


def build_stub_answer(prompt: str) -> str:
    evidence = parse_prompt_evidence(prompt)
    if not evidence:
        return "Based on the authorized evidence, the record contains relevant clinical details [E1]."

    evidence_id, content = evidence[0]
    status = line_value(content, "Status")
    vital_signs = line_value(content, "Vital signs")
    if status or vital_signs:
        parts = []
        if status:
            parts.append(f"The appointment status is {status} [{evidence_id}].")
        if vital_signs:
            parts.append(f"Vital signs: {trim_sentence(vital_signs)} [{evidence_id}].")
        return " ".join(parts)

    first_fact = first_evidence_fact(content)
    return f"Based on the authorized evidence, {trim_sentence(first_fact)} [{evidence_id}]."


def parse_prompt_evidence(prompt: str) -> list[tuple]:
    pattern = re.compile(
        r"\[(E\d+)\] Document:.*?\n(?P<content>.*?)(?=\n\n\[E\d+\] Document:|\n\nAnswer using only the evidence\.|$)",
        re.DOTALL,
    )
    return [(match.group(1), match.group("content").strip()) for match in pattern.finditer(prompt)]


def line_value(content: str, label: str) -> str:
    prefix = f"{label}:"
    for line in content.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return ""


def first_evidence_fact(content: str) -> str:
    for line in content.splitlines():
        normalized = line.strip()
        if normalized and normalized.lower() != "hms appointment summary":
            return normalized
    return "the record contains relevant clinical details"


def trim_sentence(value: str) -> str:
    return value.rstrip(".")


def extract_citation_ids(answer: str) -> set[str]:
    return set(CITATION_PATTERN.findall(answer))


def citations_are_valid(answer: str, allowed_evidence_ids: set[str]) -> bool:
    citation_ids = extract_citation_ids(answer)
    return bool(citation_ids) and citation_ids.issubset(allowed_evidence_ids)


def confidence_from_score(score: float) -> str:
    if score >= 0.78:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def meets_evidence_threshold(item: RetrievedChunk, retrieval_mode: str, threshold: float) -> bool:
    """Return True if `item` clears `threshold` under the active retrieval mode.

    Vector and BM25 modes return scores on `[0, 1]` and are compared directly
    against `threshold`.  Hybrid mode uses Reciprocal Rank Fusion which
    produces tiny scores (typically `<= 0.06`); comparing them to a 0.2
    threshold would silently mark every hybrid query as "no evidence".

    For hybrid we look at `metadata["score_list_*"]` (preserved by RRF) and
    require at least one underlying retriever to clear `threshold`.
    """
    if retrieval_mode != "hybrid":
        return item.score >= threshold

    underlying_scores: list[float] = []
    for key, value in (item.metadata or {}).items():
        if not isinstance(key, str) or not key.startswith("score_list_"):
            continue
        try:
            underlying_scores.append(float(value))
        except (TypeError, ValueError):
            continue

    if not underlying_scores:
        # No score_list_* metadata — fall back to any non-zero RRF score.
        return item.score > 0.0

    return max(underlying_scores) >= threshold


def to_evidence_schema(item: RetrievedChunk) -> EvidenceRead:
    return EvidenceRead(
        evidence_id=item.evidence_id,
        document_id=item.document_id,
        document_title=item.document_title,
        page=item.page,
        chunk_id=item.chunk_id,
        score=item.score,
        content=item.content,
        metadata=dict(item.metadata),
    )
