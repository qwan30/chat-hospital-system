import logging
import math
import re
import uuid
from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip, get_session
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage, Patient, User
from hospital_ai.schemas.graph import GraphDataResponse, GraphEdge, GraphMetadata, GraphNode, GraphPath, GraphPathStep
from hospital_ai.services.graph_rag import GraphEntity, GraphRelation
from hospital_ai.services.permissions import PermissionService
from hospital_ai.services.retrieval import RetrievalService

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


def _contains_token(value: str, token: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(token)}(?!\w)", value) is not None


def _canonical_entity_info(name: str, entity_type: str) -> tuple[str, str, Optional[str]]:
    """Returns (canonical_name, canonical_type, sublabel)."""
    # Lower case and strip to clean
    n = name.strip().lower()
    t = _map_entity_type_to_graph_type(entity_type)
    lab_value_label = name.strip() if re.search(r"(?<![A-Za-z])\d", name) else None

    # Common normalization mapping
    # conditions
    if n in ("diabetes", "type 2 diabetes mellitus", "đái tháo đường", "dai thao duong"):
        return "Type 2 Diabetes Mellitus", "diagnosis", None
    if n in ("hypertension", "tăng huyết áp", "tang huyet ap"):
        return "Hypertension", "diagnosis", None
    if n in ("chronic kidney disease", "ckd stage 3", "suy thận", "suy than"):
        return "Chronic Kidney Disease", "diagnosis", None
    if n in ("coronary artery disease", "coronary artery disease (cad)", "cad"):
        return "Coronary Artery Disease (CAD)", "diagnosis", None
    if n in ("atrial fibrillation", "atrial fibrillation (afib)", "afib"):
        return "Atrial Fibrillation (AFib)", "diagnosis", None

    # drugs
    if "lisinopril" in n:
        return "Lisinopril", "medication", None
    if "metformin" in n:
        return "Metformin", "medication", None
    if "amlodipine" in n:
        return "Amlodipine", "medication", None
    if "aspirin" in n:
        return "Aspirin", "medication", None
    if "atorvastatin" in n:
        return "Atorvastatin", "medication", None
    if "carvedilol" in n:
        return "Carvedilol", "medication", None
    if "ramipril" in n:
        return "Ramipril", "medication", None
    if "apixaban" in n:
        return "Apixaban", "medication", None
    if "metoprolol" in n:
        return "Metoprolol", "medication", None
    if "furosemide" in n:
        return "Furosemide", "medication", None

    # labs
    if _contains_token(n, "hba1c"):
        return "HbA1c", "lab", lab_value_label
    if "potassium" in n or "kali" in n:
        return "Potassium", "lab", lab_value_label
    if "hemoglobin" in n or _contains_token(n, "hgb"):
        return "Hemoglobin", "lab", lab_value_label
    if _contains_token(n, "bnp"):
        return "BNP", "lab", lab_value_label
    if "creatinine" in n:
        return "Creatinine", "lab", lab_value_label
    if "glucose" in n:
        return "Glucose", "lab", lab_value_label
    if _contains_token(n, "ast"):
        return "AST", "lab", lab_value_label
    if _contains_token(n, "alt"):
        return "ALT", "lab", lab_value_label
    if "sodium" in n or "natri" in n:
        return "Sodium", "lab", lab_value_label
    if _contains_token(n, "egfr"):
        return "eGFR", "lab", lab_value_label

    # encounters / procedures
    if "cabg" in n or "coronary artery bypass" in n:
        return "CABG Procedure", "encounter", None

    return name.title(), t, None


def _canonical_name(name: str) -> str:
    canonical_name, _, _ = _canonical_entity_info(name, "unknown")
    return canonical_name


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

    # Only active, internally consistent patient evidence may back graph data.
    active_patient_sources = (
        select(
            DocumentChunk.id.label("chunk_id"),
            DocumentChunk.document_id.label("document_id"),
        )
        .join(
            DocumentPage,
            and_(
                DocumentPage.id == DocumentChunk.page_id,
                DocumentPage.document_id == DocumentChunk.document_id,
            ),
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.patient_id == patient_id,
            Document.patient_id == patient_id,
            Document.status.in_(("ready", "ready_with_warnings")),
            DocumentChunk.deleted_at.is_(None),
            DocumentPage.deleted_at.is_(None),
            Document.deleted_at.is_(None),
        )
        .subquery()
    )
    source_chunk_ids = list((await db.scalars(select(active_patient_sources.c.chunk_id))).all())
    visible_source_ids = {
        chunk.chunk_id
        for chunk in await RetrievalService(db).get_chunks_by_ids(
            source_chunk_ids,
            user_id=current_user.id,
            patient_id=patient_id,
        )
    }
    entity_result = await db.execute(
        select(GraphEntity)
        .join(
            active_patient_sources,
            and_(
                GraphEntity.source_chunk_id == active_patient_sources.c.chunk_id,
                GraphEntity.source_document_id == active_patient_sources.c.document_id,
            ),
        )
        .where(GraphEntity.source_chunk_id.in_(visible_source_ids))
        .order_by(GraphEntity.id)
        .limit(200)
    )
    entities = list(entity_result.scalars().all())

    if not entities:
        # No graph data — return empty graph with placeholder patient node
        empty_nodes = [
            GraphNode(id="pt", type="patient", label="Patient", sublabel=patient.full_name, x=400, y=240),
        ]
        metadata = GraphMetadata(
            patient_id=patient_id,
            updated_at=datetime.now(UTC).isoformat(),
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
        select(GraphRelation, active_patient_sources.c.document_id)
        .join(active_patient_sources, GraphRelation.source_chunk_id == active_patient_sources.c.chunk_id)
        .where(
            GraphRelation.source_entity_id.in_(entity_id_set),
            GraphRelation.target_entity_id.in_(entity_id_set),
            GraphRelation.source_chunk_id.in_(visible_source_ids),
        )
        .order_by(GraphRelation.id)
        .limit(500)
    )
    relation_rows = list(relation_result.all())
    relations = [relation for relation, _ in relation_rows]
    relation_provenance = {
        relation.id: (source_document_id, relation.source_chunk_id) for relation, source_document_id in relation_rows
    }

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

    # Consolidate entities to map duplicates
    db_id_to_node_id: dict[uuid.UUID, str] = {}
    consolidated_nodes: dict[tuple[str, ...], dict] = {}

    for ent in entities:
        c_name, c_type, sublabel = _canonical_entity_info(ent.name, ent.entity_type)
        node_key = (c_name, c_type, sublabel) if c_type == "lab" else (c_name, c_type)

        if node_key not in consolidated_nodes:
            node_id = f"node-{ent.id}"
            sub = sublabel or c_type
            consolidated_nodes[node_key] = {
                "id": node_id,
                "type": c_type,
                "label": c_name,
                "sublabel": sub,
                "source_document_id": ent.source_document_id,
                "source_chunk_id": ent.source_chunk_id,
            }
        db_id_to_node_id[ent.id] = consolidated_nodes[node_key]["id"]

    # Position consolidated nodes in concentric sectors by type
    typed_consolidated: dict[str, list[dict]] = {}
    for val in consolidated_nodes.values():
        typed_consolidated.setdefault(val["type"], []).append(val)

    center_x, center_y = 400, 240
    entity_idx = 0
    for c_type, group in typed_consolidated.items():
        base_angle = _ENTITY_TYPE_SECTORS.get(c_type, entity_idx * 1.0)
        for j, node_data in enumerate(group):
            angle = base_angle + (j * 0.3)
            radius = _LAYOUT_RADIUS + (j % 3) * 60
            x = int(center_x + radius * math.cos(angle))
            y = int(center_y + radius * math.sin(angle))
            nodes.append(
                GraphNode(
                    id=node_data["id"],
                    type=node_data["type"],
                    label=node_data["label"],
                    sublabel=node_data["sublabel"],
                    source_document_id=node_data["source_document_id"],
                    source_chunk_id=node_data["source_chunk_id"],
                    x=x,
                    y=y,
                )
            )
            entity_idx += 1

    # ── Build edges ───────────────────────────────────────────────────
    edges: list[GraphEdge] = []
    for rel in relations:
        from_id = db_id_to_node_id.get(rel.source_entity_id)
        to_id = db_id_to_node_id.get(rel.target_entity_id)
        if from_id and to_id:
            source_document_id, source_chunk_id = relation_provenance[rel.id]
            edges.append(
                GraphEdge(
                    id=f"edge-{rel.id}",
                    from_node=from_id,
                    to_node=to_id,
                    label=rel.relation_type,
                    source_document_id=source_document_id,
                    source_chunk_id=source_chunk_id,
                )
            )

    # ── Build reasoning paths ─────────────────────────────────────────
    reasoning_path: list[GraphPath] = []
    if relations:
        steps = []
        for rel in relations[:5]:
            from_id = db_id_to_node_id.get(rel.source_entity_id)
            to_id = db_id_to_node_id.get(rel.target_entity_id)
            provenance = relation_provenance.get(rel.id)
            if from_id and to_id and provenance:
                source_document_id, source_chunk_id = provenance
                steps.append(
                    GraphPathStep(
                        from_node=from_id,
                        to_node=to_id,
                        relation=rel.relation_type,
                        evidence=f"document:{source_document_id};chunk:{source_chunk_id}",
                        source_document_id=source_document_id,
                        source_chunk_id=source_chunk_id,
                    )
                )
        if steps:
            reasoning_path.append(
                GraphPath(
                    id="path-dynamic-001",
                    rationale="Persisted patient-scoped graph relations.",
                    steps=steps,
                )
            )

    metadata = GraphMetadata(
        patient_id=patient_id,
        updated_at=datetime.now(UTC).isoformat(),
        node_count=len(nodes),
        edge_count=len(edges),
    )

    return GraphDataResponse(
        patient_id=patient_id,
        nodes=nodes,
        edges=edges,
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
