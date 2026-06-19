import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { MetricCard } from "@/components/hms/MetricCard";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/metrics/feedback")({
  head: () => ({ meta: [{ title: "User feedback — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="User feedback" description="Thumbs and free-text feedback on answers." />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          label="Helpful"
          value="4,213"
          delta={{ value: "+184", positive: true }}
          tone="primary"
        />
        <MetricCard
          label="Unhelpful"
          value="187"
          delta={{ value: "-21", positive: true }}
          tone="warning"
        />
        <MetricCard
          label="NPS (30d)"
          value="64"
          delta={{ value: "+3", positive: true }}
          tone="secondary"
        />
      </div>
      <Card className="mt-6 p-5">
        <p className="text-sm font-semibold mb-2">Recent comments</p>
        <ul className="space-y-2 text-sm">
          {[
            '"Citation pinpointed §5.2 — great." — Dr. Chen',
            '"Refused on a question I expected to answer." — Dr. Patel',
            '"Loved the compare-citations view." — Pharm. Ruiz',
          ].map((c) => (
            <li key={c} className="rounded-md border p-3">
              {c}
            </li>
          ))}
        </ul>
      </Card>
    </AppShell>
  );
}
