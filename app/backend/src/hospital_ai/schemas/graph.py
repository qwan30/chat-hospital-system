from uuid import UUID

from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    sublabel: str | None = None
    x: int = 0
    y: int = 0


class GraphEdge(BaseModel):
    id: str
    from_node: str
    to_node: str
    label: str


class GraphPathStep(BaseModel):
    from_node: str
    to_node: str
    relation: str
    evidence: str


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
