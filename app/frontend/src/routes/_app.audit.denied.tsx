import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/audit/denied")({
  head: () => ({ meta: [{ title: "Denied access — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const rows = [
    ['Today 14:22','Dr. L. Garcia','Tanaka, Y. (MRN-48577)','Out of unit · no consult'],
    ['Today 11:08','Dr. M. Patel','Brooks, A. (MRN-48994)','Specialty mismatch'],
    ['Yesterday','Nurse R. Owens','Romano, S. (MRN-49108)','Bedside not assigned'],
  ];
  return (
    <AppShell>
      <PageHeader title="Denied access events" description="All policy denials are retained for compliance review." />
      <Card className="p-0 overflow-hidden"><table className="w-full text-sm"><thead className="bg-muted/40 text-xs uppercase text-muted-foreground"><tr><th className="px-4 py-2 text-left">When</th><th className="px-4 py-2 text-left">Actor</th><th className="px-4 py-2 text-left">Target</th><th className="px-4 py-2 text-left">Reason</th></tr></thead><tbody>{rows.map((r,i)=>(<tr key={i} className="border-t"><td className="px-4 py-2 text-xs">{r[0]}</td><td className="px-4 py-2">{r[1]}</td><td className="px-4 py-2">{r[2]}</td><td className="px-4 py-2 text-xs text-muted-foreground">{r[3]}</td></tr>))}</tbody></table></Card>
    </AppShell>
  );
}
