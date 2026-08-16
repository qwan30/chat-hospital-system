import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useQuery } from "@tanstack/react-query";
import { getAccessRequest } from "@/lib/api/access-requests";
import { formatDateTime } from "@/lib/format";
import { ErrorState } from "@/components/hms/ErrorState";

import { sanitizeError } from "@/lib/errors";

export const Route = createFileRoute("/_app/access-requests/$requestId")({
  head: () => ({ meta: [{ title: "Access request — HMS AI Copilot" }] }),
  component: Page,
  errorComponent: ({ error, reset }) => (
    <AppShell fixedHeight>
      <div className="flex h-full items-center justify-center p-8">
        <ErrorState
          title="Failed to load access request"
          description={sanitizeError(error)}
          code="API_ERROR"
          extra={
            <Button onClick={reset} variant="outline">
              Retry
            </Button>
          }
        />
      </div>
    </AppShell>
  ),
});

const tone: Record<string, string> = {
  pending: "bg-warning/10 text-warning border-transparent",
  approved: "bg-success/10 text-success border-transparent",
  denied: "bg-destructive/10 text-destructive border-transparent",
  pending_info: "bg-info/10 text-info border-transparent",
};

function Page() {
  const { requestId } = Route.useParams();
  const {
    data: r,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["access-request", requestId],
    queryFn: () => getAccessRequest(requestId),
    retry: false,
  });

  if (isLoading) {
    return (
      <AppShell>
        <PageHeader title="Loading..." />
      </AppShell>
    );
  }

  if (error || !r) {
    const errMsg = error ? sanitizeError(error) : "The requested access record could not be found.";
    return (
      <AppShell>
        <PageHeader title="Request not found" />
        <ErrorState code="API_ERROR" title="Failed to load access request" description={errMsg} />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        title={`Request ${r.id.split("-")[0]}`}
        description={`${r.patient_name} · ${r.patient_mrn}`}
        chips={
          <Badge
            className={`capitalize ${tone[r.status] || "bg-secondary text-secondary-foreground"}`}
          >
            {r.status.replace("_", " ")}
          </Badge>
        }
        actions={
          r.status === "pending" || r.status === "pending_info" ? (
            <Button asChild>
              <Link to="/access-requests/$requestId/review" params={{ requestId: r.id }}>
                Review
              </Link>
            </Button>
          ) : null
        }
      />
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-5 space-y-3 text-sm">
          <Row k="Requester" v={`${r.requester_name} · ${r.requester_role}`} />
          <Row k="Submitted" v={formatDateTime(r.created_at)} />
          {r.reviewed_by_name ? <Row k="Reviewer" v={r.reviewed_by_name} /> : null}
          {r.reviewed_at ? <Row k="Decision" v={formatDateTime(r.reviewed_at)} /> : null}
        </Card>
        <Card className="p-5 text-sm">
          <h4 className="mb-2 text-sm font-semibold">Justification</h4>
          <p className="text-muted-foreground">{r.justification}</p>
        </Card>
        {r.review_notes && (
          <Card className="p-5 text-sm md:col-span-2">
            <h4 className="mb-2 text-sm font-semibold">Review Notes</h4>
            <p className="text-muted-foreground">{r.review_notes}</p>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-muted-foreground">{k}</span>
      <span className="font-medium">{v}</span>
    </div>
  );
}
