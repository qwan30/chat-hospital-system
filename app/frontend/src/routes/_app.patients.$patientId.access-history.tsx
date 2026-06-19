import { createFileRoute } from "@tanstack/react-router";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/patients/$patientId/access-history")({
  head: () => ({ meta: [{ title: "Access history — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <div className="space-y-4">
      <Card className="p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/40 text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="px-4 py-2 text-left">When</th>
              <th className="px-4 py-2 text-left">Actor</th>
              <th className="px-4 py-2 text-left">Action</th>
              <th className="px-4 py-2 text-left">Reason</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["Today 09:14", "Dr. S. Chen", "View overview", "Direct care"],
              ["Today 08:32", "RN R. Owens", "Read vitals", "Bedside rounding"],
              ["Today 06:21", "Lab Auto-Sync", "Append labs", "HL7 ingest"],
              ["Yesterday", "Dr. M. Patel", "Cross-consult", "Cardiology second opinion"],
              ["2d ago", "Front desk", "Admit register", "Intake"],
            ].map((r, i) => (
              <tr key={i} className="border-t">
                <td className="px-4 py-2 text-xs">{r[0]}</td>
                <td className="px-4 py-2">{r[1]}</td>
                <td className="px-4 py-2">{r[2]}</td>
                <td className="px-4 py-2 text-xs text-muted-foreground">{r[3]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
