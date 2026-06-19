import { createFileRoute } from "@tanstack/react-router";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/patients/$patientId/timeline")({
  head: () => ({ meta: [{ title: "Timeline — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <div className="space-y-4">
      <Card className="p-5">
        <ol className="relative border-l pl-6">
          {[
            {
              t: "Today 09:14",
              e: "Echocardiogram completed",
              d: "LVEF 55%, mild LA dilation. Imaging.",
            },
            { t: "Today 08:30", e: "Apixaban 5mg administered", d: "Standing order. Nursing." },
            { t: "Today 07:00", e: "Vitals: 138/82, HR 78 (sinus)", d: "Q4H rounding." },
            { t: "Yesterday", e: "ACC/AHA AF guideline reviewed", d: "Care plan attached." },
            { t: "2d ago", e: "Admit: paroxysmal AF, palpitations", d: "Triage in ED 4S." },
          ].map((x, i) => (
            <li key={i} className="mb-5">
              <span className="absolute -left-[7px] mt-1.5 h-3 w-3 rounded-full border-2 border-background bg-primary" />
              <p className="text-xs text-muted-foreground">{x.t}</p>
              <p className="text-sm font-medium">{x.e}</p>
              <p className="text-xs text-muted-foreground">{x.d}</p>
            </li>
          ))}
        </ol>
      </Card>
    </div>
  );
}
