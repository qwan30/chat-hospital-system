import { useMemo, useState } from "react";
import {
  Heart,
  Stethoscope,
  Activity,
  Pill,
  AlertTriangle,
  FlaskConical,
  Maximize2,
  Minus,
  Plus,
  RotateCcw,
} from "lucide-react";
import type { GraphDataResponse as GraphData, GraphNode, GraphEdge } from "@/lib/api/graph";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type NodeType = GraphNode["type"];

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

export function GraphCanvas({ data }: { data: GraphData }) {
  const [hover, setHover] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [hidden, setHidden] = useState<Set<NodeType>>(new Set());
  const [zoom, setZoom] = useState(1);

  const active = selected ?? hover;

  const adjacency = useMemo(() => {
    const map = new Map<string, Set<string>>();
    for (const e of data.edges) {
      if (!map.has(e.from_node)) map.set(e.from_node, new Set());
      if (!map.has(e.to_node)) map.set(e.to_node, new Set());
      map.get(e.from_node)!.add(e.to_node);
      map.get(e.to_node)!.add(e.from_node);
    }
    return map;
  }, [data.edges]);

  const visibleNodes = data.nodes.filter((n) => !hidden.has(n.type));
  const visibleIds = new Set(visibleNodes.map((n) => n.id));
  const visibleEdges = data.edges.filter(
    (e) => visibleIds.has(e.from_node) && visibleIds.has(e.to_node),
  );

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

  const vbW = 920;
  const vbH = 480;
  const z = zoom;
  const cx = vbW / 2;
  const cy = vbH / 2;
  const viewBox = `${cx - vbW / 2 / z} ${cy - vbH / 2 / z} ${vbW / z} ${vbH / z}`;

  return (
    <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">
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
                  <Icon className="h-2.5 w-2.5" />
                </span>
                <span className="capitalize">{s.label}</span>
                <span className="ml-0.5 text-[10px] text-muted-foreground">{counts[t] ?? 0}</span>
              </button>
            );
          })}
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setZoom((z) => Math.max(0.5, +(z - 0.1).toFixed(2)))}
            aria-label="Zoom out"
          >
            <Minus className="h-4 w-4" />
          </Button>
          <span className="w-10 text-center text-xs tabular-nums text-muted-foreground">
            {Math.round(zoom * 100)}%
          </span>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setZoom((z) => Math.min(2, +(z + 0.1).toFixed(2)))}
            aria-label="Zoom in"
          >
            <Plus className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => {
              setZoom(1);
              setSelected(null);
              setHidden(new Set());
            }}
            aria-label="Reset view"
          >
            <RotateCcw className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" aria-label="Fit">
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Canvas */}
      <div className="relative">
        <svg viewBox={viewBox} className="h-[520px] w-full select-none">
          <defs>
            <pattern id="graph-grid" width="32" height="32" patternUnits="userSpaceOnUse">
              <circle cx="1" cy="1" r="1" className="fill-border" />
            </pattern>
            <radialGradient id="graph-fade" cx="50%" cy="50%" r="60%">
              <stop offset="0%" stopColor="white" stopOpacity="0" />
              <stop offset="100%" stopColor="white" stopOpacity="1" />
            </radialGradient>
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

          <rect x="0" y="0" width={vbW} height={vbH} fill="url(#graph-grid)" opacity="0.6" />

          {/* Edges */}
          {visibleEdges.map((e) => {
            const from = data.nodes.find((n) => n.id === e.from_node)!;
            const to = data.nodes.find((n) => n.id === e.to_node)!;
            const midX = (from.x + to.x) / 2;
            const midY = (from.y + to.y) / 2;
            const dimmed = edgeDimmed(e.from_node, e.to_node);
            const highlighted = active && !dimmed;
            const dx = to.x - from.x;
            const dy = to.y - from.y;
            const len = Math.sqrt(dx * dx + dy * dy) || 1;
            // Trim line so the arrow doesn't overlap the node card
            const pad = 78;
            const x2 = to.x - (dx / len) * pad;
            const y2 = to.y - (dy / len) * pad;
            const x1 = from.x + (dx / len) * pad;
            const y1 = from.y + (dy / len) * pad;
            return (
              <g key={e.id} className={cn("transition-opacity", dimmed && "opacity-15")}>
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  className={cn(highlighted ? "stroke-primary" : "stroke-border")}
                  strokeWidth={highlighted ? 2 : 1.25}
                  markerEnd={highlighted ? "url(#arrow-active)" : "url(#arrow)"}
                />
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
              </g>
            );
          })}

          {/* Nodes */}
          {visibleNodes.map((n) => {
            const s = nodeStyle[n.type];
            const isActive = active === n.id;
            const dimmed = isDimmed(n.id);
            return (
              <g
                key={n.id}
                transform={`translate(${n.x}, ${n.y})`}
                className={cn("cursor-pointer transition-opacity", dimmed && "opacity-25")}
                onMouseEnter={() => setHover(n.id)}
                onMouseLeave={() => setHover(null)}
                onClick={() => setSelected((cur) => (cur === n.id ? null : n.id))}
              >
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
          {active
            ? "Click node again to deselect"
            : "Hover or click a node to highlight relationships"}
        </div>
        <div className="pointer-events-none absolute bottom-3 right-3 rounded-md border bg-background/80 px-2 py-1 text-[11px] text-muted-foreground backdrop-blur">
          {visibleNodes.length} nodes · {visibleEdges.length} edges
        </div>
      </div>
    </div>
  );
}
