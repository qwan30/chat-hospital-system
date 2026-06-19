import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/settings/profile")({
  head: () => ({ meta: [{ title: "Profile settings — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader
        title="Profile settings"
        description="Personal clinician profile and contact info."
      />
      <Card className="p-6 grid gap-4 sm:grid-cols-2">
        <div>
          <Label>Full name</Label>
          <Input defaultValue="Dr. Sarah Chen" />
        </div>
        <div>
          <Label>Email</Label>
          <Input defaultValue="s.chen@hospital.org" />
        </div>
        <div>
          <Label>Specialty</Label>
          <Input defaultValue="Cardiology" />
        </div>
        <div>
          <Label>NPI</Label>
          <Input defaultValue="1234567890" />
        </div>
        <div className="sm:col-span-2 flex justify-end">
          <Button>Save</Button>
        </div>
      </Card>
    </AppShell>
  );
}
