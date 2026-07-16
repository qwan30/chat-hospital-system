import logging
import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.models import DocumentChunk, Patient, User
from hospital_ai.schemas.graph import GraphDataResponse, GraphEdge, GraphMetadata, GraphNode, GraphPath, GraphPathStep
from hospital_ai.services.graph_rag import GraphEntity, GraphRelation, find_related_entities
from hospital_ai.services.permissions import PermissionService

logger = logging.getLogger(__name__)

router = APIRouter()

# Layout constants for simple grid/radial positioning
_LAYOUT_RADIUS = 200
_ENTITY_TYPE_SECTORS: dict[str, float] = {
    "patient": 0.0,
    "encounter": 1.2,
    "diagnosis": 2.4,
    "drug": 3.6,
    "condition": 3.0,
    "lab": 4.8,
}


@router.get("/patients/{patient_id}", response_model=GraphDataResponse)
async def get_patient_graph(
    request: Request,
    patient_id: uuid.UUID = Path(..., title="The ID of the patient to get the graph for"),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    trace_id = new_trace_id()
    await PermissionService(db).require_read(
        user=current_user,
        patient_id=patient_id,
        action="graph.read",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
    )

    # Verify patient exists
    patient = await db.get(Patient, patient_id)
    if patient is None or patient.deleted_at is not None:
        from hospital_ai.core.errors import NotFoundError

        raise NotFoundError("Patient not found.")

    # Query graph entities scoped to this patient's document chunks
    patient_chunk_ids = select(DocumentChunk.id).where(DocumentChunk.patient_id == patient_id).scalar_subquery()
    entity_result = await db.execute(
        select(GraphEntity).where(GraphEntity.source_chunk_id.in_(patient_chunk_ids)).limit(200)
    )
    entities = list(entity_result.scalars().all())

    if not entities:
        # No graph data — return empty graph with placeholder patient node
        empty_nodes = [
            GraphNode(id="pt", type="patient", label="Patient", sublabel=patient.full_name, x=400, y=240),
        ]
        metadata = GraphMetadata(
            patient_id=patient_id,
            updated_at=datetime.now(timezone.utc).isoformat(),
            node_count=1,
            edge_count=0,
        )
        return GraphDataResponse(
            patient_id=patient_id,
            nodes=empty_nodes,
            edges=[],
            reasoning_path=[],
            metadata=metadata,
        )

    entity_id_set = {e.id for e in entities}

    # Query relations between these entities
    relation_result = await db.execute(
        select(GraphRelation)
        .where(
            GraphRelation.source_entity_id.in_(entity_id_set),
            GraphRelation.target_entity_id.in_(entity_id_set),
        )
        .limit(500)
    )
    relations = list(relation_result.scalars().all())

    # ── Build nodes ───────────────────────────────────────────────────
    nodes: list[GraphNode] = []
    # Always include the patient as root node
    nodes.append(
        GraphNode(
            id="pt",
            type="patient",
            label="Patient",
            sublabel=patient.full_name,
            x=400,
            y=240,
        )
    )

    # Group entities by type for layout
    typed_entities: dict[str, list[GraphEntity]] = {}
    for e in entities:
        typed_entities.setdefault(e.entity_type, []).append(e)

    center_x, center_y = 400, 240
    entity_idx = 0
    for entity_type, group in typed_entities.items():
        base_angle = _ENTITY_TYPE_SECTORS.get(entity_type, entity_idx * 1.0)
        for j, ent in enumerate(group):
            angle = base_angle + (j * 0.3)
            radius = _LAYOUT_RADIUS + (j % 3) * 60
            x = int(center_x + radius * math.cos(angle))
            y = int(center_y + radius * math.sin(angle))
            node_id = f"e-{ent.id}"
            label = ent.name[:40]
            sublabel = ent.entity_type
            nodes.append(
                GraphNode(
                    id=node_id,
                    type=_map_entity_type_to_graph_type(ent.entity_type),
                    label=label,
                    sublabel=sublabel,
                    x=x,
                    y=y,
                )
            )
            entity_idx += 1

    # ── Build edges ───────────────────────────────────────────────────
    id_to_node_id = {e.id: f"e-{e.id}" for e in entities}
    edges: list[GraphEdge] = []
    for rel in relations:
        from_id = id_to_node_id.get(rel.source_entity_id)
        to_id = id_to_node_id.get(rel.target_entity_id)
        if from_id and to_id:
            edges.append(
                GraphEdge(
                    id=f"edge-{rel.id}",
                    from_node=from_id,
                    to_node=to_id,
                    label=rel.relation_type,
                )
            )
        # Connect first few entities to patient node
        if len(edges) <= 5 and from_id:
            edges.append(
                GraphEdge(
                    id=f"edge-pt-{rel.id}",
                    from_node="pt",
                    to_node=from_id,
                    label="has",
                )
            )

    # ── Build reasoning paths ─────────────────────────────────────────
    reasoning_path: list[GraphPath] = []
    if entities:
        # Use find_related_entities for a sample traversal
        sample_names = [e.name for e in entities[:3]]
        try:
            ctx = await find_related_entities(db, sample_names, max_hops=1, patient_id=patient_id)
            if ctx.relations:
                steps = []
                for rel in ctx.relations[:5]:
                    steps.append(
                        GraphPathStep(
                            from_node=rel.source_name,
                            to_node=rel.target_name,
                            relation=rel.relation_type,
                            evidence="Indexed document chunk",
                        )
                    )
                reasoning_path.append(
                    GraphPath(
                        id="path-dynamic-001",
                        rationale=ctx.summary,
                        steps=steps,
                    )
                )
        except Exception:
            logger.warning("Graph reasoning path generation failed", exc_info=True)

    # ── Deduplicate edges ─────────────────────────────────────────────
    seen_edge_keys: set[tuple[str, str, str]] = set()
    deduped_edges: list[GraphEdge] = []
    for edge in edges:
        key = (edge.from_node, edge.to_node, edge.label)
        if key not in seen_edge_keys:
            seen_edge_keys.add(key)
            deduped_edges.append(edge)

    metadata = GraphMetadata(
        patient_id=patient_id,
        updated_at=datetime.now(timezone.utc).isoformat(),
        node_count=len(nodes),
        edge_count=len(deduped_edges),
    )

    return GraphDataResponse(
        patient_id=patient_id,
        nodes=nodes,
        edges=deduped_edges,
        reasoning_path=reasoning_path,
        metadata=metadata,
    )


def _map_entity_type_to_graph_type(entity_type: str) -> str:
    """Map internal entity_type to graph visualizer type."""
    mapping = {
        "drug": "medication",
        "medication": "medication",
        "condition": "diagnosis",
        "diagnosis": "diagnosis",
        "lab": "lab",
        "encounter": "encounter",
        "patient": "patient",
    }
    return mapping.get(entity_type, entity_type)
