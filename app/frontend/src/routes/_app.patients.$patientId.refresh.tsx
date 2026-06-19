import { createFileRoute } from "@tanstack/react-router";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/patients/$patientId/refresh")({
  head: () => ({ meta: [{ title: "Refresh from HMS — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <div className="space-y-4">
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold">HMS pull in progress</p>
            <p className="text-xs text-muted-foreground">
              Reconciling last 7 days of orders, labs, vitals, and notes.
            </p>
          </div>
          <span className="rounded-full bg-secondary/10 px-3 py-1 text-xs font-medium text-secondary">
            Streaming
          </span>
        </div>
        <div className="mt-4 space-y-2">
          {["Orders", "Labs", "Vitals", "Notes", "Imaging"].map((s, i) => (
            <div key={s} className="flex items-center justify-between text-sm">
              <span>{s}</span>
              <span className={i < 3 ? "text-success" : "text-muted-foreground"}>
                {i < 3 ? "✓ synced" : "… pending"}
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
