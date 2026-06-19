import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { SystemHealthCard } from "@/components/hms/SystemHealthCard";

export const Route = createFileRoute("/_app/integrations/hms")({
  head: () => ({ meta: [{ title: "HMS integration — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader
        title="HMS integration"
        description="Live status of the hospital management system connector."
      />
      <SystemHealthCard />
    </AppShell>
  );
}
