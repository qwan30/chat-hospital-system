import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/settings/workspaces")({
  head: () => ({ meta: [{ title: "Workspaces — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader
        title="Workspaces"
        description="Switch between roles and workspaces you belong to."
      />
      <div className="space-y-2">
        {[
          ["Cardiology — 4N", "Cardiologist", "Active"],
          ["ICU — 2W", "Consulting", "Switch"],
          ["Pharmacy review", "Reviewer", "Switch"],
        ].map(([n, r, a]) => (
          <Card key={n} className="p-4 flex items-center justify-between">
            <div>
              <p className="font-medium text-sm">{n}</p>
              <p className="text-xs text-muted-foreground">{r}</p>
            </div>
            <span
              className={
                "text-xs font-medium " + (a === "Active" ? "text-success" : "text-primary")
              }
            >
              {a}
            </span>
          </Card>
        ))}
      </div>
    </AppShell>
  );
}
