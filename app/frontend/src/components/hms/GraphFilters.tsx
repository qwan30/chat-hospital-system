import React from "react";
import type { DocumentGraphFilters } from "@/lib/api/document-graph";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

export const DEFAULT_GRAPH_FILTERS: DocumentGraphFilters = {
  node_limit: 50,
  edge_limit: 100,
  hop_depth: 2,
  entity_types: [],
  relation_types: [],
  min_confidence: 0,
  document_scope: [],
  layout: "force",
  include_superseded: false,
};

export type GraphFilterKey = keyof DocumentGraphFilters;

export function serializeGraphFilters(filters: DocumentGraphFilters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.node_limit !== undefined) params.append("node_limit", String(filters.node_limit));
  if (filters.edge_limit !== undefined) params.append("edge_limit", String(filters.edge_limit));
  if (filters.hop_depth !== undefined) params.append("hop_depth", String(filters.hop_depth));
  if (filters.min_confidence !== undefined)
    params.append("min_confidence", String(filters.min_confidence));
  if (filters.entity_types) {
    filters.entity_types.forEach((t) => params.append("entity_types", t));
  }
  if (filters.relation_types) {
    filters.relation_types.forEach((t) => params.append("relation_types", t));
  }
  if (filters.document_scope) {
    filters.document_scope.forEach((doc) => params.append("document_scope", doc));
  }
  if (filters.approved_revision_set_id) {
    params.append("approved_revision_set_id", filters.approved_revision_set_id);
  }
  if (filters.date_from) params.append("date_from", filters.date_from);
  if (filters.date_to) params.append("date_to", filters.date_to);
  if (filters.layout) params.append("layout", filters.layout);
  if (filters.include_superseded !== undefined) {
    params.append("include_superseded", String(filters.include_superseded));
  }
  return params;
}

export interface SupersededEvidenceItem {
  id: string;
  label: string;
  date?: string;
  text?: string;
  rationale?: string;
}

export interface SourceBackedPathItem {
  id: string;
  path: string[];
  evidence?: string;
  confidence?: number;
  rationale?: string;
  source?: string;
}

export interface FinalCitationItem {
  id: string;
  title: string;
  source: string;
  snippet?: string;
}

export interface GraphFiltersProps {
  filters: DocumentGraphFilters;
  onChange: (filters: DocumentGraphFilters) => void;
  capabilities?: string[] | Record<string, unknown>;
  supportedFilters?: readonly GraphFilterKey[];
  supersededEvidenceList?: SupersededEvidenceItem[];
  sourceBackedPaths?: SourceBackedPathItem[];
  finalCitations?: FinalCitationItem[];
}

export function GraphFilters({
  filters,
  onChange,
  capabilities,
  supportedFilters,
  supersededEvidenceList = [],
  sourceBackedPaths = [],
  finalCitations = [],
}: GraphFiltersProps) {
  const supports = (key: GraphFilterKey) => supportedFilters?.includes(key) ?? true;
  const canReadSuperseded = React.useMemo(() => {
    if (!capabilities) return false;
    if (Array.isArray(capabilities)) {
      return capabilities.includes("superseded_evidence.read");
    }
    if (typeof capabilities === "object") {
      const perms = (capabilities["permissions"] || capabilities["grants"]) as string[] | undefined;
      if (Array.isArray(perms) && perms.includes("superseded_evidence.read")) {
        return true;
      }
      return Boolean(capabilities["superseded_evidence.read"]);
    }
    return false;
  }, [capabilities]);

  const handleToggleSuperseded = (checked: boolean) => {
    onChange({
      ...filters,
      include_superseded: checked,
    });
  };

  const handleLayoutChange = (newLayout: "force" | "timeline" | "hierarchical") => {
    onChange({
      ...filters,
      layout: newLayout,
    });
  };

  return (
    <div className="space-y-6 text-sm">
      <Card className="p-4 space-y-4">
        <h3 className="font-semibold text-foreground">Graph Controls</h3>

        {supports("node_limit") && (
          <div className="space-y-2">
            <Label htmlFor="node-limit-slider">Node Limit: {filters.node_limit ?? 50}</Label>
            <Slider
              id="node-limit-slider"
              aria-label="Node Limit"
              value={[filters.node_limit ?? 50]}
              min={10}
              max={200}
              step={10}
              onValueChange={(vals) => onChange({ ...filters, node_limit: vals[0] })}
            />
          </div>
        )}

        {supports("edge_limit") && (
          <div className="space-y-2">
            <Label htmlFor="edge-limit-slider">Edge Limit: {filters.edge_limit ?? 100}</Label>
            <Slider
              id="edge-limit-slider"
              aria-label="Edge Limit"
              value={[filters.edge_limit ?? 100]}
              min={10}
              max={500}
              step={10}
              onValueChange={(vals) => onChange({ ...filters, edge_limit: vals[0] })}
            />
          </div>
        )}

        {supports("hop_depth") && (
          <div className="space-y-2">
            <Label htmlFor="hop-depth-slider">Hop Depth: {filters.hop_depth ?? 2}</Label>
            <Slider
              id="hop-depth-slider"
              aria-label="Hop Depth"
              value={[filters.hop_depth ?? 2]}
              min={1}
              max={5}
              step={1}
              onValueChange={(vals) => onChange({ ...filters, hop_depth: vals[0] })}
            />
          </div>
        )}

        {supports("min_confidence") && (
          <div className="space-y-2">
            <Label htmlFor="min-conf-slider">
              Minimum Confidence: {filters.min_confidence ?? 0}
            </Label>
            <Slider
              id="min-conf-slider"
              aria-label="Minimum Confidence"
              value={[filters.min_confidence ?? 0]}
              min={0}
              max={1}
              step={0.05}
              onValueChange={(vals) => onChange({ ...filters, min_confidence: vals[0] })}
            />
          </div>
        )}

        {supports("layout") && (
          <div className="space-y-2">
            <Label id="layout-select-label">Layout</Label>
            <div className="flex gap-2" role="group" aria-labelledby="layout-select-label">
              {(["force", "timeline", "hierarchical"] as const).map((l) => (
                <button
                  key={l}
                  type="button"
                  aria-label={`Select layout ${l}`}
                  onClick={() => handleLayoutChange(l)}
                  className={`px-3 py-1 text-xs rounded-md border capitalize ${
                    filters.layout === l
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-background text-foreground"
                  }`}
                >
                  {l}
                </button>
              ))}
            </div>
          </div>
        )}

        {supports("include_superseded") && canReadSuperseded && (
          <div className="flex items-center justify-between pt-2 border-t">
            <Label htmlFor="include-superseded" className="cursor-pointer">
              Include Superseded
            </Label>
            <Switch
              id="include-superseded"
              aria-label="Include Superseded"
              checked={Boolean(filters.include_superseded)}
              onCheckedChange={handleToggleSuperseded}
            />
          </div>
        )}
      </Card>

      {canReadSuperseded && filters.include_superseded && supersededEvidenceList.length > 0 && (
        <Card className="p-4 border-warning/40 bg-warning/5 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-xs text-warning uppercase tracking-wider">
              Audit-only superseded evidence
            </h4>
            <Badge variant="outline" className="text-[10px]">
              {supersededEvidenceList.length} items
            </Badge>
          </div>
          <ul className="space-y-2 text-xs">
            {supersededEvidenceList.map((item) => (
              <li key={item.id} className="p-2 bg-background/80 rounded border">
                <div className="font-medium text-foreground">{item.label}</div>
                {item.text && <div className="text-muted-foreground mt-0.5">{item.text}</div>}
              </li>
            ))}
          </ul>
        </Card>
      )}

      {(sourceBackedPaths.length > 0 || finalCitations.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="p-4 space-y-3">
            <h4 className="font-semibold text-foreground text-sm border-b pb-2">
              Source-backed paths
            </h4>
            {sourceBackedPaths.length === 0 ? (
              <p className="text-xs text-muted-foreground">No source-backed paths</p>
            ) : (
              <ul className="space-y-3">
                {sourceBackedPaths.map((p) => (
                  <li key={p.id} className="text-xs space-y-1 p-2 bg-muted/30 rounded border">
                    <div className="font-medium flex items-center gap-1 flex-wrap">
                      {p.path.map((step, idx) => (
                        <React.Fragment key={idx}>
                          <span>{step}</span>
                          {idx < p.path.length - 1 && (
                            <span className="text-muted-foreground">→</span>
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                    {p.source && (
                      <div className="text-muted-foreground font-mono text-[11px]">
                        Source: {p.source}
                      </div>
                    )}
                    {p.evidence && (
                      <div className="text-muted-foreground">Evidence: {p.evidence}</div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card className="p-4 space-y-3">
            <h4 className="font-semibold text-foreground text-sm border-b pb-2">Final citations</h4>
            {finalCitations.length === 0 ? (
              <p className="text-xs text-muted-foreground">No final citations</p>
            ) : (
              <ul className="space-y-3">
                {finalCitations.map((c) => (
                  <li key={c.id} className="text-xs p-2 bg-muted/30 rounded border space-y-1">
                    <div className="font-medium text-foreground">{c.title}</div>
                    <div className="text-[11px] text-muted-foreground">{c.source}</div>
                    {c.snippet && (
                      <div className="text-muted-foreground italic">&ldquo;{c.snippet}&rdquo;</div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
