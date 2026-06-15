import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/documents/$documentId/retry")({
  head: () => ({ meta: [{ title: "Retry OCR — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="Retry OCR" description="Re-queue extraction with adjusted parameters." />
      <Card className="p-6 space-y-3 text-sm">
        <p className="text-muted-foreground">Last attempt failed with: <span className="font-mono text-destructive">PDF_PARSER_TIMEOUT</span> after 60s.</p>
        <div className="rounded-md border bg-muted/40 p-3"><p className="font-medium">Suggested parameters</p><ul className="mt-2 text-xs text-muted-foreground space-y-1"><li>• Use enhanced scan mode</li><li>• Increase timeout to 180s</li><li>• Force layout-aware extraction</li></ul></div>
        <div className="flex justify-end"><Button onClick={()=>toast.success("Retry queued (mock)")}>Re-queue with suggested settings</Button></div>
      </Card>
    </AppShell>
  );
}
