import { createFileRoute } from "@tanstack/react-router";
import { Card } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { getPatientMedicationReview } from "@/lib/api/medication-safety";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/_app/patients/$patientId/medication-review")({
  head: () => ({ meta: [{ title: "Medication review — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { patientId } = Route.useParams();

  const {
    data: warnings,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["patients", patientId, "medication-review"],
    queryFn: () => getPatientMedicationReview(patientId),
  });

  return (
    <div className="space-y-4">
      <Card className="p-5">
        <h3 className="text-sm font-semibold">Pharmacist review — AI suggestions</h3>
        {isLoading && (
          <div className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Running drug interaction checks...
          </div>
        )}
        {error && (
          <div className="mt-3 text-sm text-destructive bg-destructive/10 p-3 rounded-md">
            Failed to run medication review.
          </div>
        )}
        {!isLoading && !error && warnings?.length === 0 && (
          <div className="mt-3 text-sm text-muted-foreground">
            No known drug interactions detected.
          </div>
        )}
        {warnings && warnings.length > 0 && (
          <ul className="mt-3 space-y-3 text-sm">
            {warnings.map((w, idx) => (
              <li
                key={idx}
                className={`rounded-md border p-3 ${
                  w.severity === "critical"
                    ? "border-destructive/30 bg-destructive/5"
                    : w.severity === "high"
                      ? "border-destructive/20 bg-destructive/5"
                      : w.severity === "medium"
                        ? "border-warning/30 bg-warning/5"
                        : ""
                }`}
              >
                <p className="font-medium">
                  {w.drug_name} + {w.interacting_entity}
                </p>
                <p className="text-xs text-muted-foreground">{w.message}</p>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
