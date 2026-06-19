import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { accessRequests } from "@/data/accessRequests";
import { formatDateTime } from "@/lib/format";

export const Route = createFileRoute("/_app/access-requests/")({
  head: () => ({ meta: [{ title: "Access requests — HMS AI Copilot" }] }),
  component: Page,
});

const tone: Record<string, string> = {
  pending: "bg-warning/10 text-warning",
  approved: "bg-success/10 text-success",
  denied: "bg-destructive/10 text-destructive",
};

function Page() {
  return (
    <AppShell>
      <PageHeader
        title="Access requests"
        description="Inbox of PHI access requests awaiting review."
        chips={
          <Badge variant="secondary">
            {accessRequests.filter((r) => r.status === "pending").length} pending
          </Badge>
        }
      />
      <Card className="p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/40 text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-4 py-2 text-left">Patient</th>
              <th className="px-4 py-2 text-left">Requester</th>
              <th className="px-4 py-2 text-left">Justification</th>
              <th className="px-4 py-2 text-left">When</th>
              <th className="px-4 py-2 text-left">Status</th>
              <th className="px-4 py-2" />
            </tr>
          </thead>
          <tbody>
            {accessRequests.map((r) => (
              <tr key={r.id} className="border-t">
                <td className="px-4 py-2">
                  <div className="font-medium">{r.patient}</div>
                  <div className="font-mono text-xs text-muted-foreground">{r.mrn}</div>
                </td>
                <td className="px-4 py-2">
                  <div>{r.requester}</div>
                  <div className="text-xs text-muted-foreground">{r.role}</div>
                </td>
                <td className="px-4 py-2 max-w-md text-xs text-muted-foreground">
                  {r.justification}
                </td>
                <td className="px-4 py-2 text-xs">{formatDateTime(r.ts)}</td>
                <td className="px-4 py-2">
                  <span
                    className={
                      "inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize " +
                      tone[r.status]
                    }
                  >
                    {r.status}
                  </span>
                </td>
                <td className="px-4 py-2 text-right">
                  <Button size="sm" variant="ghost" asChild>
                    <Link to="/access-requests/$requestId" params={{ requestId: r.id }}>
                      Open
                    </Link>
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </AppShell>
  );
}
