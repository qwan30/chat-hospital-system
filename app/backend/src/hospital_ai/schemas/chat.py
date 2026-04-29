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


class DrugWarningSchema(BaseModel):
    """A drug interaction warning surfaced during query processing."""
    drug_name: str
    interacting_entity: str
    interaction_type: str
    severity: str
    evidence_chunk_id: UUID
    message: str


class ChatResponse(BaseModel):
    query_id: UUID
    answer: str
    citations: List[EvidenceRead]
    confidence: str
    disclaimer: str = "AI output must be verified by clinical staff."
    thread_id: Optional[UUID] = None
    pipeline: Optional[str] = None
    warnings: List[DrugWarningSchema] = []


class RagTraceEvidence(BaseModel):
    """A single evidence chunk within a RAG trace."""
    evidence_id: str
    chunk_id: UUID
    rank: int
    retrieval_score: float
    rerank_score: Optional[float] = None
    retrieval_method: Optional[str] = None
    rerank_method: Optional[str] = None
    citation_label: str
    content: Optional[str] = None
    document_title: Optional[str] = None
    page: Optional[int] = None


class RagTraceResponse(BaseModel):
    """Full RAG trace for a given query — exposes the retrieval pipeline internals."""
    query_id: UUID
    question: str
    answer: Optional[str] = None
    status: str
    pipeline: Optional[str] = None
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    evidence: List[RagTraceEvidence]
    created_at: str
