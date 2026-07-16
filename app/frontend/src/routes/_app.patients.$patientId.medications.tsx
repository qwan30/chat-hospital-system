import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { getPatientMedications, type PatientMedicationResponse } from "@/lib/api/patients";

export const Route = createFileRoute("/_app/patients/$patientId/medications")({
  head: () => ({ meta: [{ title: "Medications — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { patientId } = Route.useParams();

  const {
    data: meds,
    isLoading,
    error,
  } = useQuery<PatientMedicationResponse>({
    queryKey: ["patient-medications", patientId],
    queryFn: () => getPatientMedications(patientId),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Card className="p-0 overflow-hidden">
          <div className="animate-pulse">
            <div className="bg-muted/40 px-4 py-2">
              <div className="h-4 w-64 rounded bg-muted" />
            </div>
            {[1, 2, 3].map((i) => (
              <div key={i} className="border-t px-4 py-2">
                <div className="h-4 w-32 rounded bg-muted" />
              </div>
            ))}
          </div>
        </Card>
      </div>
    );
  }

  if (error || !meds) {
    return (
      <div className="space-y-4">
        <Card className="p-5">
          <p className="text-sm text-destructive">Unable to load medications. Please try again.</p>
        </Card>
      </div>
    );
  }

  if (meds.medications.length === 0) {
    return (
      <div className="space-y-4">
        <Card className="p-5">
          <p className="text-sm text-muted-foreground">No medications found for this patient.</p>
        </Card>
      </div>
    );
  }

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
            {meds.medications.map((med, i) => (
              <tr key={`${med.drug_name}-${i}`} className="border-t">
                <td className="px-4 py-2 font-medium">{med.drug_name}</td>
                <td className="px-4 py-2">{med.dose ?? "—"}</td>
                <td className="px-4 py-2">{med.route ?? "—"}</td>
                <td className="px-4 py-2 text-xs">{med.started ?? "—"}</td>
                <td className="px-4 py-2 text-xs text-muted-foreground">{med.prescriber ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
