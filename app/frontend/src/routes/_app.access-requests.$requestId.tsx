import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getAccessRequest } from "@/data/accessRequests";
import { formatDateTime } from "@/lib/format";

export const Route = createFileRoute("/_app/access-requests/$requestId")({
  head: () => ({ meta: [{ title: "Access request — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { requestId } = Route.useParams();
  const r = getAccessRequest(requestId);
  if (!r)
    return (
      <AppShell>
        <PageHeader title="Request not found" />
      </AppShell>
    );
  return (
    <AppShell>
      <PageHeader
        title={`Request ${r.id}`}
        description={`${r.patient} · ${r.mrn}`}
        chips={
          <Badge variant="secondary" className="capitalize">
            {r.status}
          </Badge>
        }
        actions={
          <Button asChild>
            <Link to="/access-requests/$requestId/review" params={{ requestId: r.id }}>
              Review
            </Link>
          </Button>
        }
      />
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-5 space-y-3 text-sm">
          <Row k="Requester" v={`${r.requester} · ${r.role}`} />
          <Row k="Unit" v={r.unit} />
          <Row k="Submitted" v={formatDateTime(r.ts)} />
          {r.reviewer ? <Row k="Reviewer" v={r.reviewer} /> : null}
          {r.decisionTs ? <Row k="Decision" v={formatDateTime(r.decisionTs)} /> : null}
        </Card>
        <Card className="p-5 text-sm">
          <h4 className="mb-2 text-sm font-semibold">Justification</h4>
          <p className="text-muted-foreground">{r.justification}</p>
        </Card>
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
