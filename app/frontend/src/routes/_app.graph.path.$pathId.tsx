import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/graph/path/$pathId")({
  head: () => ({ meta: [{ title: "Reasoning path — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { pathId } = Route.useParams();
  return (
    <AppShell>
      <PageHeader
        title={`Reasoning path ${pathId}`}
        description="Why the model connected these facts."
      />
      <Card className="p-5">
        <ol className="space-y-3 text-sm list-decimal pl-5">
          <li>Patient has paroxysmal AF (problem list)</li>
          <li>CHA₂DS₂-VASc = 4 (calculated from age, sex, HTN, no prior stroke)</li>
          <li>ACC/AHA AF guideline §5.2 recommends DOAC at score ≥2</li>
          <li>Apixaban prescribed since Mar 2025 (med list)</li>
          <li>No renal dose-reduction triggers (CrCl &gt; 50)</li>
        </ol>
      </Card>
    </AppShell>
  );
}
