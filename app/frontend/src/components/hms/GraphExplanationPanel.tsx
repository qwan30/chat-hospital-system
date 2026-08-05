import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Network, ArrowRight } from "lucide-react";

export interface GraphExplanationPath {
  from?: string;
  relation?: string;
  to?: string;
  confidence?: number;
  evidence?: string;
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
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
