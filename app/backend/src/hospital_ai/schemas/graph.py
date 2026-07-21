from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    sublabel: Optional[str] = None
    source_document_id: Optional[UUID] = None
    source_chunk_id: Optional[UUID] = None
    x: int = 0
    y: int = 0


class GraphEdge(BaseModel):
    id: str
    from_node: str
    to_node: str
    label: str
    source_document_id: Optional[UUID] = None
    source_chunk_id: Optional[UUID] = None


class GraphPathStep(BaseModel):
    from_node: str
    to_node: str
    relation: str
    evidence: str
    source_document_id: Optional[UUID] = None
    source_chunk_id: Optional[UUID] = None


class GraphPath(BaseModel):
    id: str
    rationale: str
    steps: list[GraphPathStep]


class GraphMetadata(BaseModel):
    patient_id: UUID
    updated_at: str
    node_count: int
    edge_count: int


class GraphDataResponse(BaseModel):
    patient_id: UUID
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    reasoning_path: list[GraphPath]
    metadata: GraphMetadata
