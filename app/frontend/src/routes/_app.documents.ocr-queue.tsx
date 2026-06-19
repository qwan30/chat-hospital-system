import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { ocrQueue } from "@/data/ocrQueue";
import { OcrConfidenceBadge } from "@/components/hms/OcrConfidenceBadge";
import { formatDateTime } from "@/lib/format";

export const Route = createFileRoute("/_app/documents/ocr-queue")({
  head: () => ({ meta: [{ title: "OCR queue — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
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
            {ocrQueue.map((j) => (
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
