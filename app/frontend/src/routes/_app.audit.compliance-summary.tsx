import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { MetricCard } from "@/components/hms/MetricCard";

export const Route = createFileRoute("/_app/audit/compliance-summary")({
  head: () => ({ meta: [{ title: "Compliance summary — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="Compliance summary" description="HIPAA / SOC 2 monthly snapshot for this workspace." />
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="PHI access events" value="48,221" delta={{value:'+3.2%', positive:true}} tone="primary" />
        <MetricCard label="Denied (policy)" value="142" delta={{value:'-12%', positive:true}} tone="secondary" />
        <MetricCard label="Break-glass" value="3" delta={{value:'0', positive:true}} tone="warning" />
        <MetricCard label="Export requests" value="11" delta={{value:'+2', positive:true}} tone="ai" />
      </div>
    </AppShell>
  );
}
