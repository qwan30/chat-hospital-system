from uuid import UUID

from pydantic import BaseModel, Field, root_validator

from hospital_ai.schemas.documents import EvidenceRead


class ChatContext(BaseModel):
    patient_id: UUID | None = None
    document_ids: list[UUID] | None = None


class ChatRequest(BaseModel):
    patient_id: UUID | None = None
    question: str = Field(min_length=1, max_length=4000)
    context: ChatContext | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    thread_id: UUID | None = None
    pipeline: str = Field(default="auto", description="Reasoning pipeline: auto, simple, decompose, patient_summary")
    mode: str | None = None

    @root_validator(pre=True)
    def map_message_to_question(cls, values):
        if "message" in values and "question" not in values:
            values["question"] = values["message"]
        return values


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
    citations: list[EvidenceRead]
    confidence: str
    disclaimer: str = "AI output must be verified by clinical staff."
    thread_id: UUID | None = None
    pipeline: str | None = None
    warnings: list[DrugWarningSchema] = []
    safety_status: str | None = None
    mode: str | None = None


class RagTraceEvidence(BaseModel):
    """A single evidence chunk within a RAG trace."""

    evidence_id: str
    chunk_id: UUID
    rank: int
    retrieval_score: float
    rerank_score: float | None = None
    retrieval_method: str | None = None
    rerank_method: str | None = None
    citation_label: str
    content: str | None = None
    document_title: str | None = None
    page: int | None = None


class RagTraceResponse(BaseModel):
    """Full RAG trace for a given query — exposes the retrieval pipeline internals."""

    query_id: UUID
    question: str
    answer: str | None = None
    status: str
    pipeline: str | None = None
    model: str | None = None
    latency_ms: int | None = None
    evidence: list[RagTraceEvidence]
    created_at: str
