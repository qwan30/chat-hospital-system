import { Card } from "@/components/ui/card";
import { FileText, ExternalLink } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { Badge } from "@/components/ui/badge";

export interface EvidenceItem {
  id: string;
  n: number;
  title: string;
  source: string;
  date: string;
  snippet: string;
  relevance: number;
}

export function EvidenceRail({ items }: { items: EvidenceItem[] }) {
  return (
    <div className="flex h-full flex-col">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">Evidence</h3>
        <Badge variant="secondary" className="bg-citation/10 text-citation">
          {items.length} citations
        </Badge>
      </div>
      <div className="space-y-3 overflow-y-auto pr-1">
        {items.map((it) => (
          <Card key={it.id} className="p-3">
            <div className="flex items-start gap-2">
              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-citation/10 font-mono text-[10px] font-semibold text-citation">
                [{it.n}]
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{it.title}</p>
                <p className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
                  <FileText className="h-3 w-3" />
                  {it.source} · {it.date}
                </p>
                <p className="mt-2 line-clamp-3 rounded-md bg-muted/60 p-2 text-xs leading-relaxed text-muted-foreground">
                  "{it.snippet}"
                </p>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
                    Relevance {(it.relevance * 100).toFixed(0)}%
                  </span>
                  <Link
                    to="/citations/$sourceId"
                    params={{ sourceId: it.id }}
                    className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                  >
                    Open <ExternalLink className="h-3 w-3" />
                  </Link>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
