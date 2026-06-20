import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { getReviewQueue } from "@/lib/api/medication-safety";
import { ConflictSeverityPill } from "@/components/hms/ConflictSeverityPill";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/_app/pharmacy/review-queue")({
  head: () => ({ meta: [{ title: "Pharmacy review queue — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const {
    data: conflicts,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["pharmacy", "review-queue"],
    queryFn: getReviewQueue,
  });

  return (
    <AppShell>
      <PageHeader
        title="Pharmacy review queue"
        description="AI-flagged drug interactions awaiting pharmacist sign-off."
      />
      <div className="space-y-2">
        {isLoading && (
          <div className="flex justify-center p-4">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}
        {error && (
          <div className="text-destructive p-4 text-sm bg-destructive/10 rounded-md">
            Failed to load review queue.
          </div>
        )}
        {conflicts?.length === 0 && (
          <div className="p-4 text-sm text-muted-foreground text-center">
            No conflicts awaiting review.
          </div>
        )}
        {conflicts?.map((c) => (
          <Link
            key={c.id}
            to="/medication-conflicts/$conflictId"
            params={{ conflictId: c.id }}
            className="block"
          >
            <Card className="p-4 flex items-center justify-between hover:bg-muted/40">
              <div>
                <p className="text-sm font-medium">{c.drug}</p>
                <p className="text-xs text-muted-foreground">
                  {c.patient} · {c.conflictsWith}
                </p>
              </div>
              <ConflictSeverityPill severity={c.severity as any} />
            </Card>
          </Link>
        ))}
      </div>
    </AppShell>
  );
}
