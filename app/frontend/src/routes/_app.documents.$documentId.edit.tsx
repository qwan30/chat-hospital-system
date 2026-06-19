import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/documents/$documentId/edit")({
  head: () => ({ meta: [{ title: "Edit document — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="Edit metadata" description="Updates re-trigger indexing." />
      <Card className="p-6 grid gap-4 sm:grid-cols-2">
        <div>
          <Label>Title</Label>
          <Input defaultValue="Echocardiogram Report — Vance" />
        </div>
        <div>
          <Label>Category</Label>
          <Input defaultValue="Imaging" />
        </div>
        <div>
          <Label>Patient MRN</Label>
          <Input defaultValue="MRN-48201" />
        </div>
        <div>
          <Label>Source</Label>
          <Input defaultValue="HMS Imaging Auto-Sync" />
        </div>
        <div className="sm:col-span-2 flex justify-end gap-2">
          <Button variant="outline">Cancel</Button>
          <Button onClick={() => toast.success("Saved (mock)")}>Save & re-index</Button>
        </div>
      </Card>
    </AppShell>
  );
}
