import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { syncJobs } from "@/data/syncJobs";
import { formatDateTime } from "@/lib/format";

const tone: Record<string,string> = { success:'text-success', running:'text-info', failed:'text-destructive', retrying:'text-warning' };

export const Route = createFileRoute("/_app/documents/sync-hms")({
  head: () => ({ meta: [{ title: "HMS sync — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="HMS document sync" description="Inbound document streams from the hospital management system." />
      <Card className="p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/40 text-xs uppercase text-muted-foreground"><tr><th className="px-4 py-2 text-left">Job</th><th className="px-4 py-2 text-left">Scope</th><th className="px-4 py-2 text-left">Records</th><th className="px-4 py-2 text-left">Status</th><th className="px-4 py-2 text-left">When</th><th/></tr></thead>
          <tbody>{syncJobs.map(j=>(<tr key={j.id} className="border-t"><td className="px-4 py-2 font-medium">{j.source}</td><td className="px-4 py-2 text-xs text-muted-foreground">{j.scope}</td><td className="px-4 py-2">{j.records} <span className="text-xs text-muted-foreground">({j.failed} failed)</span></td><td className={"px-4 py-2 capitalize font-medium "+tone[j.status]}>{j.status}</td><td className="px-4 py-2 text-xs">{formatDateTime(j.ts)}</td><td className="px-4 py-2 text-right text-xs"><Link to="/integrations/hms/jobs/$jobId" params={{jobId:j.id}} className="text-primary underline">Open</Link></td></tr>))}</tbody>
        </table>
      </Card>
    </AppShell>
  );
}
