import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/access-policy")({
  head: () => ({ meta: [{ title: "Access policy — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader
        title="Access policy"
        description="Active RBAC / ABAC rules governing retrieval and chat."
      />
      <div className="grid gap-4 md:grid-cols-2">
        {[
          [
            "Cardiologist (default)",
            "Read all cardiology unit patients · cross-consult requires justification · audit-logged.",
          ],
          ["Hospitalist", "Read assigned patients only · cross-unit requires admin approval."],
          [
            "Nurse (RN)",
            "Read bedside assignments · medications & vitals · no diagnostic notes outside unit.",
          ],
          ["Pharmacist", "Read all medication orders + active labs · no progress notes."],
          ["Front desk", "Demographics only · no PHI beyond MRN/contact."],
          [
            "Admin",
            "Approve access requests · audit export · break-glass requires 2-person sign-off.",
          ],
        ].map(([k, v]) => (
          <Card key={k} className="p-5">
            <h4 className="text-sm font-semibold">{k}</h4>
            <p className="mt-2 text-sm text-muted-foreground">{v}</p>
          </Card>
        ))}
      </div>
    </AppShell>
  );
}
