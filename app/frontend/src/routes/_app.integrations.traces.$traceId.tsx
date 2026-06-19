import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { TraceTimeline } from "@/components/hms/TraceTimeline";
import { traces } from "@/data/traces";

export const Route = createFileRoute("/_app/integrations/traces/$traceId")({
  head: () => ({ meta: [{ title: "Trace — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { traceId } = Route.useParams();
  const t = traces.find((x) => x.id === traceId) || traces[0];
  return (
    <AppShell>
      <PageHeader
        title={`OpenTelemetry trace ${t.id}`}
        description={`${t.query} · ${t.spans.length} spans · ${t.totalMs}ms`}
      />
      <TraceTimeline trace={t} />
    </AppShell>
  );
}
