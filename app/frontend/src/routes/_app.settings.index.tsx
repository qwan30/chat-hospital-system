import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";

export const Route = createFileRoute("/_app/settings/")({
  head: () => ({
    meta: [{ title: "Settings — HMS AI Copilot" }],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  return (
    <AppShell>
      <PageHeader title="Settings" description="Profile, security, and AI behavior." />
      <Tabs defaultValue="profile" className="w-full">
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="ai">AI behavior</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="mt-4">
          <Card className="p-6">
            <h3 className="text-sm font-semibold">Clinician profile</h3>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Full name</Label>
                <Input defaultValue="Dr. Sarah Chen" />
              </div>
              <div className="space-y-2">
                <Label>Email</Label>
                <Input defaultValue="s.chen@hospital.org" />
              </div>
              <div className="space-y-2">
                <Label>Specialty</Label>
                <Input defaultValue="Cardiology" />
              </div>
              <div className="space-y-2">
                <Label>NPI</Label>
                <Input defaultValue="1234567890" />
              </div>
            </div>
            <div className="mt-5 flex justify-end">
              <Button>Save changes</Button>
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="mt-4">
          <Card className="p-6">
            <h3 className="text-sm font-semibold">Security</h3>
            <div className="mt-4 space-y-4">
              <Row k="Multi-factor authentication" v="Required at every sign-in" badge="Enforced" />
              <Row k="Device trust" v="Remember this device for 30 days" toggle />
              <Row k="Session timeout" v="Sign out after 15 minutes of inactivity" toggle defaultOn />
              <Row k="Break-glass access" v="Allow temporary PHI access in emergencies (audit-heavy)" toggle />
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="ai" className="mt-4">
          <Card className="p-6">
            <h3 className="text-sm font-semibold">AI behavior</h3>
            <div className="mt-4 space-y-4">
              <Row k="Citations required" v="Block answers without retrievable sources" toggle defaultOn />
              <Row k="Safe refusal" v="Refuse when confidence is below threshold" toggle defaultOn />
              <Row k="PHI redaction in prompts" v="Strip identifiers before sending to the model" toggle defaultOn />
              <Row k="Show reasoning trace" v="Display the model's evidence retrieval steps" toggle />
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="mt-4">
          <Card className="p-6">
            <h3 className="text-sm font-semibold">Notifications</h3>
            <div className="mt-4 space-y-4">
              <Row k="Critical patient alerts" v="Push + email" toggle defaultOn />
              <Row k="Access request decisions" v="Email only" toggle defaultOn />
              <Row k="Weekly metrics digest" v="Sundays at 6pm" toggle />
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </AppShell>
  );
}

function Row({
  k,
  v,
  toggle,
  defaultOn,
  badge,
}: {
  k: string;
  v: string;
  toggle?: boolean;
  defaultOn?: boolean;
  badge?: string;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border p-4">
      <div>
        <p className="text-sm font-medium">{k}</p>
        <p className="text-xs text-muted-foreground">{v}</p>
      </div>
      {toggle ? (
        <Switch defaultChecked={defaultOn} />
      ) : badge ? (
        <Badge variant="secondary" className="bg-success/10 text-success">{badge}</Badge>
      ) : null}
    </div>
  );
}