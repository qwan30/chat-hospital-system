import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { drugConflicts } from "@/data/conflicts";
import { ConflictSeverityPill } from "@/components/hms/ConflictSeverityPill";

export const Route = createFileRoute("/_app/pharmacy/review-queue")({
  head: () => ({ meta: [{ title: "Pharmacy review queue — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="Pharmacy review queue" description="AI-flagged drug interactions awaiting pharmacist sign-off." />
      <div className="space-y-2">{drugConflicts.map(c=>(<Link key={c.id} to="/medication-conflicts/$conflictId" params={{conflictId:c.id}} className="block"><Card className="p-4 flex items-center justify-between hover:bg-muted/40"><div><p className="text-sm font-medium">{c.drug}</p><p className="text-xs text-muted-foreground">{c.patient} · {c.conflictsWith}</p></div><ConflictSeverityPill severity={c.severity} /></Card></Link>))}</div>
    </AppShell>
  );
}
