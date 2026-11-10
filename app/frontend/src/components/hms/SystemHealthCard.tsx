import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { systemHealth, type HealthMetric } from "@/data/health";
import { getDashboardSummary, type SystemsHealth } from "@/lib/api/dashboard";
import { CheckCircle2, AlertTriangle, XCircle } from "lucide-react";

const iconFor = {
  ok: CheckCircle2,
  degraded: AlertTriangle,
  down: XCircle,
};
const toneFor = {
  ok: "text-success",
  degraded: "text-warning",
  down: "text-destructive",
};

function toHealthStatus(raw: string | undefined): "ok" | "degraded" | "down" {
  const normalized = (raw ?? "").toLowerCase();
  if (normalized === "online" || normalized === "ok" || normalized === "healthy") {
    return "ok";
  }
  if (normalized === "down" || normalized === "offline" || normalized === "error") {
    return "down";
  }
  return "degraded";
}

export function SystemHealthCard({ health }: { health?: SystemsHealth } = {}) {
  const { data } = useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: getDashboardSummary,
    enabled: !health,
    staleTime: 30_000,
  });

  const liveHealth = health ?? data?.systems_health;
  const docStats = data?.document_stats;

  const metrics: HealthMetric[] = liveHealth
    ? [
        {
          name: "HMS FHIR bridge",
          status: toHealthStatus(liveHealth.hms_api),
          detail: "Core clinical BFF & patient scope sync",
          value: liveHealth.hms_api,
        },
        {
          name: "LLM runtime (Ollama)",
          status: toHealthStatus(liveHealth.ollama_inference),
          detail: "Local clinical inference & guardrails",
          value: liveHealth.ollama_inference,
        },
        {
          name: "Vector index (pgvector)",
          status: docStats && docStats.failed > 0 ? "degraded" : "ok",
          detail: docStats
            ? `${docStats.indexed} indexed · ${docStats.processing} processing · ${docStats.failed} failed`
            : "Active generation index",
          value: docStats ? `${docStats.indexed} docs` : "ready",
        },
      ]
    : systemHealth;

  return (
    <Card className="p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold">System health</div>
          <div className="text-xs text-muted-foreground">Live readout · refreshed every 30s</div>
        </div>
      </div>
      <ul className="space-y-3">
        {metrics.map((m) => {
          const Icon = iconFor[m.status];
          return (
            <li
              key={m.name}
              className="flex items-center justify-between border-b pb-3 last:border-0 last:pb-0"
            >
              <div className="flex items-center gap-3">
                <Icon className={`h-4 w-4 ${toneFor[m.status]}`} />
                <div>
                  <div className="text-sm font-medium">{m.name}</div>
                  <div className="text-xs text-muted-foreground">{m.detail}</div>
                </div>
              </div>
              <div className="font-mono text-xs">{m.value}</div>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
