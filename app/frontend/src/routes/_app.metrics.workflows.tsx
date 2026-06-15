import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { MetricCard } from "@/components/hms/MetricCard";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/metrics/workflows")({
  head: () => ({ meta: [{ title: "Workflow metrics — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="Workflow metrics" description="Latency, success, and abandonment across major workflows." />
      
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Avg answer latency" value="1.8s" delta={{value:'-0.3s', positive:true}} tone="primary" />
        <MetricCard label="P95 latency" value="4.6s" delta={{value:'-0.4s', positive:true}} tone="primary" />
        <MetricCard label="Success rate" value="98.4%" delta={{value:'+0.2pp', positive:true}} tone="secondary" />
        <MetricCard label="Abandonment" value="2.1%" delta={{value:'-0.4pp', positive:true}} tone="warning" />
      </div>
      <Card className="mt-6 p-5"><p className="text-sm text-muted-foreground">Workflow breakdown chart (mock).</p></Card>

    </AppShell>
  );
}
