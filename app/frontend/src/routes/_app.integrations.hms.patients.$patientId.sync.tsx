import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/integrations/hms/patients/$patientId/sync")({
  head: () => ({ meta: [{ title: "HMS patient sync — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { patientId } = Route.useParams();
  return (
    <AppShell>
      <PageHeader
        title={`Sync ${patientId}`}
        description="Per-patient HMS reconciliation status."
      />
      <Card className="p-5 text-sm">
        <ul className="space-y-2">
          {["Demographics", "Allergies", "Orders", "Labs", "Vitals", "Notes"].map((s, i) => (
            <li key={s} className="flex justify-between">
              <span>{s}</span>
              <span className={i < 4 ? "text-success" : "text-muted-foreground"}>
                {i < 4 ? "✓ in sync" : "… 3 deltas"}
              </span>
            </li>
          ))}
        </ul>
      </Card>
    </AppShell>
  );
}
