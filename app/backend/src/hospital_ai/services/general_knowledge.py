from __future__ import annotations

import re
import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.schemas.documents import EvidenceRead
from hospital_ai.services.chat import (
    ChatGenerator,
    build_grounded_prompt,
    confidence_from_score,
    extract_citation_ids,
)
from hospital_ai.services.retrieval import RetrievedChunk

GENERAL_NO_EVIDENCE_ANSWER = (
    "I could not find approved general hospital knowledge for this question. "
    "Please check the hospital policy source directly or ask records staff to add an approved non-PHI source."
)
GENERAL_DISCLAIMER = "General hospital knowledge must be verified against current local policy before use."


@dataclass(frozen=True)
class ApprovedGeneralKnowledgeSource:
    document_id: uuid.UUID
    chunk_id: uuid.UUID
    title: str
    page: int
    content: str
    keywords: frozenset[str]


@dataclass(frozen=True)
class GeneralKnowledgeAnswer:
    answer: str
    citations: list[EvidenceRead]
    confidence: str
    disclaimer: str = GENERAL_DISCLAIMER


APPROVED_GENERAL_KNOWLEDGE: Sequence[ApprovedGeneralKnowledgeSource] = (
    ApprovedGeneralKnowledgeSource(
        document_id=uuid.UUID("90000000-0000-0000-0000-000000000001"),
        chunk_id=uuid.UUID("91000000-0000-0000-0000-000000000001"),
        title="Approved ward transfer policy",
        page=12,
        content=(
            "Ward transfer requests should include receiving unit confirmation, attending approval, "
            "current observation needs, isolation precautions, and the latest medication administration status."
        ),
        keywords=frozenset(
            {
                "ward",
                "transfer",
                "policy",
                "receiving",
                "unit",
                "confirmation",
                "attending",
                "approval",
                "observation",
                "isolation",
                "medication",
            }
        ),
    ),
    ApprovedGeneralKnowledgeSource(
        document_id=uuid.UUID("90000000-0000-0000-0000-000000000002"),
        chunk_id=uuid.UUID("91000000-0000-0000-0000-000000000002"),
        title="Approved discharge checklist",
        page=4,
        content=(
            "Discharge preparation should confirm patient education, follow-up appointment details, "
            "medication reconciliation, transport readiness, and documented handoff instructions."
        ),
        keywords=frozenset(
            {
                "discharge",
                "checklist",
                "education",
                "follow",
                "appointment",
                "medication",
                "reconciliation",
                "transport",
                "handoff",
            }
        ),
    ),
    ApprovedGeneralKnowledgeSource(
        document_id=uuid.UUID("90000000-0000-0000-0000-000000000003"),
        chunk_id=uuid.UUID("91000000-0000-0000-0000-000000000003"),
        title="Approved infection control quick guide",
        page=7,
        content=(
            "Standard infection control reminders include hand hygiene before and after patient contact, "
            "appropriate personal protective equipment, and prompt isolation escalation for flagged symptoms."
        ),
        keywords=frozenset(
            {
                "infection",
                "control",
                "hand",
                "hygiene",
                "patient",
                "contact",
                "protective",
                "equipment",
                "isolation",
                "symptoms",
            }
        ),
    ),
    ApprovedGeneralKnowledgeSource(
        document_id=uuid.UUID("90000000-0000-0000-0000-000000000004"),
        chunk_id=uuid.UUID("91000000-0000-0000-0000-000000000004"),
        title="Clinical Guideline: STEMI Emergency Management Protocol",
        page=1,
        content=(
            "For suspected acute ST-Elevation Myocardial Infarction (STEMI), immediately obtain 12-lead ECG "
            "within 10 minutes. Activate the emergency cardiac catheterization lab team (Cathlab), administer "
            "aspirin 300mg chewable, high-potency P2Y12 inhibitor, sublingual nitroglycerin if systolic BP > 90, "
            "and prepare for immediate Primary PCI with target door-to-balloon time under 90 minutes."
        ),
        keywords=frozenset(
            {
                "stemi",
                "myocardial",
                "infarction",
                "ecg",
                "cathlab",
                "cardiac",
                "aspirin",
                "pci",
                "chest",
                "pain",
                "protocol",
                "emergency",
            }
        ),
    ),
    ApprovedGeneralKnowledgeSource(
        document_id=uuid.UUID("90000000-0000-0000-0000-000000000005"),
        chunk_id=uuid.UUID("91000000-0000-0000-0000-000000000005"),
        title="Clinical Protocol: SBAR Shift Handoff Standard",
        page=2,
        content=(
            "Clinical shift handoff follows the structured SBAR model: Situation (patient identity, current status), "
            "Background (admission diagnosis, relevant history, allergies), Assessment (vital signs, clinical trends, "
            "abnormal labs), and Recommendation (pending investigations, escalation plan, critical follow-up tasks)."
        ),
        keywords=frozenset(
            {
                "sbar",
                "handoff",
                "shift",
                "handover",
                "situation",
                "background",
                "assessment",
                "recommendation",
                "nursing",
                "communication",
            }
        ),
    ),
    ApprovedGeneralKnowledgeSource(
        document_id=uuid.UUID("90000000-0000-0000-0000-000000000006"),
        chunk_id=uuid.UUID("91000000-0000-0000-0000-000000000006"),
        title="Clinical Guideline: NEWS2 Deterioration & Escalation Criteria",
        page=3,
        content=(
            "The National Early Warning Score 2 (NEWS2) monitors respiration rate, oxygen saturation, systolic BP, "
            "pulse, consciousness level, and temperature. An aggregate score of 5-6 or an individual red score of 3 "
            "requires urgent clinical review within 30 minutes; a score of 7 or higher triggers immediate Medical "
            "Emergency Team (MET) / Rapid Response Team escalation and continuous vital monitoring."
        ),
        keywords=frozenset(
            {
                "news2",
                "escalation",
                "deterioration",
                "vital",
                "warning",
                "met",
                "rapid",
                "response",
                "score",
                "triggers",
                "emergency",
            }
        ),
    ),
)


class GeneralKnowledgeService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def answer(self, question: str, top_k: int = 5) -> GeneralKnowledgeAnswer:
        evidence = rank_general_knowledge(question, top_k)
        if not evidence:
            return GeneralKnowledgeAnswer(
                answer=GENERAL_NO_EVIDENCE_ANSWER,
                citations=[],
                confidence="low",
            )

        prompt = build_grounded_prompt(question, evidence)
        answer = await ChatGenerator(self.settings).generate(prompt)
        citation_ids = extract_citation_ids(answer)
        allowed_ids = {item.evidence_id for item in evidence}
        if not citation_ids or not citation_ids.issubset(allowed_ids):
            raise ExternalServiceError("Generated general answer included invalid or missing citations.")

        cited_evidence = [item for item in evidence if item.evidence_id in citation_ids]
        return GeneralKnowledgeAnswer(
            answer=answer,
            citations=[to_general_evidence_schema(item) for item in cited_evidence],
            confidence=confidence_from_score(evidence[0].score),
        )


def rank_general_knowledge(question: str, top_k: int) -> list[RetrievedChunk]:
    query_tokens = tokenize(question)
    if not query_tokens:
        return []

    scored = []
    for source in APPROVED_GENERAL_KNOWLEDGE:
        overlap = query_tokens.intersection(source.keywords)
        if not overlap:
            continue
        score = min(0.99, 0.45 + (len(overlap) / max(len(query_tokens), 1)))
        scored.append((score, source))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        RetrievedChunk(
            evidence_id=f"E{index}",
            document_id=source.document_id,
            document_title=source.title,
            page=source.page,
            chunk_id=source.chunk_id,
            score=float(score),
            content=source.content,
            metadata={
                "source_scope": "general-hospital-knowledge",
                "approved_non_phi": True,
                "contains_phi": False,
            },
        )
        for index, (score, source) in enumerate(scored[:top_k], start=1)
    ]


def tokenize(value: str) -> frozenset[str]:
    return frozenset(re.findall(r"[a-z0-9]+", value.lower()))


def to_general_evidence_schema(item: RetrievedChunk) -> EvidenceRead:
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
