import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";

export const Route = createFileRoute("/_app/settings/security")({
  head: () => ({ meta: [{ title: "Security — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="Security" description="MFA, device trust, session timeout, break-glass." />
      <Card className="p-6 space-y-4 text-sm">
        {[
          ["Multi-factor auth", "Required at every sign-in", "enforced"],
          ["Device trust", "Remember device for 30 days", "toggle"],
          ["Session timeout", "Sign out after 15 minutes idle", "toggle-on"],
          ["Break-glass", "Emergency PHI access (audit-heavy)", "toggle"],
        ].map(([k, v, kind], i) => (
          <div key={i} className="flex items-center justify-between rounded-lg border p-4">
            <div>
              <p className="font-medium">{k}</p>
              <p className="text-xs text-muted-foreground">{v}</p>
            </div>
            {kind === "enforced" ? (
              <Badge variant="secondary" className="bg-success/10 text-success">
                Enforced
              </Badge>
            ) : (
              <Switch defaultChecked={kind === "toggle-on"} />
            )}
          </div>
        ))}
      </Card>
    </AppShell>
  );
}
