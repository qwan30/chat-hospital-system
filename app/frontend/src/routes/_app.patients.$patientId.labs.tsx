import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { getPatientLabs, type PatientLabResponse } from "@/lib/api/patients";

export const Route = createFileRoute("/_app/patients/$patientId/labs")({
  head: () => ({ meta: [{ title: "Labs — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { patientId } = Route.useParams();

  const {
    data: labsResp,
    isLoading,
    error,
  } = useQuery<PatientLabResponse>({
    queryKey: ["patient-labs", patientId],
    queryFn: () => getPatientLabs(patientId),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Card className="p-0 overflow-hidden">
          <div className="animate-pulse">
            <div className="bg-muted/40 px-4 py-2">
              <div className="h-4 w-64 rounded bg-muted" />
            </div>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="border-t px-4 py-2">
                <div className="h-4 w-32 rounded bg-muted" />
              </div>
            ))}
          </div>
        </Card>
      </div>
    );
  }

  if (error || !labsResp) {
    return (
      <div className="space-y-4">
        <Card className="p-5">
          <p className="text-sm text-destructive">Unable to load lab results. Please try again.</p>
        </Card>
      </div>
    );
  }

  if (labsResp.labs.length === 0) {
    return (
      <div className="space-y-4">
        <Card className="p-5">
          <p className="text-sm text-muted-foreground">No lab results found for this patient.</p>
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
              <th className="px-4 py-2 text-left">Analyte</th>
              <th className="px-4 py-2 text-left">Value</th>
              <th className="px-4 py-2 text-left">Ref</th>
              <th className="px-4 py-2 text-left">Flag</th>
              <th className="px-4 py-2 text-left">Collected</th>
            </tr>
          </thead>
          <tbody>
            {labsResp.labs.map((lab, i) => {
              const flagClass =
                lab.flag === "H"
                  ? "text-destructive"
                  : lab.flag === "L"
                    ? "text-warning"
                    : "text-muted-foreground";
              return (
                <tr key={`${lab.analyte}-${i}`} className="border-t">
                  <td className="px-4 py-2">{lab.analyte}</td>
                  <td className="px-4 py-2 font-medium">{lab.value ?? "—"}</td>
                  <td className="px-4 py-2 text-muted-foreground">{lab.reference_range ?? "—"}</td>
                  <td className={`px-4 py-2 font-semibold ${flagClass}`}>
                    {lab.flag === "H" ? "H" : lab.flag === "L" ? "L" : "—"}
                  </td>
                  <td className="px-4 py-2 text-xs">{lab.collected ?? "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
