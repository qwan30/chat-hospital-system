import type { Trace } from "@/data/traces";
import { Card } from "@/components/ui/card";

const serviceColor: Record<string, string> = {
  BFF: "bg-primary",
  Auth: "bg-info",
  AccessControl: "bg-secondary",
  Audit: "bg-muted-foreground",
  RAG: "bg-citation",
  Ollama: "bg-ai",
};

export function TraceTimeline({ trace }: { trace: Trace }) {
  return (
    <Card className="p-5">
      <div className="mb-3 flex items-baseline justify-between">
        <div>
          <div className="text-sm font-semibold">Trace · {trace.id}</div>
          <div className="text-xs text-muted-foreground">{trace.query}</div>
        </div>
        <div className="font-mono text-sm">{trace.totalMs} ms</div>
      </div>
      <ul className="space-y-2">
        {trace.spans.map((s) => {
          const leftPct = (s.startOffsetMs / trace.totalMs) * 100;
          const widthPct = Math.max((s.durationMs / trace.totalMs) * 100, 1.5);
          return (
            <li key={s.id} className="grid grid-cols-[160px_1fr_64px] items-center gap-3 text-xs">
              <div className="truncate">
                <div className="font-medium text-foreground">{s.name}</div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                  {s.service}
                </div>
              </div>
              <div className="relative h-5 rounded-full bg-muted">
                <div
                  className={`absolute top-0 h-full rounded-full ${serviceColor[s.service] ?? "bg-muted-foreground"} ${s.status === "warn" ? "opacity-70" : ""}`}
                  style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
                />
              </div>
              <div className="text-right font-mono">{s.durationMs}ms</div>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
