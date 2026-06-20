import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { getPatientTimeline, type PatientTimelineResponse } from "@/lib/api/patients";

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

  if (timeline.events.length === 0) {
    return (
      <div className="space-y-4">
        <Card className="p-5">
          <p className="text-sm text-muted-foreground">
            No clinical events found for this patient.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card className="p-5">
        <ol className="relative border-l pl-6">
          {timeline.events.map((event, i) => (
            <li key={event.event_id || i} className="mb-5">
              <span className="absolute -left-[7px] mt-1.5 h-3 w-3 rounded-full border-2 border-background bg-primary" />
              <p className="text-xs text-muted-foreground">{formatTimestamp(event.timestamp)}</p>
              <p className="text-sm font-medium">{event.title}</p>
              {event.description && (
                <p className="text-xs text-muted-foreground">{event.description}</p>
              )}
              <span className="text-[10px] uppercase tracking-wide text-muted-foreground/60">
                {event.event_type}
              </span>
            </li>
          ))}
        </ol>
      </Card>
    </div>
  );
}

function formatTimestamp(ts: string): string {
  try {
    const date = new Date(ts);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHr = Math.floor(diffMs / 3600000);
    const diffDay = Math.floor(diffHr / 24);

    if (diffHr < 1) return "Just now";
    if (diffHr < 24)
      return `Today ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
    if (diffDay === 1) return "Yesterday";
    if (diffDay < 7) return `${diffDay}d ago`;
    return date.toLocaleDateString();
  } catch {
    return ts;
  }
}
