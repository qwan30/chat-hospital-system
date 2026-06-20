import { createFileRoute, useSearch } from "@tanstack/react-router";
import { ArrowRight, Network, Download, Share2, Sparkles } from "lucide-react";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { GraphCanvas } from "@/components/hms/GraphCanvas";
import { getPatientGraph } from "@/lib/api/graph";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StreamingControls } from "@/components/hms/StreamingControls";
import { useStreamSteps } from "@/hooks/use-stream-steps";
import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";

export const Route = createFileRoute("/_app/graph/patients/$patientId")({
  head: () => ({ meta: [{ title: "Patient graph — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { patientId } = Route.useParams();

  const {
    data: patientGraph,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["graph", patientId],
    queryFn: () => getPatientGraph(patientId),
  });

  const search = useSearch({ strict: false }) as { simulate?: string };
  const force = search?.simulate === "stream-fail";

  const path = patientGraph?.reasoning_path?.[0] || { steps: [], rationale: "" };
  const streamLength = path.steps.length || 0;

  const stream = useStreamSteps(streamLength, {
    forceInterrupt: force,
    failureRate: force ? 1 : 0.08,
  });

  useEffect(() => {
    if (streamLength > 0 && stream.status === "idle") {
      stream.start();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streamLength]);

  if (isLoading)
    return (
      <AppShell>
        <div className="p-8 text-muted-foreground">Loading graph...</div>
      </AppShell>
    );
  if (error)
    return (
      <AppShell>
        <div className="p-8 text-destructive">Error loading graph.</div>
      </AppShell>
    );
  if (!patientGraph) return null;

  return (
    <AppShell>
      <PageHeader
        title="Patient knowledge graph"
        description="Diagnoses, medications, labs, and providers linked by clinical events. Click any node to trace its relationships."
        backLink={{ to: `/patients/${patientId}`, label: "Back to Patient" }}
        chips={
          <>
            <Badge variant="secondary" className="gap-1.5">
              <Network className="h-3 w-3" /> {patientGraph.nodes.length} entities
            </Badge>
            <Badge variant="outline" className="gap-1.5">
              <Sparkles className="h-3 w-3 text-ai" /> RAG-grounded
            </Badge>
            <Badge variant="outline">
              Updated {new Date(patientGraph.metadata?.updated_at || "").toLocaleDateString()}
            </Badge>
          </>
        }
        actions={
          <>
            <Button variant="outline" size="sm" className="gap-1.5">
              <Share2 className="h-4 w-4" /> Share
            </Button>
            <Button variant="outline" size="sm" className="gap-1.5">
              <Download className="h-4 w-4" /> Export
            </Button>
          </>
        }
      />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_360px]">
        {/* @ts-ignore */}
        <GraphCanvas data={patientGraph} />

        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold">Reasoning path</CardTitle>
                <Badge variant="outline" className="gap-1 text-[10px]">
                  <Sparkles className="h-3 w-3 text-ai" />
                  {stream.status === "streaming"
                    ? `Streaming ${stream.revealed}/${streamLength}`
                    : stream.status === "interrupted"
                      ? "Interrupted"
                      : "AI traversal"}
                </Badge>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{path.rationale}</p>
            </CardHeader>
            <CardContent className="space-y-3">
              {path.steps.slice(0, stream.revealed).map((s: any, i: number) => (
                <div key={i} className="rounded-lg border bg-muted/30 p-3">
                  <div className="flex items-center gap-2 text-[11px] font-medium text-muted-foreground">
                    <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-primary text-[10px] font-semibold">
                      {i + 1}
                    </span>
                    <span className="truncate">{s.from_node}</span>
                    <ArrowRight className="h-3 w-3 shrink-0" />
                    <span className="truncate text-foreground">{s.to_node}</span>
                  </div>
                  <p className="mt-2 text-xs text-foreground">{s.relation}</p>
                  <p className="mt-1 text-[11px] text-muted-foreground">Evidence: {s.evidence}</p>
                </div>
              ))}
              {stream.status === "streaming" && stream.revealed < streamLength ? (
                <div className="rounded-lg border border-dashed bg-muted/20 p-3 text-[11px] text-muted-foreground">
                  Tracing next hop…
                </div>
              ) : null}
              <StreamingControls
                status={stream.status}
                error={stream.error}
                progress={stream.progress}
                total={stream.total}
                onRetry={stream.retry}
                onResume={stream.resume}
                onStop={stream.stop}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold">Legend</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-2 text-xs">
              {[
                { c: "bg-primary", l: "Patient" },
                { c: "bg-info", l: "Encounter" },
                { c: "bg-ai", l: "Diagnosis" },
                { c: "bg-citation", l: "Medication" },
                { c: "bg-destructive", l: "Allergy" },
                { c: "bg-warning", l: "Lab" },
              ].map((x) => (
                <div key={x.l} className="flex items-center gap-2">
                  <span className={`h-2.5 w-2.5 rounded-full ${x.c}`} />
                  <span className="text-muted-foreground">{x.l}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
