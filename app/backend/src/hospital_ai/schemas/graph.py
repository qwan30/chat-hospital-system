"""Schemas cho Đồ thị tri thức y tế (Medical Graph RAG APIs).

Định nghĩa cấu trúc các nút (nodes), cạnh kết nối (edges) và chuỗi suy luận
(reasoning path) trên đồ thị tri thức bệnh nhân.
"""

from uuid import UUID

from pydantic import BaseModel


class GraphNode(BaseModel):
    """Schema biểu diễn một nút thực thể trên đồ thị (Bệnh nhân, Chẩn đoán, Thuốc, Triệu chứng...)."""
    id: str
    type: str
    label: str
    sublabel: str | None = None
    x: int = 0
    y: int = 0


class GraphEdge(BaseModel):
    """Schema biểu diễn một mối quan hệ (edge) giữa hai nút thực thể trên đồ thị y tế."""
    id: str
    from_node: str
    to_node: str
    label: str


class GraphPathStep(BaseModel):
    """Schema biểu diễn một bước suy luận từng phần giữa 2 nút kèm bằng chứng trích xuất."""
    from_node: str
    to_node: str
    relation: str
    evidence: str


class GraphPath(BaseModel):
    """Schema biểu diễn chuỗi đường đi suy luận (Reasoning Path) giải thích cách AI kết nối thông tin trên đồ thị."""
    id: str
    rationale: str
    steps: list[GraphPathStep]


class GraphMetadata(BaseModel):
    """Schema siêu dữ liệu của đồ thị tri thức bệnh nhân (tổng số nút, cạnh và thời gian cập nhật)."""
    patient_id: UUID
    updated_at: str
    node_count: int
    edge_count: int


class GraphDataResponse(BaseModel):
    """Schema phản hồi toàn bộ dữ liệu đồ thị tri thức của một bệnh nhân cho giao diện trực quan hóa."""
    patient_id: UUID
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    reasoning_path: list[GraphPath]
    metadata: GraphMetadata

