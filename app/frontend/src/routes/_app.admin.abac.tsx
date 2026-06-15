import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/admin/abac")({
  head: () => ({ meta: [{ title: "ABAC policy — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="ABAC policy builder" description="Attribute-based access rules layered on top of roles." />
      <Card className="p-5"><pre className="text-xs overflow-auto">{`policy "cardiology-cross-consult" {
  effect = allow
  subject.role     == "cardiologist"
  resource.unit    in ["4N", "ICU-2W"]
  resource.consent.cross_consult == true
  obligation = require_justification
}`}</pre></Card>
    </AppShell>
  );
}
