import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { MetricCard } from "@/components/hms/MetricCard";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/integrations/llm")({
  head: () => ({ meta: [{ title: "LLM provider — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="LLM provider" description="Model routing, latency, and fallback status." />
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Primary uptime" value="99.97%" delta={{value:'+0.02pp', positive:true}} tone="primary" />
        <MetricCard label="Avg latency" value="820ms" delta={{value:'-40ms', positive:true}} tone="ai" />
        <MetricCard label="Fallback events" value="14" delta={{value:'-3', positive:true}} tone="warning" />
        <MetricCard label="Token spend (24h)" value="$182" delta={{value:'+$8', positive:false}} tone="citation" />
      </div>
      <Card className="mt-6 p-5 text-sm">Routing rules: Cardiology questions → med-large; General chat → med-small; Fallback after 2 timeouts.</Card>
    </AppShell>
  );
}
