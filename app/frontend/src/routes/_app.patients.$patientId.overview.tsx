import { createFileRoute } from "@tanstack/react-router";
import { Card } from "@/components/ui/card";
import { CitationChip } from "@/components/hms/CitationChip";

export const Route = createFileRoute("/_app/patients/$patientId/overview")({
  head: () => ({ meta: [{ title: "Overview — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <div className="space-y-4">
      <Card className="p-5">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold">AI clinical summary</h3>
          <span className="text-xs text-muted-foreground">Generated 4 min ago</span>
        </div>
        <p className="text-sm leading-relaxed text-foreground/90">
          72-year-old female with paroxysmal atrial fibrillation (CHA<sub>2</sub>DS<sub>2</sub>-VASc 4, HAS-BLED 2) on apixaban 5mg BID since Mar 2025.
          Most recent echo (today 09:14) shows preserved LVEF 55%, mild LA dilation. No prior bleeding events. INR not applicable.
        </p>
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          <CitationChip n={1} sourceId="c-001" />
          <CitationChip n={2} sourceId="c-002" />
          <CitationChip n={3} sourceId="c-003" />
        </div>
      </Card>
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-5"><h4 className="mb-2 text-sm font-semibold">Active problems</h4><ul className="space-y-1 text-sm">{['Atrial fibrillation','Hypertension','Hyperlipidemia','GERD'].map(x=><li key={x} className="flex justify-between"><span>{x}</span><span className="text-xs text-muted-foreground">Active</span></li>)}</ul></Card>
        <Card className="p-5"><h4 className="mb-2 text-sm font-semibold">Allergies</h4><ul className="space-y-1 text-sm"><li className="flex justify-between"><span>Penicillin</span><span className="text-xs text-destructive">Anaphylaxis</span></li><li className="flex justify-between"><span>Sulfa drugs</span><span className="text-xs text-warning">Rash</span></li></ul></Card>
      </div>
</div>
  );
}
