import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/admin/data-retention")({
  head: () => ({ meta: [{ title: "Data retention — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader
        title="Data retention"
        description="Per-dataset retention windows and purge schedules."
      />
      <Card className="p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/40 text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-4 py-2 text-left">Dataset</th>
              <th className="px-4 py-2 text-left">Retention</th>
              <th className="px-4 py-2 text-left">Next purge</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["Chat transcripts", "7 years", "—"],
              ["Audit logs", "10 years", "—"],
              ["Document index", "Indefinite", "—"],
              ["Telemetry traces", "30 days", "Tomorrow 02:00 UTC"],
              ["Feedback comments", "2 years", "—"],
            ].map((r, i) => (
              <tr key={i} className="border-t">
                <td className="px-4 py-2 font-medium">{r[0]}</td>
                <td className="px-4 py-2">{r[1]}</td>
                <td className="px-4 py-2 text-xs text-muted-foreground">{r[2]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </AppShell>
  );
}
