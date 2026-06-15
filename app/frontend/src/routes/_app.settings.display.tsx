import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";


export const Route = createFileRoute("/_app/settings/display")({
  head: () => ({ meta: [{ title: "Display preferences — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="Display preferences" description="Theme, density, and accessibility." />
      <Card className="p-6 text-sm text-muted-foreground">Theme · Density · Reduce motion · High contrast (mock controls).</Card>
    </AppShell>
  );
}
