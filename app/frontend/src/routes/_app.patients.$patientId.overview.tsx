import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { getPatientOverview, type PatientOverviewResponse } from "@/lib/api/patients";

export const Route = createFileRoute("/_app/patients/$patientId/overview")({
  head: () => ({ meta: [{ title: "Overview — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { patientId } = Route.useParams();

  const {
    data: overview,
    isLoading,
    error,
  } = useQuery<PatientOverviewResponse>({
    queryKey: ["patient-overview", patientId],
    queryFn: () => getPatientOverview(patientId),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Card className="p-5">
          <div className="animate-pulse space-y-3">
            <div className="h-4 w-48 rounded bg-muted" />
            <div className="h-3 w-full rounded bg-muted" />
            <div className="h-3 w-3/4 rounded bg-muted" />
          </div>
        </Card>
        <div className="grid gap-4 md:grid-cols-2">
          <Card className="p-5">
            <div className="animate-pulse space-y-2">
              <div className="h-4 w-32 rounded bg-muted" />
              <div className="h-3 w-full rounded bg-muted" />
              <div className="h-3 w-20 rounded bg-muted" />
            </div>
          </Card>
          <Card className="p-5">
            <div className="animate-pulse space-y-2">
              <div className="h-4 w-24 rounded bg-muted" />
              <div className="h-3 w-full rounded bg-muted" />
            </div>
          </Card>
        </div>
      </div>
    );
  }

  if (error || !overview) {
    return (
      <div className="space-y-4">
        <Card className="p-5">
          <p className="text-sm text-destructive">
            Unable to load patient overview. Please try again.
          </p>
        </Card>
      </div>
    );
  }

  const lastUpdated = overview.last_updated
    ? formatRelativeTime(overview.last_updated)
    : "recently";

  return (
    <div className="space-y-4">
      <Card className="p-5">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold">Patient demographics</h3>
          <span className="text-xs text-muted-foreground">
            {overview.full_name} · MRN {overview.mrn}
          </span>
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
          <div>
            <span className="text-xs text-muted-foreground">DOB</span>
            <p className="font-medium">{overview.dob ?? "—"}</p>
          </div>
          <div>
            <span className="text-xs text-muted-foreground">Gender</span>
            <p className="font-medium">{overview.gender ?? "—"}</p>
          </div>
          <div>
            <span className="text-xs text-muted-foreground">Blood Type</span>
            <p className="font-medium">{overview.blood_type ?? "—"}</p>
          </div>
          <div>
            <span className="text-xs text-muted-foreground">Occupation</span>
            <p className="font-medium">{overview.occupation ?? "—"}</p>
          </div>
        </div>
      </Card>

      {overview.ai_summary && (
        <Card className="p-5">
          <div className="mb-3 flex items-center justify-between border-b pb-2">
            <h3 className="text-sm font-semibold">AI clinical summary</h3>
            <span className="text-xs text-muted-foreground">Generated {lastUpdated}</span>
          </div>
          {renderClinicalSummary(overview.ai_summary)}
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-5">
          <h4 className="mb-2 text-sm font-semibold">Record counts</h4>
          <ul className="space-y-2 text-sm">
            <li className="flex justify-between">
              <span className="text-muted-foreground">Medications</span>
              <span className="font-medium">{overview.medication_count}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-muted-foreground">Labs</span>
              <span className="font-medium">{overview.lab_count}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-muted-foreground">Allergies</span>
              <span className="font-medium">{overview.allergy_count}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-muted-foreground">Appointments</span>
              <span className="font-medium">{overview.appointment_count}</span>
            </li>
          </ul>
        </Card>
        <Card className="p-5">
          <h4 className="mb-2 text-sm font-semibold">Patient info</h4>
          <ul className="space-y-2 text-sm">
            <li className="flex justify-between">
              <span className="text-muted-foreground">CCCD</span>
              <span className="font-medium">{overview.cccd ?? "—"}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-muted-foreground">Patient ID</span>
              <span className="font-mono text-xs">{overview.patient_id}</span>
            </li>
          </ul>
        </Card>
      </div>
    </div>
  );
}

function formatRelativeTime(isoString: string): string {
  const now = Date.now();
  const then = new Date(isoString).getTime();
  const diffMs = now - then;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin} min ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  return `${diffDay}d ago`;
}

function renderClinicalSummary(text: string) {
  if (!text) return null;

  const lines = text.split("\n").filter((l) => l.trim().length > 0);

  return (
    <div className="space-y-2 text-sm leading-relaxed text-foreground/90">
      {lines.map((line, lIdx) => {
        const parts = line.split(/(\*\*[^*]+\*\*|\[[a-zA-Z0-9_-]+\])/g);

        return (
          <p key={lIdx} className="leading-relaxed">
            {parts.map((part, pIdx) => {
              const boldMatch = part.match(/^\*\*([^*]+)\*\*$/);
              if (boldMatch) {
                return (
                  <strong key={pIdx} className="font-semibold text-foreground">
                    {boldMatch[1]}
                  </strong>
                );
              }
              const citeMatch = part.match(/^\[([a-zA-Z0-9_-]+)\]$/);
              if (citeMatch) {
                return (
                  <span
                    key={pIdx}
                    className="inline-flex h-4 min-w-4 items-center justify-center rounded border border-citation/30 bg-citation/10 px-1 mx-0.5 align-middle font-mono text-[10px] font-semibold text-citation"
                  >
                    [{citeMatch[1]}]
                  </span>
                );
              }
              return <span key={pIdx}>{part}</span>;
            })}
          </p>
        );
      })}
    </div>
  );
}
