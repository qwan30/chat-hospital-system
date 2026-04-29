from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from hospital_ai.schemas.documents import EvidenceRead


class ChatRequest(BaseModel):
    patient_id: UUID
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    thread_id: Optional[UUID] = None
    pipeline: str = Field(default="auto", description="Reasoning pipeline: auto, simple, decompose, patient_summary")


class ChatResponse(BaseModel):
    query_id: UUID
    answer: str
    citations: List[EvidenceRead]
    confidence: str
    disclaimer: str = "AI output must be verified by clinical staff."
    thread_id: Optional[UUID] = None
    pipeline: Optional[str] = None
