import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/documents/duplicates")({
  head: () => ({ meta: [{ title: "Duplicates — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader
        title="Duplicate candidates"
        description="Pairs flagged by content fingerprint similarity ≥ 0.92."
      />
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Card
            key={i}
            className="p-4 grid grid-cols-1 md:grid-cols-[1fr_auto_1fr_auto] gap-4 items-center"
          >
            <div>
              <p className="text-sm font-medium">ACC-AHA-AF-Guideline-2024.pdf</p>
              <p className="text-xs text-muted-foreground">Uploaded today · 4.2MB</p>
            </div>
            <span className="text-xs text-muted-foreground">↔ {(0.98 - i * 0.02).toFixed(2)}</span>
            <div>
              <p className="text-sm font-medium">acc_aha_af_2024_v2.pdf</p>
              <p className="text-xs text-muted-foreground">Uploaded 2d ago · 4.1MB</p>
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="outline">
                Keep both
              </Button>
              <Button size="sm">Merge</Button>
            </div>
          </Card>
        ))}
      </div>
    </AppShell>
  );
}
