import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { TraceTimeline } from "@/components/hms/TraceTimeline";
import { ErrorState } from "@/components/hms/ErrorState";
import { traces, type Trace } from "@/data/traces";
import { getQueryTrace, type RagTraceResponse } from "@/lib/api/citations";

export const Route = createFileRoute("/_app/audit/traces/$traceId")({
  head: () => ({ meta: [{ title: "Trace — HMS AI Copilot" }] }),
  component: Page,
});

function mapRagTraceToTimeline(resp: RagTraceResponse): Trace {
  const totalMs = Math.max(resp.latency_ms ?? 300, 50);
  const retrievalMs = Math.round(totalMs * 0.3);
  const generationMs = Math.max(totalMs - retrievalMs, 10);
  return {
    id: resp.query_id,
    query: resp.question,
    user: "Authenticated Clinician",
    totalMs,
    ts: resp.created_at,
    spans: [
      {
        id: "span-bff",
        name: `POST /api/v1/chat (${resp.pipeline ?? "rag"})`,
        service: "BFF",
        startOffsetMs: 0,
        durationMs: totalMs,
        status: resp.status === "failed" ? "error" : "ok",
      },
      {
        id: "span-rag",
        name: `Retrieval · ${resp.evidence.length} chunks`,
        service: "RAG",
        startOffsetMs: 5,
        durationMs: retrievalMs,
        status: resp.evidence.length > 0 ? "ok" : "warn",
      },
      {
        id: "span-llm",
        name: `LLM · ${resp.model ?? "clinical-llm"}`,
        service: "Ollama",
        startOffsetMs: retrievalMs,
        durationMs: generationMs,
        status: resp.status === "failed" ? "error" : "ok",
      },
    ],
  };
}

function Page() {
  const { traceId } = Route.useParams();
  const staticMatch = traces.find((x) => x.id === traceId);
  const { data: apiTrace } = useQuery({
    queryKey: ["chat", "trace", traceId],
    queryFn: () => getQueryTrace(traceId),
    enabled: !staticMatch,
    retry: false,
  });

  const t = staticMatch ?? (apiTrace ? mapRagTraceToTimeline(apiTrace) : null);

  if (!t) {
    return (
      <AppShell>
        <ErrorState
          code="TRACE_NOT_FOUND"
          title={`Trace ${traceId} not found`}
          description="No audit or RAG execution trace matched the requested identifier."
          cta={{ label: "Back to Audit", to: "/audit" }}
        />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        title={`Trace ${t.id}`}
        description={`${t.query} · ${t.spans.length} spans · ${t.totalMs}ms total`}
        backLink={{ to: "/audit", label: "Back to Audit" }}
      />
      <TraceTimeline trace={t} />
    </AppShell>
  );
}
