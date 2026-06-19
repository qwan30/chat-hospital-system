import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { patients } from "@/data/patients";
import { useState } from "react";
import { StatusBadge } from "@/components/hms/StatusBadge";

export const Route = createFileRoute("/_app/chat/new")({
  head: () => ({ meta: [{ title: "New chat — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const [q, setQ] = useState("");
  const filtered = patients.filter(
    (p) =>
      p.name.toLowerCase().includes(q.toLowerCase()) ||
      p.mrn.toLowerCase().includes(q.toLowerCase()),
  );
  return (
    <AppShell>
      <PageHeader
        title="Start a new chat"
        description="Pick a patient context, or start a general clinical chat."
      />
      <Card className="p-4">
        <Input
          placeholder="Search patients by name or MRN…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </Card>
      <div className="mt-4 grid gap-2">
        {filtered.map((p) => (
          <Link
            key={p.id}
            to="/chat/patients/$patientId"
            params={{ patientId: p.id }}
            className="flex items-center justify-between rounded-md border bg-card p-3 hover:bg-muted"
          >
            <div>
              <p className="font-medium text-sm">{p.name}</p>
              <p className="text-xs text-muted-foreground">
                {p.unit} · {p.condition}
              </p>
            </div>
            <StatusBadge status={p.access} />
          </Link>
        ))}
      </div>
      <Card className="mt-4 p-4 text-sm">
        <Link to="/chat/general" className="text-primary underline">
          Or start a general clinical knowledge chat →
        </Link>
      </Card>
    </AppShell>
  );
}
