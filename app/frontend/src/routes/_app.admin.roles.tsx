import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const Route = createFileRoute("/_app/admin/roles")({
  head: () => ({ meta: [{ title: "Roles — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="Roles" description="System-wide RBAC role definitions." />
      <Card className="p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/40 text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-4 py-2 text-left">Role</th>
              <th className="px-4 py-2 text-left">Members</th>
              <th className="px-4 py-2 text-left">Scope</th>
              <th className="px-4 py-2 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["Cardiologist", "24", "Cardiology unit", "Active"],
              ["Hospitalist", "61", "Assigned patients", "Active"],
              ["RN", "118", "Bedside", "Active"],
              ["Pharmacist", "12", "Meds + labs", "Active"],
              ["Front desk", "9", "Demographics", "Active"],
              ["Admin", "4", "Workspace-wide", "Active"],
            ].map((r, i) => (
              <tr key={i} className="border-t">
                <td className="px-4 py-2 font-medium">{r[0]}</td>
                <td className="px-4 py-2">{r[1]}</td>
                <td className="px-4 py-2 text-xs text-muted-foreground">{r[2]}</td>
                <td className="px-4 py-2">
                  <Badge variant="secondary" className="bg-success/10 text-success">
                    {r[3]}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </AppShell>
  );
}
