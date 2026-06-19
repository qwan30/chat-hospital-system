import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/integrations/hms/dlq")({
  head: () => ({ meta: [{ title: "Dead letter queue — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const rows = [
    ["msg-9f3a", "HL7 ADT^A08", "schema mismatch", "3", "12 min ago"],
    ["msg-9f29", "HL7 ORU^R01", "unknown OBX type", "5", "41 min ago"],
    ["msg-9e88", "PDF ingest", "OCR timeout", "2", "1h ago"],
  ];
  return (
    <AppShell>
      <PageHeader
        title="Dead letter queue"
        description="Messages that failed all retries — manual triage required."
      />
      <Card className="p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/40 text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-4 py-2 text-left">Message</th>
              <th className="px-4 py-2 text-left">Type</th>
              <th className="px-4 py-2 text-left">Reason</th>
              <th className="px-4 py-2 text-left">Attempts</th>
              <th className="px-4 py-2 text-left">Since</th>
              <th className="px-4 py-2" />
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-t">
                <td className="px-4 py-2 font-mono text-xs">{r[0]}</td>
                <td className="px-4 py-2">{r[1]}</td>
                <td className="px-4 py-2 text-xs text-muted-foreground">{r[2]}</td>
                <td className="px-4 py-2">{r[3]}</td>
                <td className="px-4 py-2 text-xs">{r[4]}</td>
                <td className="px-4 py-2 text-right">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toast.success("Replayed (mock)")}
                  >
                    Replay
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </AppShell>
  );
}
