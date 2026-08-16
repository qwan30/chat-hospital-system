import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { MetricCard } from "@/components/hms/MetricCard";
import { Card } from "@/components/ui/card";
import { getVectorMetrics } from "@/lib/api/metrics";

export const Route = createFileRoute("/_app/integrations/vector-index")({
  head: () => ({ meta: [{ title: "Vector index — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { data: metrics } = useQuery({
    queryKey: ["vector-metrics"],
    queryFn: getVectorMetrics,
  });

  const formattedDocuments = metrics ? metrics.indexed_document_count.toLocaleString() : "—";
  const formattedChunks = metrics ? metrics.active_chunk_count.toLocaleString() : "—";

  return (
    <AppShell>
      <PageHeader title="Vector index" description="Embedding storage and retrieval performance." />
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard
          label="Documents indexed"
          value={formattedDocuments}
          delta={{ value: "+1,204", positive: true }}
          tone="primary"
        />
        <MetricCard
          label="Chunks"
          value={formattedChunks}
          delta={{ value: "+38k", positive: true }}
          tone="secondary"
        />
        <MetricCard
          label="Query P95"
          value="84ms"
          delta={{ value: "-9ms", positive: true }}
          tone="ai"
        />
        <MetricCard
          label="Recall @10"
          value="0.93"
          delta={{ value: "+0.01", positive: true }}
          tone="citation"
        />
      </div>
      <Card className="mt-6 p-5 text-sm text-muted-foreground">
        Index sharding map (mock).
        {metrics && (
          <div className="mt-4">
            <h3 className="font-semibold mb-2">Sources</h3>
            <ul className="list-disc pl-5">
              {metrics.sources.map((source) => (
                <li key={source.document_id}>
                  {source.document_id}: {source.chunk_count} chunks
                </li>
              ))}
            </ul>
          </div>
        )}
      </Card>
    </AppShell>
  );
}
