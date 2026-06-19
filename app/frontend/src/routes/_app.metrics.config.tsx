import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { MetricCard } from "@/components/hms/MetricCard";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/metrics/config")({
  head: () => ({ meta: [{ title: "Metrics configuration — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader
        title="Metrics configuration"
        description="Dashboard thresholds, alerting, and retention."
      />

      <Card className="p-5 text-sm text-muted-foreground">
        Threshold sliders, alert rules, and retention controls (mock UI).
      </Card>
    </AppShell>
  );
}
