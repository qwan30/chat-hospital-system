import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { MetricCard } from "@/components/hms/MetricCard";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/metrics/safe-refusal")({
  head: () => ({ meta: [{ title: "Safe-refusal metrics — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="Safe-refusal metrics" description="When and why the system declined to answer." />
      
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Safe refusals" value="3.4%" delta={{value:'-0.3pp', positive:true}} tone="ai" />
        <MetricCard label="Low confidence" value="2.1%" delta={{value:'-0.2pp', positive:true}} tone="ai" />
        <MetricCard label="No evidence" value="0.9%" delta={{value:'-0.1pp', positive:true}} tone="warning" />
        <MetricCard label="Policy blocked" value="0.4%" delta={{value:'0', positive:true}} tone="secondary" />
      </div>

    </AppShell>
  );
}
