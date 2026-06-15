import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";

export const Route = createFileRoute("/_app/dashboard/customize")({
  head: () => ({ meta: [{ title: "Customize dashboard — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="Customize dashboard" description="Pick widgets and ordering for your home view." />
      <Card className="p-5 space-y-3 text-sm">{['My patients','Alerts','Recent chats','Today\'s schedule','Pending access requests','Citation coverage','System health'].map(w=>(<div key={w} className="flex items-center justify-between border-b pb-2 last:border-0"><span>{w}</span><Switch defaultChecked /></div>))}</Card>
    </AppShell>
  );
}
