import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { syncJobs } from "@/data/syncJobs";
import { formatDateTime } from "@/lib/format";

export const Route = createFileRoute("/_app/integrations/hms/jobs/$jobId")({
  head: () => ({ meta: [{ title: "HMS job — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { jobId } = Route.useParams();
  const j = syncJobs.find(x=>x.id===jobId) || syncJobs[0];
  return (
    <AppShell>
      <PageHeader title={`Job ${j.id}`} description={`${j.source} · ${j.status}`} />
      <Card className="p-5 text-sm space-y-2 max-w-md">
        <Row k="Source" v={j.source} />
        <Row k="Scope" v={j.scope} />
        <Row k="When" v={formatDateTime(j.ts)} />
        <Row k="Records" v={String(j.records)} />
        <Row k="Failed" v={String(j.failed)} />
        <Row k="Duration" v={`${j.durationMs} ms`} />
      </Card>
    </AppShell>
  );
}
function Row({k,v}:{k:string;v:string}){return <div className="flex justify-between border-b py-1 last:border-0"><span className="text-muted-foreground">{k}</span><span className="font-medium">{v}</span></div>}
