import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { drugConflicts } from "@/data/conflicts";
import { ConflictSeverityPill } from "@/components/hms/ConflictSeverityPill";
import { Badge } from "@/components/ui/badge";

export const Route = createFileRoute("/_app/medication-conflicts/$conflictId")({
  head: () => ({ meta: [{ title: "Medication conflict — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { conflictId } = Route.useParams();
  const c = drugConflicts.find((x) => x.id === conflictId) || drugConflicts[0];
  return (
    <AppShell>
      <PageHeader
        title={`Conflict ${c.id}`}
        description={`${c.patient} · ${c.drug}`}
        chips={
          <>
            <ConflictSeverityPill severity={c.severity} />
            <Badge variant="outline" className="capitalize">
              {c.type}
            </Badge>
          </>
        }
      />
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-5 text-sm space-y-2">
          <h4 className="text-sm font-semibold">Conflicts with</h4>
          <p className="text-foreground">{c.conflictsWith}</p>
          <p className="text-xs text-muted-foreground mt-3">Rule: {c.rule}</p>
          <p className="text-xs text-muted-foreground">Source: {c.source}</p>
        </Card>
        <Card className="p-5 text-sm">
          <h4 className="text-sm font-semibold mb-2">Recommendation</h4>
          <p>{c.recommendation}</p>
        </Card>
      </div>
    </AppShell>
  );
}
