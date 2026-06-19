import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload } from "lucide-react";

export const Route = createFileRoute("/_app/documents/upload")({
  head: () => ({ meta: [{ title: "Upload documents — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader
        title="Upload documents"
        description="Files ingest into the OCR + vector pipeline."
      />
      <Card className="flex flex-col items-center justify-center border-dashed p-12 text-center">
        <Upload className="h-10 w-10 text-muted-foreground" />
        <p className="mt-3 text-sm font-medium">Drop PDFs, scans, or HL7 messages here</p>
        <p className="text-xs text-muted-foreground">Max 25MB · PDF · DOCX · JPG · HL7</p>
        <Button className="mt-4">Browse files</Button>
      </Card>
    </AppShell>
  );
}
