import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { getAccessRequest } from "@/data/accessRequests";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/access-requests/$requestId/review")({
  head: () => ({ meta: [{ title: "Review request — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { requestId } = Route.useParams();
  const r = getAccessRequest(requestId);
  if (!r) return <AppShell><PageHeader title="Request not found" /></AppShell>;
  return (
    <AppShell>
      <PageHeader title="Review access request" description={`${r.patient} · ${r.mrn}`} />
      <Card className="p-6 space-y-4">
        <div className="rounded-md border bg-muted/40 p-4 text-sm"><p className="font-medium">{r.requester} · {r.role}</p><p className="mt-1 text-muted-foreground">{r.justification}</p></div>
        <div className="space-y-2"><label className="text-sm font-medium">Reviewer note (audited)</label><Textarea placeholder="Document scope, duration, and conditions for this access grant…" rows={4} /></div>
        <div className="flex gap-2 justify-end">
          <Button variant="outline" onClick={()=>toast.error("Request denied (mock)")}>Deny</Button>
          <Button onClick={()=>toast.success("Approved with 24h scope (mock)")}>Approve · 24h</Button>
          <Button variant="default" onClick={()=>toast.success("Approved with 7d scope (mock)")}>Approve · 7d</Button>
        </div>
      </Card>
    </AppShell>
  );
}
