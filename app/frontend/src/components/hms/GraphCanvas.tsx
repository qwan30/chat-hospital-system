import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Heart,
  Stethoscope,
  Activity,
  Pill,
  AlertTriangle,
  FlaskConical,
  Maximize2,
  Minimize2,
  Minus,
  Plus,
  RotateCcw,
} from "lucide-react";
import type {
  GraphDataResponse as GraphData,
  GraphNode,
  GraphEdge,
  GraphProvenance,
} from "@/lib/api/graph";
import type { DocumentGraphFilters } from "@/lib/api/document-graph";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type NodeType = GraphNode["type"];

type ProvenanceSource = Pick<
  GraphNode,
  | "source_document_id"
  | "source_chunk_id"
  | "source_generation_id"
  | "source_revision_set_id"
  | "source_page_revision_id"
  | "source_page"
  | "source_start_offset"
  | "source_end_offset"
  | "source_bounding_boxes"
  | "source_alignment_status"
>;

function provenanceFor(source: ProvenanceSource): GraphProvenance {
  return {
    document_id: source.source_document_id,
    chunk_id: source.source_chunk_id,
    generation_id: source.source_generation_id,
    revision_set_id: source.source_revision_set_id,
    page_revision_id: source.source_page_revision_id,
    page: source.source_page,
    start_offset: source.source_start_offset,
    end_offset: source.source_end_offset,
    bounding_boxes: source.source_bounding_boxes,
    alignment_status: source.source_alignment_status,
  };
}

function provenanceTitle(provenance: GraphProvenance): string {
  const values = [
    provenance.document_id && `document:${provenance.document_id}`,
    provenance.revision_set_id && `revision:${provenance.revision_set_id}`,
    provenance.page_revision_id && `page-revision:${provenance.page_revision_id}`,
    provenance.page !== undefined && provenance.page !== null && `page:${provenance.page}`,
    provenance.chunk_id && `chunk:${provenance.chunk_id}`,
  ].filter(Boolean);
  return values.length > 0 ? `Provenance — ${values.join("; ")}` : "Provenance unavailable";
}

/* ------------------------------------------------------------------ */
/*  Style map                                                          */
/* ------------------------------------------------------------------ */
const nodeStyle: Record<
  NodeType,
  { fill: string; ring: string; chip: string; label: string; Icon: typeof Heart }
> = {
  patient: {
    fill: "fill-primary",
    ring: "stroke-primary",
    chip: "bg-primary text-primary-foreground",
    label: "Patient",
    Icon: Heart,
  },
  encounter: {
    fill: "fill-info",
    ring: "stroke-info",
    chip: "bg-info text-white",
    label: "Encounter",
    Icon: Stethoscope,
  },
  diagnosis: {
    fill: "fill-ai",
    ring: "stroke-ai",
    chip: "bg-ai text-ai-foreground",
    label: "Diagnosis",
    Icon: Activity,
  },
  medication: {
    fill: "fill-citation",
    ring: "stroke-citation",
    chip: "bg-citation text-citation-foreground",
    label: "Medication",
    Icon: Pill,
  },
  allergy: {
    fill: "fill-destructive",
    ring: "stroke-destructive",
    chip: "bg-destructive text-destructive-foreground",
    label: "Allergy",
    Icon: AlertTriangle,
  },
  lab: {
    fill: "fill-warning",
    ring: "stroke-warning",
    chip: "bg-warning text-white",
    label: "Lab",
    Icon: FlaskConical,
  },
};

/* ------------------------------------------------------------------ */
/*  Force-directed layout helpers                                       */
/* ------------------------------------------------------------------ */
interface LayoutNode {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  type: string;
  label: string;
  sublabel?: string | null;
}

function forceLayout(
  rawNodes: GraphNode[],
  edges: GraphEdge[],
  iterations = 120,
): Map<string, { x: number; y: number }> {
  if (rawNodes.length === 0) return new Map();

  // Group nodes by type for initial ring placement
  const typeGroups = new Map<string, GraphNode[]>();
  for (const n of rawNodes) {
    if (!typeGroups.has(n.type)) typeGroups.set(n.type, []);
    typeGroups.get(n.type)!.push(n);
  }

  const typeOrder = ["patient", "encounter", "diagnosis", "medication", "allergy", "lab"];
  const totalNodes = rawNodes.length;

  // Calculate a bounding area that scales with node count
  const baseRadius = Math.max(300, Math.sqrt(totalNodes) * 80);

  // Place nodes in concentric rings by type
  const nodes: LayoutNode[] = [];
  const nodeMap = new Map<string, LayoutNode>();

  let globalIdx = 0;
  const orderedTypes = typeOrder.filter((t) => typeGroups.has(t));

  for (let tIdx = 0; tIdx < orderedTypes.length; tIdx++) {
    const type = orderedTypes[tIdx];
    const group = typeGroups.get(type) || [];
    const ringRadius = baseRadius * (0.3 + (tIdx / Math.max(orderedTypes.length - 1, 1)) * 0.7);

    for (let i = 0; i < group.length; i++) {
      const angle = (2 * Math.PI * i) / group.length + (tIdx * Math.PI) / 6;
      // Add some jitter so nodes don't sit exactly on top of each other
      const jitterX = (Math.random() - 0.5) * 40;
      const jitterY = (Math.random() - 0.5) * 40;

      const ln: LayoutNode = {
        id: group[i].id,
        x: ringRadius * Math.cos(angle) + jitterX,
        y: ringRadius * Math.sin(angle) + jitterY,
        vx: 0,
        vy: 0,
        type: group[i].type,
        label: group[i].label,
        sublabel: group[i].sublabel,
      };
      nodes.push(ln);
      nodeMap.set(ln.id, ln);
      globalIdx++;
    }
  }

  // Build edge lookup
  const edgePairs: [LayoutNode, LayoutNode][] = [];
  for (const e of edges) {
    const from = nodeMap.get(e.from_node);
    const to = nodeMap.get(e.to_node);
    if (from && to) edgePairs.push([from, to]);
  }

  // Run simulation
  const repulsionStrength = 50000;
  const attractionStrength = 0.003;
  const idealEdgeLen = 200;
  const damping = 0.85;
  const minDistance = 160; // Minimum distance between node centers to prevent overlap

  for (let iter = 0; iter < iterations; iter++) {
    const temp = 1 - iter / iterations; // cooling

    // Repulsion between all pairs
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[j].x - nodes[i].x;
        const dy = nodes[j].y - nodes[i].y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;

        // Stronger repulsion if nodes are closer than minDistance
        const force = (repulsionStrength / (dist * dist)) * temp;

        // Extra push if overlapping
        let extraForce = 0;
        if (dist < minDistance) {
          extraForce = ((minDistance - dist) / minDistance) * 30 * temp;
        }

        const totalForce = force + extraForce;
        const fx = (dx / dist) * totalForce;
        const fy = (dy / dist) * totalForce;

        nodes[i].vx -= fx;
        nodes[i].vy -= fy;
        nodes[j].vx += fx;
        nodes[j].vy += fy;
      }
    }

    // Attraction along edges
    for (const [a, b] of edgePairs) {
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const delta = dist - idealEdgeLen;
      const force = delta * attractionStrength * temp;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      a.vx += fx;
      a.vy += fy;
      b.vx -= fx;
      b.vy -= fy;
    }

    // Apply velocity
    for (const n of nodes) {
      n.vx *= damping;
      n.vy *= damping;
      n.x += n.vx;
      n.y += n.vy;
    }
  }

  const result = new Map<string, { x: number; y: number }>();
  for (const n of nodes) {
    result.set(n.id, { x: n.x, y: n.y });
  }
  return result;
}

/**
 * Calculates the offset from the center of a node of width w and height h
 * to its boundary along the vector (dx, dy).
 * Margin adjusts the target distance (e.g. 4px padding so arrows touch cleanly).
 */
function getIntersectionOffset(
  dx: number,
  dy: number,
  w: number,
  h: number,
  margin = 4,
): { x: number; y: number } {
  if (dx === 0 && dy === 0) return { x: 0, y: 0 };

  const halfW = w / 2 + margin;
  const halfH = h / 2 + margin;

  const absDx = Math.abs(dx);
  const absDy = Math.abs(dy);

  // Intersection times with horizontal and vertical boundaries
  const tx = absDx > 0 ? halfW / absDx : Infinity;
  const ty = absDy > 0 ? halfH / absDy : Infinity;

  // The first boundary it hits is the actual intersection point
  const t = Math.min(tx, ty);

  return {
    x: dx * t,
    y: dy * t,
  };
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */
export function GraphCanvas({
  data,
  filters,
}: {
  data: GraphData;
  filters?: DocumentGraphFilters;
}) {
  const [hover, setHover] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [hidden, setHidden] = useState<Set<NodeType>>(new Set());
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showCooccurrence, setShowCooccurrence] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Camera state: pan + zoom
  const [camera, setCamera] = useState({ x: 0, y: 0, zoom: 1 });

  // Drag state for nodes
  const [dragging, setDragging] = useState<string | null>(null);
  const dragStart = useRef({ mx: 0, my: 0, nx: 0, ny: 0 });

  // Pan state
  const [panning, setPanning] = useState(false);
  const panStart = useRef({ mx: 0, my: 0, cx: 0, cy: 0 });

  const active = selected ?? hover;

  // Filter edges based on co-occurrence toggle
  const filteredEdges = useMemo(() => {
    if (showCooccurrence) return data.edges;
    return data.edges.filter((e) => e.label !== "mentioned_with");
  }, [data.edges, showCooccurrence]);

  // Run force layout on the data
  const layoutPositions = useMemo(
    () => forceLayout(data.nodes, filteredEdges, 150),
    [data.nodes, filteredEdges],
  );

  // Mutable node positions (for drag)
  const [nodePositions, setNodePositions] = useState<Map<string, { x: number; y: number }>>(
    () => new Map(layoutPositions),
  );

  // Sync when layout changes (new data)
  useEffect(() => {
    setNodePositions(new Map(layoutPositions));
  }, [layoutPositions]);

  const adjacency = useMemo(() => {
    const map = new Map<string, Set<string>>();
    for (const e of filteredEdges) {
      if (!map.has(e.from_node)) map.set(e.from_node, new Set());
      if (!map.has(e.to_node)) map.set(e.to_node, new Set());
      map.get(e.from_node)!.add(e.to_node);
      map.get(e.to_node)!.add(e.from_node);
    }
    return map;
  }, [filteredEdges]);

  const visibleNodes = useMemo(() => {
    const nodes = data.nodes.filter((n) => !hidden.has(n.type as NodeType));
    if (filters?.node_limit !== undefined && filters.node_limit > 0) {
      return nodes.slice(0, filters.node_limit);
    }
    return nodes;
  }, [data.nodes, hidden, filters?.node_limit]);
  const visibleIds = useMemo(() => new Set(visibleNodes.map((n) => n.id)), [visibleNodes]);
  const visibleEdges = useMemo(() => {
    const edges = filteredEdges.filter(
      (e) => visibleIds.has(e.from_node) && visibleIds.has(e.to_node),
    );
    if (filters?.edge_limit !== undefined && filters.edge_limit > 0) {
      return edges.slice(0, filters.edge_limit);
    }
    return edges;
  }, [filteredEdges, visibleIds, filters?.edge_limit]);

  const counts = data.nodes.reduce<Record<string, number>>((acc, n) => {
    acc[n.type] = (acc[n.type] ?? 0) + 1;
    return acc;
  }, {});

  const isDimmed = (id: string) => {
    if (!active) return false;
    if (id === active) return false;
    return !adjacency.get(active)?.has(id);
  };

  const edgeDimmed = (from: string, to: string) => {
    if (!active) return false;
    return from !== active && to !== active;
  };

  const toggleType = (t: NodeType) => {
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(t)) next.delete(t);
      else next.add(t);
      return next;
    });
  };

  /* ---- Fit all visible nodes ---- */
  const fitView = useCallback(() => {
    const positions = Array.from(nodePositions.entries())
      .filter(([id]) => visibleIds.has(id))
      .map(([, pos]) => pos);

    if (positions.length === 0) return;

    const pad = 120;
    let minX = Infinity,
      maxX = -Infinity,
      minY = Infinity,
      maxY = -Infinity;
    for (const p of positions) {
      if (p.x < minX) minX = p.x;
      if (p.x > maxX) maxX = p.x;
      if (p.y < minY) minY = p.y;
      if (p.y > maxY) maxY = p.y;
    }

    minX -= pad;
    maxX += pad;
    minY -= pad;
    maxY += pad;

    const contentW = maxX - minX || 1;
    const contentH = maxY - minY || 1;

    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const svgW = rect.width;
    const svgH = rect.height;

    const zoom = Math.min(svgW / contentW, svgH / contentH, 2);
    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;

    setCamera({ x: cx, y: cy, zoom });
  }, [nodePositions, visibleIds]);

  // Auto-fit on initial load
  const initialFit = useRef(false);
  useEffect(() => {
    if (!initialFit.current && nodePositions.size > 0) {
      initialFit.current = true;
      // Small delay so the SVG has rendered
      requestAnimationFrame(() => fitView());
    }
  }, [nodePositions, fitView]);

  /* ---- Fullscreen toggle ---- */
  const toggleFullscreen = useCallback(() => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current
        .requestFullscreen()
        .then(() => setIsFullscreen(true))
        .catch(() => {});
    } else {
      document
        .exitFullscreen()
        .then(() => setIsFullscreen(false))
        .catch(() => {});
    }
  }, []);

  useEffect(() => {
    const handler = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  /* ---- Compute viewBox from camera ---- */
  const getViewBox = useCallback(() => {
    const svg = svgRef.current;
    if (!svg) return "-500 -500 1000 1000";
    const rect = svg.getBoundingClientRect();
    const w = rect.width / camera.zoom;
    const h = rect.height / camera.zoom;
    return `${camera.x - w / 2} ${camera.y - h / 2} ${w} ${h}`;
  }, [camera]);

  /* ---- Mouse wheel for zoom ---- */
  const handleWheel = useCallback((e: React.WheelEvent<SVGSVGElement>) => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 0.92 : 1.08;
    setCamera((c) => ({
      ...c,
      zoom: Math.min(4, Math.max(0.1, c.zoom * factor)),
    }));
  }, []);

  /* ---- SVG coordinate conversion ---- */
  const svgPoint = useCallback((clientX: number, clientY: number) => {
    const svg = svgRef.current;
    if (!svg) return { x: 0, y: 0 };
    const pt = svg.createSVGPoint();
    pt.x = clientX;
    pt.y = clientY;
    const ctm = svg.getScreenCTM();
    if (!ctm) return { x: 0, y: 0 };
    const svgPt = pt.matrixTransform(ctm.inverse());
    return { x: svgPt.x, y: svgPt.y };
  }, []);

  /* ---- Node drag handlers ---- */
  const handleNodeMouseDown = useCallback(
    (e: React.MouseEvent, nodeId: string) => {
      e.stopPropagation();
      e.preventDefault();
      const pos = nodePositions.get(nodeId);
      if (!pos) return;
      const svgPos = svgPoint(e.clientX, e.clientY);
      dragStart.current = { mx: svgPos.x, my: svgPos.y, nx: pos.x, ny: pos.y };
      setDragging(nodeId);
    },
    [nodePositions, svgPoint],
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (dragging) {
        const svgPos = svgPoint(e.clientX, e.clientY);
        const dx = svgPos.x - dragStart.current.mx;
        const dy = svgPos.y - dragStart.current.my;
        setNodePositions((prev) => {
          const next = new Map(prev);
          next.set(dragging, {
            x: dragStart.current.nx + dx,
            y: dragStart.current.ny + dy,
          });
          return next;
        });
        return;
      }
      if (panning) {
        const dx = (e.clientX - panStart.current.mx) / camera.zoom;
        const dy = (e.clientY - panStart.current.my) / camera.zoom;
        setCamera((c) => ({
          ...c,
          x: panStart.current.cx - dx,
          y: panStart.current.cy - dy,
        }));
      }
    },
    [dragging, panning, camera.zoom, svgPoint],
  );

  const handleMouseUp = useCallback(
    (e: React.MouseEvent) => {
      if (dragging) {
        // If we barely moved, treat as a click
        const svgPos = svgPoint(e.clientX, e.clientY);
        const dx = Math.abs(svgPos.x - dragStart.current.mx);
        const dy = Math.abs(svgPos.y - dragStart.current.my);
        if (dx < 3 && dy < 3) {
          setSelected((cur) => (cur === dragging ? null : dragging));
        }
        setDragging(null);
      }
      if (panning) {
        setPanning(false);
      }
    },
    [dragging, panning, svgPoint],
  );

  /* ---- Pan handlers (background drag) ---- */
  const handleBgMouseDown = useCallback(
    (e: React.MouseEvent) => {
      // Only left button
      if (e.button !== 0) return;
      panStart.current = { mx: e.clientX, my: e.clientY, cx: camera.x, cy: camera.y };
      setPanning(true);
    },
    [camera],
  );

  /* ---- Get node position (use layoutPositions as fallback) ---- */
  const getPos = useCallback(
    (id: string) => nodePositions.get(id) || { x: 0, y: 0 },
    [nodePositions],
  );

  return (
    <div
      ref={containerRef}
      className={cn(
        "overflow-hidden rounded-2xl border bg-card shadow-sm",
        isFullscreen && "rounded-none border-0",
      )}
    >
      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b bg-muted/30 px-4 py-2.5">
        <div className="flex flex-wrap items-center gap-1.5">
          {(Object.keys(nodeStyle) as NodeType[]).map((t) => {
            const s = nodeStyle[t];
            const off = hidden.has(t);
            const Icon = s.Icon;
            return (
              <button
                key={t}
                onClick={() => toggleType(t)}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition",
                  off
                    ? "border-dashed bg-background text-muted-foreground opacity-60"
                    : "border-transparent bg-background shadow-sm hover:shadow",
                )}
              >
                <span
                  className={cn(
                    "inline-flex h-4 w-4 items-center justify-center rounded-full",
                    s.chip,
                  )}
                >
                  <Icon className="h-2.5 w-2.5" aria-hidden="true" />
                </span>
                <span className="capitalize">{s.label}</span>
                <span className="ml-0.5 text-[10px] text-muted-foreground">{counts[t] ?? 0}</span>
              </button>
            );
          })}
          <div className="mx-1.5 h-4 w-[1px] bg-border shrink-0 self-center" />
          <button
            onClick={() => setShowCooccurrence((prev) => !prev)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition",
              !showCooccurrence
                ? "border-dashed bg-background text-muted-foreground opacity-60 hover:opacity-100"
                : "border-primary bg-primary/10 text-primary shadow-sm hover:bg-primary/20",
            )}
          >
            <span>Co-occurrence links</span>
            <span className="text-[10px] opacity-80">
              ({data.edges.filter((e) => e.label === "mentioned_with").length})
            </span>
          </button>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={() =>
              setCamera((c) => ({ ...c, zoom: Math.max(0.1, +(c.zoom - 0.1).toFixed(2)) }))
            }
            aria-label="Zoom out"
          >
            <Minus className="h-4 w-4" />
          </Button>
          <span className="w-10 text-center text-xs tabular-nums text-muted-foreground">
            {Math.round(camera.zoom * 100)}%
          </span>
          <Button
            variant="ghost"
            size="icon"
            onClick={() =>
              setCamera((c) => ({ ...c, zoom: Math.min(4, +(c.zoom + 0.1).toFixed(2)) }))
            }
            aria-label="Zoom in"
          >
            <Plus className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => {
              setCamera({ x: 0, y: 0, zoom: 1 });
              setSelected(null);
              setHidden(new Set());
              setNodePositions(new Map(layoutPositions));
            }}
            aria-label="Reset view"
          >
            <RotateCcw className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={fitView} aria-label="Fit all nodes">
            <Maximize2 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleFullscreen}
            aria-label={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
          >
            {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Canvas */}
      <div className="relative">
        <svg
          ref={svgRef}
          viewBox={getViewBox()}
          className={cn(
            "w-full select-none",
            isFullscreen ? "h-[calc(100vh-52px)]" : "h-[680px]",
            dragging ? "cursor-grabbing" : panning ? "cursor-grabbing" : "cursor-grab",
          )}
          onWheel={handleWheel}
          onMouseDown={handleBgMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={() => {
            setDragging(null);
            setPanning(false);
          }}
        >
          <defs>
            <pattern id="graph-grid" width="32" height="32" patternUnits="userSpaceOnUse">
              <circle cx="1" cy="1" r="1" className="fill-border" />
            </pattern>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto"
            >
              <path d="M0,0 L10,5 L0,10 z" className="fill-muted-foreground" />
            </marker>
            <marker
              id="arrow-active"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="7"
              markerHeight="7"
              orient="auto"
            >
              <path d="M0,0 L10,5 L0,10 z" className="fill-primary" />
            </marker>
            <filter id="node-shadow" x="-50%" y="-50%" width="200%" height="200%">
              <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.12" />
            </filter>
          </defs>

          {/* Infinite grid background */}
          <rect
            x="-10000"
            y="-10000"
            width="20000"
            height="20000"
            fill="url(#graph-grid)"
            opacity="0.4"
          />

          {/* Edges */}
          {visibleEdges.map((e) => {
            const provenance = provenanceFor(e);
            const from = getPos(e.from_node);
            const to = getPos(e.to_node);
            const midX = (from.x + to.x) / 2;
            const midY = (from.y + to.y) / 2;
            const dimmed = edgeDimmed(e.from_node, e.to_node);
            const highlighted = active && !dimmed;
            const dx = to.x - from.x;
            const dy = to.y - from.y;
            // Calculate dynamic padding offsets to align arrows perfectly with node borders
            const offsetFrom = getIntersectionOffset(dx, dy, 144, 44, 4);
            const offsetTo = getIntersectionOffset(dx, dy, 144, 44, 8); // slightly larger margin for arrowhead to sit perfectly

            const x1 = from.x + offsetFrom.x;
            const y1 = from.y + offsetFrom.y;
            const x2 = to.x - offsetTo.x;
            const y2 = to.y - offsetTo.y;
            return (
              <g
                key={e.id}
                data-testid={`graph-edge-${e.id}`}
                data-provenance-document-id={provenance.document_id ?? undefined}
                data-provenance-revision-id={provenance.revision_set_id ?? undefined}
                data-provenance-page-revision-id={provenance.page_revision_id ?? undefined}
                data-provenance-page={provenance.page ?? undefined}
                data-provenance-chunk-id={provenance.chunk_id ?? undefined}
                data-provenance-alignment-status={provenance.alignment_status ?? undefined}
                className={cn("transition-opacity", dimmed && "opacity-15")}
              >
                <title>{provenanceTitle(provenance)}</title>
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  className={cn(highlighted ? "stroke-primary" : "stroke-border")}
                  strokeWidth={highlighted ? 2 : 1.25}
                  markerEnd={highlighted ? "url(#arrow-active)" : "url(#arrow)"}
                />
                {/* Edge label – only show when not too zoomed out */}
                {camera.zoom > 0.3 && (
                  <g transform={`translate(${midX}, ${midY})`}>
                    <rect
                      x={-e.label.length * 3.2 - 6}
                      y={-9}
                      width={e.label.length * 6.4 + 12}
                      height={16}
                      rx={8}
                      className="fill-card stroke-border"
                      strokeWidth={0.75}
                    />
                    <text
                      textAnchor="middle"
                      y={3}
                      className={cn(
                        "text-[10px]",
                        highlighted ? "fill-primary font-medium" : "fill-muted-foreground",
                      )}
                    >
                      {e.label}
                    </text>
                  </g>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {visibleNodes.map((n) => {
            const s = nodeStyle[n.type as NodeType];
            if (!s) return null;
            const provenance = provenanceFor(n);
            const pos = getPos(n.id);
            const isActive = active === n.id;
            const dimmed = isDimmed(n.id);
            const isDraggingThis = dragging === n.id;
            return (
              <g
                key={n.id}
                data-testid={`graph-node-${n.id}`}
                data-provenance-document-id={provenance.document_id ?? undefined}
                data-provenance-revision-id={provenance.revision_set_id ?? undefined}
                data-provenance-page-revision-id={provenance.page_revision_id ?? undefined}
                data-provenance-page={provenance.page ?? undefined}
                data-provenance-chunk-id={provenance.chunk_id ?? undefined}
                data-provenance-alignment-status={provenance.alignment_status ?? undefined}
                transform={`translate(${pos.x}, ${pos.y})`}
                className={cn(
                  "transition-opacity",
                  dimmed && "opacity-25",
                  isDraggingThis ? "cursor-grabbing" : "cursor-grab",
                )}
                onMouseEnter={() => !dragging && setHover(n.id)}
                onMouseLeave={() => !dragging && setHover(null)}
                onMouseDown={(e) => handleNodeMouseDown(e, n.id)}
                style={{ pointerEvents: "all" }}
              >
                <title>{provenanceTitle(provenance)}</title>
                {isActive ? (
                  <rect
                    x={-78}
                    y={-26}
                    width={156}
                    height={52}
                    rx={14}
                    className={cn(s.fill, "opacity-20")}
                  />
                ) : null}
                <rect
                  x={-72}
                  y={-22}
                  width={144}
                  height={44}
                  rx={11}
                  className={cn("fill-card", s.ring)}
                  strokeWidth={isActive ? 2 : 1.25}
                  filter="url(#node-shadow)"
                />
                <rect x={-72} y={-22} width={6} height={44} rx={3} className={s.fill} />
                <circle cx={-54} cy={0} r={9} className={cn(s.fill)} />
                <text
                  textAnchor="start"
                  x={-40}
                  y={-3}
                  className="fill-foreground text-[11px] font-semibold pointer-events-none"
                >
                  {n.label.length > 18 ? n.label.slice(0, 17) + "…" : n.label}
                </text>
                {n.sublabel ? (
                  <text
                    textAnchor="start"
                    x={-40}
                    y={11}
                    className="fill-muted-foreground text-[10px] pointer-events-none"
                  >
                    {n.sublabel}
                  </text>
                ) : null}
              </g>
            );
          })}
        </svg>

        {/* Hint */}
        <div className="pointer-events-none absolute bottom-3 left-3 rounded-md border bg-background/80 px-2 py-1 text-[11px] text-muted-foreground backdrop-blur">
          {dragging
            ? "Release to drop node"
            : active
              ? "Click node again to deselect"
              : "Drag nodes to rearrange · Scroll to zoom · Drag background to pan"}
        </div>
        <div className="pointer-events-none absolute bottom-3 right-3 rounded-md border bg-background/80 px-2 py-1 text-[11px] text-muted-foreground backdrop-blur">
          {visibleNodes.length} nodes · {visibleEdges.length} edges
        </div>
      </div>
    </div>
  );
}
