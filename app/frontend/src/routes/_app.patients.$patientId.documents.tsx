import { createFileRoute } from "@tanstack/react-router";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/patients/$patientId/documents")({
  head: () => ({ meta: [{ title: "Documents — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <div className="space-y-4">
      <Card className="p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/40 text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="px-4 py-2 text-left">Document</th>
              <th className="px-4 py-2 text-left">Type</th>
              <th className="px-4 py-2 text-left">Date</th>
              <th className="px-4 py-2 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["Echo Report Vance 2026-06-12", "Imaging", "Today", "Indexed"],
              ["Cardiology Consult — Chen", "Note", "2d ago", "Indexed"],
              ["ED Triage Note", "Note", "2d ago", "Indexed"],
              ["EKG strip 6-lead", "Imaging", "2d ago", "Indexed"],
              ["Outpatient apixaban prescription", "Rx", "Mar 2025", "Indexed"],
            ].map((r, i) => (
              <tr key={i} className="border-t">
                <td className="px-4 py-2 font-medium">{r[0]}</td>
                <td className="px-4 py-2">{r[1]}</td>
                <td className="px-4 py-2 text-xs">{r[2]}</td>
                <td className="px-4 py-2 text-xs text-success">{r[3]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
