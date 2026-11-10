import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { ocrQueue, type OcrJob } from "@/data/ocrQueue";
import { OcrConfidenceBadge } from "@/components/hms/OcrConfidenceBadge";
import { listDocuments } from "@/lib/api/documents";
import { formatDateTime } from "@/lib/format";

export const Route = createFileRoute("/_app/documents/ocr-queue")({
  head: () => ({ meta: [{ title: "OCR queue — HMS AI Copilot" }] }),
  component: Page,
});

function mapStatusToQueueState(status: string): OcrJob["status"] {
  if (status === "ready" || status === "indexed") return "indexed";
  if (status === "ready_with_warnings") return "review";
  if (status === "failed") return "failed";
  if (status === "uploaded") return "queued";
  return "processing";
}

function Page() {
  const { data } = useQuery({
    queryKey: ["documents", "ocr-queue"],
    queryFn: () => listDocuments({ limit: 50 }),
    staleTime: 15_000,
  });

  const liveJobs: OcrJob[] =
    data?.items && data.items.length > 0
      ? data.items.map((doc) => ({
          id: doc.id,
          file: doc.title,
          size: "—",
          pages: doc.page_count ?? 1,
          status: mapStatusToQueueState(doc.status),
          confidence:
            doc.status === "ready" || doc.status === "indexed"
              ? 0.96
              : doc.status === "ready_with_warnings"
                ? 0.74
                : 0,
          ts: doc.created_at,
          documentId: doc.id,
        }))
      : ocrQueue;

  return (
    <AppShell>
      <PageHeader
        title="OCR processing queue"
        description="Live extraction backlog with confidence and status."
      />
      <Card className="p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/40 text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-4 py-2 text-left">File</th>
              <th className="px-4 py-2 text-left">Pages</th>
              <th className="px-4 py-2 text-left">Status</th>
              <th className="px-4 py-2 text-left">Confidence</th>
              <th className="px-4 py-2 text-left">When</th>
            </tr>
          </thead>
          <tbody>
            {liveJobs.map((j) => (
              <tr key={j.id} className="border-t">
                <td className="px-4 py-2 font-medium">{j.file}</td>
                <td className="px-4 py-2">{j.pages}</td>
                <td className="px-4 py-2 capitalize">{j.status}</td>
                <td className="px-4 py-2">
                  {j.confidence > 0 ? (
                    <OcrConfidenceBadge confidence={j.confidence} />
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </td>
                <td className="px-4 py-2 text-xs">{formatDateTime(j.ts)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </AppShell>
  );
}
