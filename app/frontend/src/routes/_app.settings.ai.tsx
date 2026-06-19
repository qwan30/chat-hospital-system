import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";

export const Route = createFileRoute("/_app/settings/ai")({
  head: () => ({ meta: [{ title: "AI behavior — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader
        title="AI behavior"
        description="Confidence thresholds, refusal behavior, citation policy."
      />
      <Card className="p-6 space-y-4 text-sm">
        {[
          ["Citations required", "Block answers without retrievable sources", true],
          ["Safe refusal", "Refuse when confidence is below threshold", true],
          ["PHI redaction", "Strip identifiers before sending to model", true],
          ["Show reasoning trace", "Display retrieval steps", false],
        ].map(([k, v, d], i) => (
          <div key={i} className="flex items-center justify-between rounded-lg border p-4">
            <div>
              <p className="font-medium">{k}</p>
              <p className="text-xs text-muted-foreground">{v}</p>
            </div>
            <Switch defaultChecked={d as boolean} />
          </div>
        ))}
      </Card>
    </AppShell>
  );
}
