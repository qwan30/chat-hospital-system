import { createFileRoute } from "@tanstack/react-router";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/patients/$patientId/medications")({
  head: () => ({ meta: [{ title: "Medications — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <div className="space-y-4">
      <Card className="p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/40 text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="px-4 py-2 text-left">Drug</th>
              <th className="px-4 py-2 text-left">Dose</th>
              <th className="px-4 py-2 text-left">Route</th>
              <th className="px-4 py-2 text-left">Started</th>
              <th className="px-4 py-2 text-left">Prescriber</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["Apixaban", "5 mg BID", "PO", "2025-03-04", "Dr. S. Chen"],
              ["Metoprolol succinate", "50 mg daily", "PO", "2024-11-12", "Dr. S. Chen"],
              ["Atorvastatin", "40 mg HS", "PO", "2023-09-01", "Dr. M. Patel"],
              ["Lisinopril", "10 mg daily", "PO", "2022-04-15", "Dr. M. Patel"],
              ["Pantoprazole", "40 mg daily", "PO", "2025-01-20", "Dr. L. Garcia"],
            ].map((r, i) => (
              <tr key={i} className="border-t">
                <td className="px-4 py-2 font-medium">{r[0]}</td>
                <td className="px-4 py-2">{r[1]}</td>
                <td className="px-4 py-2">{r[2]}</td>
                <td className="px-4 py-2 text-xs">{r[3]}</td>
                <td className="px-4 py-2 text-xs text-muted-foreground">{r[4]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
