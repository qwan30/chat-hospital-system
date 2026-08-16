import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { getPatientTimeline, type PatientTimelineResponse } from "@/lib/api/patients";
import { ClinicalTimelinePanel } from "@/components/hms/ClinicalTimelinePanel";

export const Route = createFileRoute("/_app/patients/$patientId/timeline")({
  head: () => ({ meta: [{ title: "Timeline — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { patientId } = Route.useParams();

  const {
    data: timeline,
    isLoading,
    error,
  } = useQuery<PatientTimelineResponse>({
    queryKey: ["patient-timeline", patientId],
    queryFn: () => getPatientTimeline(patientId),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Card className="p-5">
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex gap-3">
                <div className="mt-1.5 h-3 w-3 shrink-0 rounded-full bg-muted" />
                <div className="flex-1 space-y-1">
                  <div className="h-3 w-20 rounded bg-muted" />
                  <div className="h-4 w-48 rounded bg-muted" />
                  <div className="h-3 w-32 rounded bg-muted" />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    );
  }

  if (error || !timeline) {
    return (
      <div className="space-y-4">
        <Card className="p-5">
          <p className="text-sm text-destructive">Unable to load timeline. Please try again.</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ClinicalTimelinePanel events={timeline.events} />
    </div>
  );
}
