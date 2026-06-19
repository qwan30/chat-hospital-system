import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/audit/export")({
  head: () => ({ meta: [{ title: "Audit export — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader
        title="Audit export"
        description="Generate compliance-ready exports of audit logs."
      />
      <Card className="p-6 grid gap-3 sm:grid-cols-2 text-sm">
        <Row k="Range" v="2026-05-01 → 2026-06-12" />
        <Row k="Format" v="JSONL (signed)" />
        <Row k="Events" v="48,221 records" />
        <Row k="Size (est.)" v="86 MB" />
        <div className="sm:col-span-2 flex justify-end">
          <Button onClick={() => toast.success("Export queued — link will arrive by email (mock)")}>
            Generate export
          </Button>
        </div>
      </Card>
    </AppShell>
  );
}
function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between border-b pb-1">
      <span className="text-muted-foreground">{k}</span>
      <span className="font-medium">{v}</span>
    </div>
  );
}
