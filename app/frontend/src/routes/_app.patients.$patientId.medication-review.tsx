import { createFileRoute } from "@tanstack/react-router";
import { Card } from "@/components/ui/card";


export const Route = createFileRoute("/_app/patients/$patientId/medication-review")({
  head: () => ({ meta: [{ title: "Medication review — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <div className="space-y-4">
      <Card className="p-5">
        <h3 className="text-sm font-semibold">Pharmacist review — AI suggestions</h3>
        <ul className="mt-3 space-y-3 text-sm">
          <li className="rounded-md border border-warning/30 bg-warning/5 p-3"><p className="font-medium">Lisinopril + Spironolactone</p><p className="text-xs text-muted-foreground">Hyperkalemia risk. K+ trending 4.2 → recheck in 48h.</p></li>
          <li className="rounded-md border border-destructive/30 bg-destructive/5 p-3"><p className="font-medium">Apixaban + NSAID (PRN ibuprofen)</p><p className="text-xs text-muted-foreground">Major bleeding risk. Recommend acetaminophen alternative.</p></li>
          <li className="rounded-md border p-3"><p className="font-medium">Atorvastatin dose appropriate</p><p className="text-xs text-muted-foreground">LDL-C target met. No change.</p></li>
        </ul>
      </Card>
</div>
  );
}
