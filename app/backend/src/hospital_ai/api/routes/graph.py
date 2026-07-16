"""Knowledge Graph visualization API routes.
Các endpoint API cung cấp dữ liệu mạng lưới tri thức y khoa (graph nodes, edges & reasoning path) của bệnh nhân.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.models import User
from hospital_ai.schemas.graph import GraphDataResponse, GraphEdge, GraphMetadata, GraphNode, GraphPath, GraphPathStep
from hospital_ai.services.permissions import PermissionService

router = APIRouter()


@router.get("/patients/{patient_id}", response_model=GraphDataResponse)
async def get_patient_graph(
    request: Request,
    patient_id: uuid.UUID = Path(..., title="The ID of the patient to get the graph for"),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve clinical knowledge graph structure (nodes and edges) and reasoning paths for a patient.
    Lấy dữ liệu mạng lưới tri thức lâm sàng (thực thể, mối quan hệ và đường dẫn suy luận) của một bệnh nhân cụ thể.
    """
    await PermissionService(db).require_read(
        user=current_user,
        patient_id=patient_id,
        action="graph.read",
        trace_id=new_trace_id(),
        ip_address=get_request_ip(request),
    )

    # Phase 12 - Serve dynamic graph or seeded graph.
    # Currently serving a seeded graph mirroring the frontend for Phase 12 completion
    # while laying the foundation for dynamic traversal.

    nodes = [
        GraphNode(id="pt", type="patient", label="Patient", sublabel=str(patient_id), x=400, y=240),
        GraphNode(id="e1", type="encounter", label="Admission", sublabel="Recent", x=180, y=120),
        GraphNode(id="d1", type="diagnosis", label="Atrial fibrillation", sublabel="I48.0", x=620, y=100),
        GraphNode(id="m1", type="medication", label="Apixaban", sublabel="5mg BID", x=820, y=100),
        GraphNode(id="l1", type="lab", label="BNP 612", sublabel="Recent", x=400, y=60),
    ]

    edges = [
        GraphEdge(id="e-pt-e1", from_node="pt", to_node="e1", label="had"),
        GraphEdge(id="e-e1-d1", from_node="e1", to_node="d1", label="diagnosed"),
        GraphEdge(id="e-d1-m1", from_node="d1", to_node="m1", label="treats"),
        GraphEdge(id="e-pt-l1", from_node="pt", to_node="l1", label="result"),
    ]

    reasoning_path = [
        GraphPath(
            id="path-001",
            rationale="Selected because the query asked 'why apixaban for this patient'",
            steps=[
                GraphPathStep(
                    from_node="Patient",
                    to_node="Atrial fibrillation (I48.0)",
                    relation="diagnosed at admission",
                    evidence="Admit note",
                ),
                GraphPathStep(
                    from_node="Atrial fibrillation",
                    to_node="Apixaban 5mg BID",
                    relation="guideline-directed anticoagulation",
                    evidence="ACC/AHA AFib 2023",
                ),
            ],
        )
    ]

    metadata = GraphMetadata(
        patient_id=patient_id,
        updated_at=datetime.now(UTC).isoformat(),
        node_count=len(nodes),
        edge_count=len(edges),
    )

    return GraphDataResponse(
        patient_id=patient_id, nodes=nodes, edges=edges, reasoning_path=reasoning_path, metadata=metadata
    )
