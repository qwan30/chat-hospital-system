import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { documents } from "@/data/documents";

export const Route = createFileRoute("/_app/documents/search")({
  head: () => ({ meta: [{ title: "Search documents — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const [q,setQ]=useState('apixaban renal');
  return (
    <AppShell>
      <PageHeader title="Document search" description="Hybrid keyword + vector search across the indexed corpus." />
      <Card className="p-3"><Input value={q} onChange={e=>setQ(e.target.value)} /></Card>
      <div className="mt-4 space-y-2">
        {documents.slice(0,6).map((d,i)=>(<Card key={d.id} className="p-4"><p className="text-sm font-semibold">{d.name}</p><p className="mt-1 text-xs text-muted-foreground">{d.category} · {d.pages}p · score {(0.92 - i*0.04).toFixed(2)}</p><p className="mt-2 text-sm">…CrCl 30–50 mL/min: reduce apixaban to 2.5 mg BID when co-administered with strong CYP3A4 inhibitors…</p></Card>))}
      </div>
    </AppShell>
  );
}
