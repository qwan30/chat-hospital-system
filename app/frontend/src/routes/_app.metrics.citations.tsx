import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { MetricCard } from "@/components/hms/MetricCard";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/metrics/citations")({
  head: () => ({ meta: [{ title: "Citation coverage — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader
        title="Citation coverage"
        description="How often answers cite ≥1 retrievable source."
      />

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard
          label="With citations"
          value="96.2%"
          delta={{ value: "+1.1pp", positive: true }}
          tone="citation"
        />
        <MetricCard
          label="Avg per answer"
          value="2.7"
          delta={{ value: "+0.2", positive: true }}
          tone="citation"
        />
        <MetricCard
          label="Broken citations"
          value="0.4%"
          delta={{ value: "-0.1pp", positive: true }}
          tone="warning"
        />
        <MetricCard
          label="Out-of-scope"
          value="0.8%"
          delta={{ value: "-0.2pp", positive: true }}
          tone="warning"
        />
      </div>
    </AppShell>
  );
}
