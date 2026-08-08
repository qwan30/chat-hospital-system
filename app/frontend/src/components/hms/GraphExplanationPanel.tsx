import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Network, ArrowRight } from "lucide-react";

export interface GraphExplanationPath {
  from?: string;
  relation?: string;
  to?: string;
  confidence?: number;
  evidence?: string;
  document_id?: string;
  revision_set_id?: string;
  page_revision_id?: string;
  page?: number;
  start_offset?: number;
  end_offset?: number;
  alignment_status?: string;
}

export interface GraphExplanationData {
  summary?: string;
  rationale?: string;
  paths?: GraphExplanationPath[];
  nodes?: string[];
  [key: string]: unknown;
}

export interface GraphExplanationPanelProps {
  explanation?: unknown;
}

export function GraphExplanationPanel({ explanation }: GraphExplanationPanelProps) {
  if (!explanation) return null;

  const data: GraphExplanationData =
    typeof explanation === "string"
      ? { summary: explanation }
      : (explanation as GraphExplanationData);

  const summary = data.summary ?? data.rationale;
  const paths = Array.isArray(data.paths) ? data.paths : [];

  if (!summary && paths.length === 0) return null;

  return (
    <Card className="mt-3 p-3.5 bg-muted/40 border border-border/80 text-xs space-y-3">
      <div className="flex items-center justify-between font-semibold text-foreground">
        <div className="flex items-center gap-1.5">
          <Network className="h-3.5 w-3.5 text-ai" aria-hidden="true" />
          <span>Graph Explanation &amp; Reasoning</span>
        </div>
        {paths.length > 0 && (
          <Badge variant="outline" className="text-[10px] py-0">
            {paths.length} {paths.length === 1 ? "hop" : "hops"}
          </Badge>
        )}
      </div>

      {summary && (
        <p className="leading-relaxed text-muted-foreground whitespace-pre-wrap">
          {String(summary)}
        </p>
      )}

      {paths.length > 0 && (
        <div className="space-y-2 pt-1 border-t border-border/50">
          {paths.map((p, index) => (
            <div key={index} className="p-2 rounded bg-card border border-border/60 space-y-1">
              <div className="flex items-center gap-1.5 font-medium text-foreground flex-wrap">
                <span>{p.from ?? "Unknown"}</span>
                <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" aria-hidden="true" />
                <Badge
                  variant="secondary"
                  className="text-[10px] px-1.5 py-0 bg-primary/10 text-primary"
                >
                  {p.relation ?? "related_to"}
                </Badge>
                <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" aria-hidden="true" />
                <span>{p.to ?? "Unknown"}</span>
              </div>
              <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                {p.confidence !== undefined && (
                  <span>Confidence: {Math.round((Number(p.confidence) || 0) * 100)}%</span>
                )}
                {p.evidence && <span className="truncate">Evidence: {p.evidence}</span>}
              </div>
              {(p.document_id ||
                p.revision_set_id ||
                p.page_revision_id ||
                p.page !== undefined) && (
                <div className="flex flex-wrap gap-x-3 gap-y-1 border-t pt-1 text-[11px] text-muted-foreground">
                  {p.document_id && <span>Document: {p.document_id}</span>}
                  {p.revision_set_id && <span>Revision: {p.revision_set_id}</span>}
                  {p.page_revision_id && <span>Page revision: {p.page_revision_id}</span>}
                  {p.page !== undefined && <span>Page: {p.page}</span>}
                  {p.start_offset !== undefined && p.end_offset !== undefined && (
                    <span>
                      Offsets: {p.start_offset}-{p.end_offset}
                    </span>
                  )}
                  {p.alignment_status === "aligned" &&
                  p.page_revision_id &&
                  p.page !== undefined &&
                  p.start_offset !== undefined &&
                  p.end_offset !== undefined ? (
                    <span className="font-medium text-success">Exact evidence locator</span>
                  ) : p.alignment_status && p.alignment_status !== "aligned" ? (
                    <span className="font-medium text-warning">Geometry {p.alignment_status}</span>
                  ) : null}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
