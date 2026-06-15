import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { MetricCard } from "@/components/hms/MetricCard";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/integrations/vector-index")({
  head: () => ({ meta: [{ title: "Vector index — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="Vector index" description="Embedding storage and retrieval performance." />
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Documents indexed" value="48,221" delta={{value:'+1,204', positive:true}} tone="primary" />
        <MetricCard label="Chunks" value="1.42M" delta={{value:'+38k', positive:true}} tone="secondary" />
        <MetricCard label="Query P95" value="84ms" delta={{value:'-9ms', positive:true}} tone="ai" />
        <MetricCard label="Recall @10" value="0.93" delta={{value:'+0.01', positive:true}} tone="citation" />
      </div>
      <Card className="mt-6 p-5 text-sm text-muted-foreground">Index sharding map (mock).</Card>
    </AppShell>
  );
}
