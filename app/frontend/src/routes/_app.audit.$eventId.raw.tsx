import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/audit/$eventId/raw")({
  head: () => ({ meta: [{ title: "Audit event — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { eventId } = Route.useParams();
  const sample = { id: eventId, ts: "2026-06-12T16:42:11Z", actor: "Dr. S. Chen", action: "chat.completion", patient: "p-001", citations: ["c-001","c-002"], result: "ok", traceId: "t-9f3a", policy: { allow: true, rules: ["role:cardiologist","unit:4N"] } };
  return (
    <AppShell>
      <PageHeader title={`Audit event ${eventId}`} description="Raw JSON record (signed, append-only)." />
      <Card className="p-5"><pre className="overflow-auto text-xs">{JSON.stringify(sample, null, 2)}</pre></Card>
    </AppShell>
  );
}
