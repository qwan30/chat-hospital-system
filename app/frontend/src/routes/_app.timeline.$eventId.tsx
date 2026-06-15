import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/timeline/$eventId")({
  head: () => ({ meta: [{ title: "Timeline event — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { eventId } = Route.useParams();
  return (
    <AppShell>
      <PageHeader title={`Event ${eventId}`} description="Patient timeline event detail with linked evidence." />
      <Card className="p-5 text-sm space-y-2"><p><span className="text-muted-foreground">Type:</span> Lab result</p><p><span className="text-muted-foreground">Patient:</span> Eleanor Vance</p><p><span className="text-muted-foreground">When:</span> Today 06:20</p><p><span className="text-muted-foreground">Summary:</span> BNP 420 pg/mL (elevated). Trending up vs. prior 280.</p></Card>
    </AppShell>
  );
}
