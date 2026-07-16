import { createFileRoute, Link, Outlet, useRouterState } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/hms/StatusBadge";
import { getPatient } from "@/lib/api/patients";
import { MessageSquare, RefreshCw, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSession } from "@/lib/session";
import { canAccessPatientTab } from "@/lib/rbac";
import { useQuery } from "@tanstack/react-query";

export const Route = createFileRoute("/_app/patients/$patientId")({
  head: () => ({ meta: [{ title: "Patient — HMS AI Copilot" }] }),
  component: PatientLayout,
});

function calculateAge(dob: string | null): number | string {
  if (!dob) return "--";
  const birthDate = new Date(dob);
  const diffMs = Date.now() - birthDate.getTime();
  const ageDt = new Date(diffMs);
  return Math.abs(ageDt.getUTCFullYear() - 1970);
}

function PatientLayout() {
  const { patientId } = Route.useParams();
  const path = useRouterState({ select: (s) => s.location.pathname });
  const { session } = useSession();

  const {
    data: p,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["patient", patientId],
    queryFn: () => getPatient(patientId),
  });

  const allTabs = [
    { url: `/patients/${patientId}/overview`, label: "Overview" },
    { url: `/patients/${patientId}/timeline`, label: "Timeline" },
    { url: `/patients/${patientId}/labs`, label: "Labs" },
    { url: `/patients/${patientId}/medications`, label: "Medications" },
    { url: `/patients/${patientId}/documents`, label: "Documents" },
    { url: `/patients/${patientId}/access-history`, label: "Access history" },
    { url: `/patients/${patientId}/medication-review`, label: "Med review" },
  ];
  const slugFromUrl = (u: string) => u.split("/").pop()!;
  const tabs = session
    ? allTabs.filter((t) => canAccessPatientTab(session.role, slugFromUrl(t.url)))
    : allTabs;

  return (
    <AppShell>
      {isLoading ? (
        <>
          <PageHeader title="Loading patient..." description="Fetching from HMS" />
          <Card className="p-6 text-sm text-muted-foreground">Loading...</Card>
        </>
      ) : isError || !p ? (
        <>
          <PageHeader
            title="Patient not found"
            description="No record matches this MRN in your accessible scope."
          />
          <Card className="p-6 text-sm text-muted-foreground">
            The record may be archived or outside your unit.{" "}
            <Link to="/patients" className="text-primary underline">
              Back to roster
            </Link>
          </Card>
        </>
      ) : (
        <>
          <PageHeader
            title={p.full_name}
            description={`${calculateAge(p.dob)} · ${p.department || "--"} · MRN ${p.mrn}`}
            backLink={{ to: "/patients", label: "Back to Patients" }}
            chips={
              <>
                <Badge variant="secondary" className="capitalize">
                  {p.status}
                </Badge>
                <StatusBadge status="allow" />
              </>
            }
            actions={
              <>
                <Button size="sm" variant="outline" asChild>
                  <Link to="/patients/$patientId/refresh" params={{ patientId }}>
                    <RefreshCw className="mr-1 h-4 w-4" />
                    Refresh HMS
                  </Link>
                </Button>
                <Button size="sm" asChild>
                  <Link to="/chat/patients/$patientId" params={{ patientId }}>
                    <MessageSquare className="mr-1 h-4 w-4" />
                    Open chat
                  </Link>
                </Button>
              </>
            }
          />
          <div className="mb-4 flex flex-wrap gap-1 border-b">
            {tabs.map((t) => (
              <Link
                key={t.url}
                to={t.url as any}
                className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium transition ${path.startsWith(t.url) ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}
              >
                {t.label}
              </Link>
            ))}
          </div>
          <Outlet />
        </>
      )}
    </AppShell>
  );
}
