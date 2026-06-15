import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/dashboard/activity")({
  head: () => ({ meta: [{ title: "Activity feed — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const items=[
    ['09:14','Dr. S. Chen opened chat with Eleanor Vance'],
    ['09:01','New guideline ingested: ACC/AHA AF 2024'],
    ['08:48','Access request approved for Marcus Okafor'],
    ['08:32','Apixaban administered to Vance (RN R. Owens)'],
    ['08:10','Pharmacy flagged apixaban + NSAID for Vance'],
  ];
  return (
    <AppShell>
      <PageHeader title="Activity feed" description="What happened across your workspace today." />
      <Card className="p-0 overflow-hidden"><ul className="divide-y">{items.map((i,k)=>(<li key={k} className="p-3 text-sm"><span className="mr-3 font-mono text-xs text-muted-foreground">{i[0]}</span>{i[1]}</li>))}</ul></Card>
    </AppShell>
  );
}
