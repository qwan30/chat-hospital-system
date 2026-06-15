import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { OcrConfidenceBadge } from "@/components/hms/OcrConfidenceBadge";

export const Route = createFileRoute("/_app/documents/$documentId/review")({
  head: () => ({ meta: [{ title: "OCR review — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="OCR review" description="Low-confidence regions flagged for human verification." />
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-5"><div className="aspect-[3/4] rounded-md bg-muted/40 flex items-center justify-center text-xs text-muted-foreground">[Scanned page preview]</div></Card>
        <Card className="p-5 space-y-3 text-sm">
          {[['Patient name','Eleanor Vance',0.98],['MRN','MRN-48201',0.96],['DOB','1954-03-12',0.71],['Allergies','penicillin (anaphylaxis)',0.45],['LVEF','55%',0.92]].map(([k,v,c],i)=>(<div key={i} className="flex items-center justify-between rounded-md border p-3"><div><p className="text-xs text-muted-foreground">{k}</p><p className="font-medium">{v}</p></div><OcrConfidenceBadge confidence={c as number} /></div>))}
        </Card>
      </div>
    </AppShell>
  );
}
