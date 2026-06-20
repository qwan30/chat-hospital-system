import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import { listAccessRequests } from "@/lib/api/access-requests";
import { formatDateTime } from "@/lib/format";
import { EmptyState } from "@/components/hms/EmptyState";
import { ErrorState } from "@/components/hms/ErrorState";

export const Route = createFileRoute("/_app/access-requests/")({
  head: () => ({ meta: [{ title: "Access requests — HMS AI Copilot" }] }),
  component: Page,
});

const tone: Record<string, string> = {
  pending: "bg-warning/10 text-warning",
  approved: "bg-success/10 text-success",
  denied: "bg-destructive/10 text-destructive",
  pending_info: "bg-info/10 text-info",
};

function Page() {
  const {
    data: accessRequests,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["access-requests"],
    queryFn: listAccessRequests,
  });

  if (isLoading) {
    return (
      <AppShell>
        <PageHeader title="Access requests" description="Loading..." />
      </AppShell>
    );
  }

  if (error || !accessRequests) {
    return (
      <AppShell>
        <PageHeader title="Access requests" />
        <ErrorState
          code="API_ERROR"
          title="Failed to load access requests"
          description={(error as Error)?.message}
        />
      </AppShell>
    );
  }

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
      {accessRequests.length === 0 ? (
        <EmptyState
          title="No access requests found"
          description="There are no pending or resolved access requests."
        />
      ) : (
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
                    <div className="font-medium">{r.patient_name}</div>
                    <div className="font-mono text-xs text-muted-foreground">{r.patient_mrn}</div>
                  </td>
                  <td className="px-4 py-2">
                    <div>{r.requester_name}</div>
                    <div className="text-xs text-muted-foreground">{r.requester_role}</div>
                  </td>
                  <td className="px-4 py-2 max-w-md text-xs text-muted-foreground">
                    {r.justification}
                  </td>
                  <td className="px-4 py-2 text-xs">{formatDateTime(r.created_at)}</td>
                  <td className="px-4 py-2">
                    <span
                      className={
                        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize " +
                        (tone[r.status] || "bg-muted text-muted-foreground")
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
      )}
    </AppShell>
  );
}
