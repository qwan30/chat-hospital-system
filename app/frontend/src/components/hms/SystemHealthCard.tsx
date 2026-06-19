import { Card } from "@/components/ui/card";
import { systemHealth } from "@/data/health";
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

export function SystemHealthCard() {
  return (
    <Card className="p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold">System health</div>
          <div className="text-xs text-muted-foreground">Live readout · refreshed every 30s</div>
        </div>
      </div>
      <ul className="space-y-3">
        {systemHealth.map((m) => {
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
