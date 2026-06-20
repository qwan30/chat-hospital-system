import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { getConflict } from "@/lib/api/medication-safety";
import { ConflictSeverityPill } from "@/components/hms/ConflictSeverityPill";
import { Badge } from "@/components/ui/badge";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/_app/medication-conflicts/$conflictId")({
  head: () => ({ meta: [{ title: "Medication conflict — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { conflictId } = Route.useParams();

  const {
    data: c,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["pharmacy", "conflict", conflictId],
    queryFn: () => getConflict(conflictId),
  });

  if (isLoading) {
    return (
      <AppShell>
        <div className="flex h-40 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </AppShell>
    );
  }

  if (error || !c) {
    return (
      <AppShell>
        <div className="p-6 text-center text-muted-foreground">Conflict not found</div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        title={`Conflict ${c.id}`}
        description={`${c.patient} · ${c.drug}`}
        chips={
          <>
            <ConflictSeverityPill severity={c.severity as any} />
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
