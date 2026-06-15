import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/citations/compare")({
  head: () => ({ meta: [{ title: "Compare citations — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="Compare citations" description="Side-by-side passages used to ground a single answer." />
      <div className="grid gap-4 md:grid-cols-2">
        {[
          ['ACC/AHA AF Guideline 2024 — §5.2','For non-valvular AF with CHA₂DS₂-VASc ≥2, direct oral anticoagulants are preferred over warfarin (Class I, LOE A).'],
          ['ESC AF Guideline 2024 — §6.4','DOACs are recommended over VKAs for stroke prevention in eligible AF patients (Class I).'],
        ].map(([t,b])=>(<Card key={t} className="p-5"><p className="text-xs font-medium text-primary">{t}</p><p className="mt-2 text-sm">{b}</p></Card>))}
      </div>
    </AppShell>
  );
}
