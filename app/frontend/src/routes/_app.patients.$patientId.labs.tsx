import { createFileRoute } from "@tanstack/react-router";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/patients/$patientId/labs")({
  head: () => ({ meta: [{ title: "Labs — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <div className="space-y-4">
      <Card className="p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/40 text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="px-4 py-2 text-left">Analyte</th>
              <th className="px-4 py-2 text-left">Value</th>
              <th className="px-4 py-2 text-left">Ref</th>
              <th className="px-4 py-2 text-left">Flag</th>
              <th className="px-4 py-2 text-left">Collected</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["Sodium", "139 mmol/L", "135-145", "—", "Today 06:20"],
              ["Potassium", "4.2 mmol/L", "3.5-5.0", "—", "Today 06:20"],
              ["Creatinine", "1.1 mg/dL", "0.6-1.2", "—", "Today 06:20"],
              ["Hemoglobin", "11.2 g/dL", "12.0-15.5", "L", "Today 06:20"],
              ["Platelets", "188 ×10⁹/L", "150-400", "—", "Today 06:20"],
              ["INR", "1.0", "0.8-1.2", "—", "Today 06:20"],
              ["BNP", "420 pg/mL", "<100", "H", "Today 06:20"],
              ["Troponin I", "0.02 ng/mL", "<0.04", "—", "Today 06:20"],
            ].map((r, i) => (
              <tr key={i} className="border-t">
                <td className="px-4 py-2">{r[0]}</td>
                <td className="px-4 py-2 font-medium">{r[1]}</td>
                <td className="px-4 py-2 text-muted-foreground">{r[2]}</td>
                <td
                  className={
                    "px-4 py-2 font-semibold " +
                    (r[3] === "H"
                      ? "text-destructive"
                      : r[3] === "L"
                        ? "text-warning"
                        : "text-muted-foreground")
                  }
                >
                  {r[3]}
                </td>
                <td className="px-4 py-2 text-xs">{r[4]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
